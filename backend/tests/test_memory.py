from backend.app.memory import EventStore
from backend.app.schemas import Action, Event, StepRequest
from backend.app.world import World


def sample_event():
    return Event(
        event_id="evt-1", run_id="run-1", tick=1, agent_id="ethan",
        action="gather", outcome="accepted", text="Ethan gathered 1 wood at the forest.",
    )


def test_saved_event_survives_reopening_the_store(tmp_path):
    path = tmp_path / "memory.sqlite"
    EventStore(path).save(sample_event())
    assert EventStore(path).get("evt-1") == sample_event()


def test_missing_event_returns_none(tmp_path):
    assert EventStore(tmp_path / "memory.sqlite").get("nope") is None


def test_world_saves_every_event_with_its_outcome(tmp_path):
    # Gayatri gathers on the farm (accepted); everyone else walks off the map (rejected).
    def planner(agent, state):
        return Action(action="gather") if agent.id == "gayatri" else Action(action="move", x=12, y=agent.y)

    store = EventStore(tmp_path / "memory.sqlite")
    world = World(planner=planner, store=store)
    world._state.agents[1].x = 9  # move Gayatri onto the farm at (9, 3)
    run_id = world.snapshot().run_id
    world.step(StepRequest(run_id=run_id, expected_revision=0, request_id="step-1"))

    reopened = EventStore(tmp_path / "memory.sqlite")
    gather = reopened.get(f"{run_id}:1:gayatri")
    bad_move = reopened.get(f"{run_id}:1:ethan")
    assert (gather.action, gather.outcome) == ("gather", "accepted")
    assert (bad_move.action, bad_move.outcome) == ("move", "rejected")
    assert all(reopened.get(f"{run_id}:1:{agent}") for agent in ["aishani", "rylee", "saurya"])
