import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.agents import baseline_plan
from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.memory import EventStore
from backend.app.schemas import Action, Event, StepRequest
from backend.app.world import World


def step(world, name):
    state = world.snapshot()
    return world.step(StepRequest(run_id=state.run_id, expected_revision=state.revision, request_id=name))


def test_sql_scope_excludes_other_residents_old_runs_and_future_before_ranking(tmp_path):
    store = EventStore(tmp_path / "scope.sqlite")
    for event_id, run, agent, tick in [
        ("visible", "current", "ethan", 1), ("private", "current", "gayatri", 2),
        ("old", "old", "ethan", 3), ("future", "current", "ethan", 99),
    ]:
        store.save(Event(event_id=event_id, run_id=run, agent_id=agent, tick=tick,
                         action="gather", outcome="accepted", text="Forest wood."))
    result = store.retrieve("current", "ethan", "forest wood", as_of_tick=3)
    assert [event.event_id for event in result.recent] == ["visible"]
    assert [event.event_id for event in result.relevant] == ["visible"]
    assert store.retrieve("current", "saurya", "forest", 3).recent == []
    store.close()


def test_ten_frozen_keyword_retrieval_examples(tmp_path):
    fixtures = json.loads((Path(__file__).parents[2] / "ml/data/retrieval_examples.json").read_text())
    assert len(fixtures) == 10
    store = EventStore(tmp_path / "queries.sqlite")
    for tick, row in enumerate(fixtures, 1):
        store.save(Event(event_id=f"fixture:{tick}:ethan", run_id="fixture", agent_id="ethan",
                         tick=tick, action=row["action"], outcome=row["outcome"], text=row["text"]))
    hits = sum(f"fixture:{tick}:ethan" in [event.event_id for event in
               store.retrieve("fixture", "ethan", row["query"], 10).relevant]
               for tick, row in enumerate(fixtures, 1))
    assert hits == 10
    store.close()


def test_planner_and_inspector_receive_identical_stored_evidence(tmp_path):
    seen = {}
    store = EventStore(tmp_path / "pipeline.sqlite")

    def planner(agent, state, memory):
        assert all(event.agent_id == agent.id for event in state.events)
        assert set(state.decisions).issubset({agent.id})
        seen[agent.id] = memory.model_copy(deep=True)
        # The planner only gets copies: tampering must not affect recorded evidence.
        if memory.recent:
            memory.recent[0].text = "invented by planner"
        return baseline_plan(agent, state)

    world = World(store=store, context_planner=planner)
    step(world, "first")
    state = step(world, "second")
    for agent in state.agents:
        inspector = world.inspect(agent.id, state.run_id, state.revision)
        assert inspector.retrieval == seen[agent.id]
        assert inspector.decision.memory == state.decisions[agent.id].memory
        assert inspector.retrieval.recent
        assert all(event.tick < inspector.decision.tick for event in inspector.retrieval.recent)
        for event in inspector.retrieval.recent + inspector.retrieval.relevant:
            assert event.agent_id == agent.id and event.run_id == state.run_id
            assert store.get(event.event_id) == event
    world.reset(11)
    for agent in state.agents:
        inspector = world.inspect(agent.id)
        assert inspector.decision is None
        assert inspector.retrieval.recent == inspector.retrieval.relevant == []
    store.close()


def test_inspector_http_contract_and_stale_run(tmp_path):
    app = create_app(Settings(_env_file=None, memory_db_path=str(tmp_path / "api.sqlite")))
    with TestClient(app) as client:
        state = client.get("/state").json()
        for index in range(3):
            state = client.post("/step", json={"run_id": state["run_id"],
                "expected_revision": state["revision"], "request_id": str(index)}).json()
        for agent in state["agents"]:
            response = client.get(f"/agents/{agent['id']}", params={"run_id": state["run_id"], "revision": state["revision"]})
            assert response.status_code == 200
            body = response.json()
            assert body["agent"] == agent
            assert body["decision"] == state["decisions"][agent["id"]]
            assert body["retrieval"] == body["decision"]["memory"]
        assert client.get("/agents/unknown").status_code == 404
        assert client.get("/agents/ethan", params={"revision": 0}).status_code == 409
        client.post("/reset", json={"seed": 11})
        assert client.get("/agents/ethan", params={"run_id": state["run_id"]}).status_code == 409
        assert client.get("/agents/ethan").json()["retrieval"]["recent"] == []


@pytest.mark.parametrize("failure", ["planner", "storage"])
def test_failed_tick_rolls_back_world_and_durable_events(tmp_path, monkeypatch, failure):
    store = EventStore(tmp_path / "atomic.sqlite")

    def planner(agent, state):
        if failure == "planner" and agent.id == "aishani":
            raise RuntimeError("planner failed")
        return Action(action="rest")

    world = World(store=store, planner=planner)
    before = world.snapshot()
    if failure == "storage":
        def fail_save(events):
            raise sqlite3.OperationalError("storage failed")
        monkeypatch.setattr(store, "save_many", fail_save)
    with pytest.raises((RuntimeError, sqlite3.OperationalError)):
        step(world, "failed")
    assert world.snapshot() == before
    assert store.recent(before.run_id, "ethan") == []
    store.close()
