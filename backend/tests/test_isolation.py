"""Day 7: trade memories stay with their residents, run and tick."""

from backend.app.memory import EventStore
from backend.tests.test_relationships import ACCEPT, offer, run

QUERY = "trade food coins accepted"


def trade_world(store):
    return run({(1, "ethan"): offer(give="food"), (2, "aishani"): ACCEPT, (3, "rylee"): ACCEPT}, store)


def ids(context):
    return {event.event_id for event in context.recent + context.relevant}


def test_bystanders_never_retrieve_a_trade_they_were_not_in(tmp_path):
    store = EventStore(tmp_path / "memory.sqlite")
    run_id = trade_world(store).snapshot().run_id
    for bystander in ("gayatri", "rylee", "saurya"):
        context = store.retrieve(run_id, bystander, QUERY, 3)
        assert all(event.agent_id == bystander for event in context.recent + context.relevant)
        assert all("trade t1:" not in event.text for event in context.recent + context.relevant)


def test_partner_memory_is_hidden_before_its_tick(tmp_path):
    store = EventStore(tmp_path / "memory.sqlite")
    run_id = trade_world(store).snapshot().run_id
    partner_id = f"{run_id}:2:aishani:partner"
    assert partner_id in ids(store.retrieve(run_id, "ethan", QUERY, 2))
    assert partner_id not in ids(store.retrieve(run_id, "ethan", QUERY, 1))


def test_new_run_cannot_retrieve_the_old_run(tmp_path):
    store = EventStore(tmp_path / "memory.sqlite")
    world = trade_world(store)
    old_run = world.snapshot().run_id
    new_run = world.reset(11).run_id
    assert new_run != old_run
    assert ids(store.retrieve(new_run, "ethan", QUERY, 99)) == set()
    assert world.snapshot().agents[0].relationships["aishani"] == 0
