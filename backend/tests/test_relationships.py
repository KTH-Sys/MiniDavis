"""Day 6: relationships and memories change only from executed interactions."""

from backend.app.agents import PlannedStep
from backend.app.memory import EventStore
from backend.app.schemas import Action, MemoryContext, StepRequest
from backend.app.world import World

REST = Action(action="rest")


def offer(give="wood", give_amount=2, receive="food", receive_amount=1):
    return Action(action="offer_trade", offer_id="t1", recipient_id="aishani", give_resource=give,
                  give_amount=give_amount, receive_resource=receive, receive_amount=receive_amount)


ACCEPT = Action(action="accept_trade", offer_id="t1")


def run(script, store=None):
    """script maps (tick, agent_id) to an action; everyone else rests."""
    def planner(agent, state):
        return script.get((state.tick, agent.id), REST)

    world = World(planner=planner, store=store)
    world._state.agents[2].x, world._state.agents[2].y = 2, 1
    for number in range(max(tick for tick, _ in script)):
        state = world.snapshot()
        world.step(StepRequest(run_id=state.run_id, expected_revision=state.revision, request_id=f"r{number}"))
    return world


def agent(world, agent_id):
    return next(item for item in world.snapshot().agents if item.id == agent_id)


def test_accepted_trade_adds_two_in_both_directions():
    script = {(1, "ethan"): offer(give="food"), (2, "aishani"): ACCEPT}
    world = run(script)
    assert agent(world, "ethan").relationships["aishani"] == 2
    assert agent(world, "aishani").relationships["ethan"] == 2
    assert agent(world, "ethan").relationships["rylee"] == 0


def test_accepted_gift_adds_five_recipient_to_giver_only():
    script = {(1, "ethan"): offer(give="coins", give_amount=3, receive="food", receive_amount=0),
              (2, "aishani"): ACCEPT}
    world = run(script)
    assert agent(world, "aishani").relationships["ethan"] == 5
    assert agent(world, "ethan").relationships["aishani"] == 0
    assert agent(world, "ethan").coins == 7
    assert agent(world, "aishani").coins == 18


def test_relationship_stays_within_bounds():
    world = World()
    ethan, aishani = world._state.agents[0], world._state.agents[2]
    aishani.x, aishani.y = ethan.x + 1, ethan.y
    ethan.relationships["aishani"] = 99
    aishani.relationships["ethan"] = 100
    world._execute(ethan, offer(give="food"))
    assert world._execute(aishani, ACCEPT)[0] == "accepted"
    assert ethan.relationships["aishani"] == 100
    assert aishani.relationships["ethan"] == 100


def test_offer_and_rejected_accept_change_no_relationship_or_memory(tmp_path):
    store = EventStore(tmp_path / "memory.sqlite")
    script = {(1, "ethan"): offer(give="food"), (2, "rylee"): ACCEPT}  # Rylee is not the recipient.
    world = run(script, store)
    assert agent(world, "ethan").relationships["aishani"] == 0
    assert agent(world, "rylee").relationships["ethan"] == 0
    run_id = world.snapshot().run_id
    assert all(event.action != "trade_completed" for event in store.recent(run_id, "ethan", limit=50))


def test_both_sides_remember_the_trade_with_its_real_amounts(tmp_path):
    store = EventStore(tmp_path / "memory.sqlite")
    script = {(1, "ethan"): offer(give="food", give_amount=2, receive="coins", receive_amount=4),
              (2, "aishani"): ACCEPT}
    world = run(script, store)
    run_id = world.snapshot().run_id

    ethan_events = store.recent(run_id, "ethan", limit=50)
    partner_event = next(event for event in ethan_events if event.action == "trade_completed")
    assert partner_event.tick == 2 and partner_event.outcome == "accepted"
    # Ethan's own action on the same tick must not be overwritten.
    assert store.get(f"{run_id}:2:ethan").action == "rest"

    aishani_event = store.get(f"{run_id}:2:aishani")
    for text in (partner_event.text, aishani_event.text):
        assert "2 food" in text and "4 coins" in text


def test_model_claims_never_become_memories_or_relationships(tmp_path):
    claim = "I gave Rylee 100 coins and we are best friends."
    empty = MemoryContext(mode="recent-only", query="", as_of_tick=0)

    def lying_planner(agent, state, memory):
        return PlannedStep(action=REST, mode="live", memory=empty, model_explanation=claim)

    store = EventStore(tmp_path / "memory.sqlite")
    world = World(context_planner=lying_planner, planner=lambda agent, state: REST, store=store)
    state = world.snapshot()
    world.step(StepRequest(run_id=state.run_id, expected_revision=state.revision, request_id="r1"))

    assert world.snapshot().decisions["ethan"].model_explanation == claim
    assert all(claim not in event.text for event in store.recent(state.run_id, "ethan", limit=50))
    assert agent(world, "ethan").relationships["rylee"] == 0
    assert agent(world, "ethan").coins == 10
