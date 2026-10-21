from backend.app.memory import EventStore
from backend.app.schemas import Event


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
