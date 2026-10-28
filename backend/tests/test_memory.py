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


def test_recent_returns_last_five_real_events_for_one_resident_and_run(tmp_path):
    store = EventStore(tmp_path / "memory.sqlite")
    world = World(store=store)
    run_id = world.snapshot().run_id
    for tick in range(7):
        world.step(StepRequest(run_id=run_id, expected_revision=tick, request_id=f"step-{tick}"))
    store.save(Event(event_id="old:1:ethan", run_id="old", tick=99, agent_id="ethan",
                     action="rest", outcome="accepted", text="Old run."))

    recent = store.recent(run_id, "ethan")

    assert [event.tick for event in recent] == [3, 4, 5, 6, 7]  # oldest first, reads like a story
    assert all(event.agent_id == "ethan" and event.run_id == run_id for event in recent)
    assert all(store.get(event.event_id) == event for event in recent)  # every ID really exists


def word_embedder(calls):
    """Fake MiniLM: 'lumber' and 'wood' share a meaning, so lexical search alone misses it."""
    def embed(texts):
        calls.extend(texts)
        return [[float("wood" in t.lower() or "lumber" in t.lower()),
                 float("food" in t.lower() or "meal" in t.lower())] for t in texts]
    return embed


def save_town(store):
    store.save_many([
        Event(event_id="e1", run_id="r", tick=1, agent_id="ethan", action="gather", outcome="accepted", text="Ethan gathered wood."),
        Event(event_id="e2", run_id="r", tick=2, agent_id="ethan", action="eat", outcome="accepted", text="Ethan ate food."),
        Event(event_id="other", run_id="r", tick=1, agent_id="eric", action="gather", outcome="accepted", text="Eric gathered wood."),
        Event(event_id="old", run_id="old", tick=1, agent_id="ethan", action="gather", outcome="accepted", text="Ethan gathered wood."),
        Event(event_id="future", run_id="r", tick=9, agent_id="ethan", action="gather", outcome="accepted", text="Ethan gathered wood."),
    ])


def test_semantic_retrieval_finds_meaning_not_just_words(tmp_path):
    store = EventStore(tmp_path / "m.sqlite", embedder=word_embedder([]))
    save_town(store)
    memory = store.retrieve("r", "ethan", "lumber", as_of_tick=2)
    assert memory.mode == "semantic"
    assert [e.event_id for e in memory.relevant][0] == "e1"
    assert {e.event_id for e in memory.relevant + memory.recent} <= {"e1", "e2"}


def test_event_embeddings_are_cached(tmp_path):
    calls = []
    store = EventStore(tmp_path / "m.sqlite", embedder=word_embedder(calls))
    save_town(store)
    store.retrieve("r", "ethan", "lumber", as_of_tick=2)
    calls.clear()
    store.retrieve("r", "ethan", "meal", as_of_tick=2)
    assert calls == ["meal"]


def test_broken_embedder_falls_back_to_keyword_search(tmp_path):
    def broken(texts):
        raise RuntimeError("model failed to load")
    store = EventStore(tmp_path / "m.sqlite", embedder=broken)
    save_town(store)
    memory = store.retrieve("r", "ethan", "wood", as_of_tick=2)
    assert memory.mode == "lexical"
    assert [e.event_id for e in memory.relevant] == ["e1"]
