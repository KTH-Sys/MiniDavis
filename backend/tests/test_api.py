from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.schemas import Action, StepRequest
from backend.app.world import Conflict, World


@pytest.fixture
def client():
    with TestClient(create_app(Settings(_env_file=None))) as connection:
        yield connection


def payload(state, request_id="step-1"):
    return {"run_id": state["run_id"], "expected_revision": state["revision"], "request_id": request_id}


def test_step_and_reset_use_authoritative_state(client):
    first = client.get("/state").json()
    assert len(first["agents"]) == 5
    response = client.post("/step", json=payload(first))
    assert response.status_code == 200
    stepped = response.json()
    assert stepped["tick"] == stepped["revision"] == 1
    assert stepped["agents"][0]["x"] != first["agents"][0]["x"]
    assert len(stepped["events"]) == 5
    reset = client.post("/reset", json={"seed": 11, "mode": "baseline"}).json()
    assert reset["run_id"] != first["run_id"]
    assert reset["tick"] == reset["revision"] == 0
    assert reset["agents"] == first["agents"]
    assert reset["resources"] == first["resources"]
    assert reset["events"] == []


def test_duplicate_retry_does_not_step_twice_or_return_an_old_snapshot(client):
    first = client.get("/state").json()
    one = client.post("/step", json=payload(first)).json()
    two = client.post("/step", json=payload(one, "step-2")).json()
    retried = client.post("/step", json=payload(first))
    assert retried.status_code == 200
    assert retried.json() == two
    assert client.post("/step", json=payload(one)).status_code == 409


def test_stale_revision_and_reset_run_cannot_mutate_the_town(client):
    first = client.get("/state").json()
    client.post("/step", json=payload(first))
    assert client.post("/step", json=payload(first, "different-id")).status_code == 409
    reset = client.post("/reset", json={"seed": 22}).json()
    assert client.post("/step", json=payload(first)).status_code == 409
    assert client.get("/state").json() == reset


def test_competing_clients_only_advance_one_tick():
    world = World()
    state = world.snapshot()

    def attempt(request_id):
        try:
            world.step(StepRequest(run_id=state.run_id, expected_revision=0, request_id=request_id))
            return "accepted"
        except Conflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, ["window-a", "window-b"])) == ["accepted", "conflict"]
    assert world.snapshot().tick == 1


def test_baseline_runs_100_ticks_without_provider_or_model_weights(client):
    state = client.get("/state").json()
    for turn in range(100):
        response = client.post("/step", json=payload(state, f"turn-{turn}"))
        assert response.status_code == 200
        state = response.json()
        assert state["tick"] == turn + 1
        for resident in state["agents"]:
            assert 0 <= resident["x"] < 12 and 0 <= resident["y"] < 12
            assert 0 <= resident["energy"] <= 100
            assert min(resident[k] for k in ["food", "wood", "coins"]) >= 0
        assert all(resource["stock"] >= 0 for resource in state["resources"])
    assert len(state["events"]) == 200
    assert sum(agent["wood"] for agent in state["agents"]) + state["resources"][1]["stock"] == 40


def test_invalid_baseline_proposal_is_rejected_without_inventory_changes():
    world = World(planner=lambda agent, state: Action(action="move", x=12, y=agent.y))
    before = world.snapshot()
    after = world.step(StepRequest(run_id=before.run_id, expected_revision=0, request_id="bad-move"))
    assert before.agents == after.agents
    assert before.resources == after.resources
    assert all(event.outcome == "rejected" for event in after.events)


def test_snapshots_do_not_expose_mutable_world_objects():
    world = World()
    snapshot = world.snapshot()
    snapshot.agents[0].coins = -100
    assert world.snapshot().agents[0].coins == 10


def test_credentials_are_server_only_and_future_modes_fail_clearly():
    settings = Settings(_env_file=None, llm_api_key="test-only-secret-value")
    with TestClient(create_app(settings)) as connection:
        health = connection.get("/health")
        assert health.json() == {"status": "ok", "mode": "baseline", "live_llm_enabled": False}
        for path in ["/health", "/state", "/openapi.json"]:
            assert "test-only-secret-value" not in connection.get(path).text
        assert connection.post("/reset", json={"seed": 11, "mode": "llm"}).status_code == 422
        assert connection.post("/reset", json={"seed": -1}).status_code == 422
        assert connection.post("/step", json={}).status_code == 422


def test_frontend_origins_are_explicit(client):
    allowed = client.options("/step", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied = client.get("/state", headers={"Origin": "https://unrelated.example"})
    assert "access-control-allow-origin" not in denied.headers
