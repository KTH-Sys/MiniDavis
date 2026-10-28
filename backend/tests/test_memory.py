from backend.app.memory import EventStore
from backend.app.schemas import Action, Event, StepRequest
from backend.app.world import World
import pytest


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


def test_only_visible_events_are_ever_sent_to_embedder(tmp_path):
    calls = []
    store = EventStore(tmp_path / 'scope.sqlite', embedder=word_embedder(calls))
    save_town(store)
    result = store.retrieve('r', 'ethan', 'lumber', 2)
    assert result.mode == 'semantic'
    assert calls == ['Ethan gathered wood.', 'Ethan ate food.', 'lumber']
    store.close()


def test_changed_event_text_invalidates_its_embedding(tmp_path):
    calls = []
    store = EventStore(tmp_path / 'edited.sqlite', embedder=word_embedder(calls))
    save_town(store)
    store.retrieve('r', 'ethan', 'lumber', 2)
    event = store.get('e1').model_copy(update={'text': 'Ethan collected food.'})
    store.save(event)
    calls.clear()
    store.retrieve('r', 'ethan', 'meal', 2)
    assert calls == ['Ethan collected food.', 'meal']
    store.close()


def test_embedding_cache_survives_restart_but_not_model_change(tmp_path):
    path = tmp_path / 'restart.sqlite'
    calls = []
    first = EventStore(path, embedder=word_embedder(calls), embedding_key='model-v1')
    save_town(first)
    first.retrieve('r', 'ethan', 'wood', 2)
    first.close()
    calls.clear()
    same = EventStore(path, embedder=word_embedder(calls), embedding_key='model-v1')
    same.retrieve('r', 'ethan', 'meal', 2)
    assert calls == ['meal']
    same.close()
    calls.clear()
    changed = EventStore(path, embedder=word_embedder(calls), embedding_key='model-v2')
    changed.retrieve('r', 'ethan', 'meal', 2)
    assert calls == ['Ethan gathered wood.', 'Ethan ate food.', 'meal']
    changed.close()


@pytest.mark.parametrize('bad', [[], [[float('nan')]], [[1.0], [1.0]], [['invalid']]])
def test_invalid_embedding_batch_is_labelled_keyword_fallback(tmp_path, bad):
    store = EventStore(tmp_path / 'bad.sqlite', embedder=lambda texts: bad)
    save_town(store)
    result = store.retrieve('r', 'ethan', 'wood', 2)
    assert result.mode == 'lexical'
    assert [event.event_id for event in result.relevant] == ['e1']
    store.close()


def test_dimension_mismatch_does_not_rank_truncated_vectors(tmp_path):
    def inconsistent(texts):
        return [[1.0, 0.0] for _ in texts] if len(texts) > 1 else [[1.0]]
    store = EventStore(tmp_path / 'dimension.sqlite', embedder=inconsistent)
    save_town(store)
    assert store.retrieve('r', 'ethan', 'wood', 2).mode == 'lexical'
    store.close()


def test_old_event_only_cache_is_not_reused(tmp_path):
    store = EventStore(tmp_path / 'old-cache.sqlite', embedder=word_embedder([]))
    save_town(store)
    store.db.execute('CREATE TABLE embeddings(event_id TEXT PRIMARY KEY, vector TEXT)')
    store.db.execute("INSERT INTO embeddings VALUES ('e1', '[0.0,1.0]')")
    assert store.retrieve('r', 'ethan', 'lumber', 2).relevant[0].event_id == 'e1'
    store.close()
