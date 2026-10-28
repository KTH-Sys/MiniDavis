from backend.app.schemas import Action
from backend.app.world import World


def test_trade_offer_does_not_transfer_resources():
    world = World()
    state = world._state

    ethan = next(a for a in state.agents if a.id == "ethan")
    aishani = next(a for a in state.agents if a.id == "aishani")

    ethan.wood = 5
    aishani.food = 5

    before = (ethan.wood, ethan.food, aishani.wood, aishani.food)

    outcome, message = world._execute(
        ethan,
        Action(
            action="offer_trade",
            offer_id="trade-001",
            recipient_id="aishani",
            give_resource="wood",
            give_amount=2,
            receive_resource="food",
            receive_amount=1,
        ),
    )

    after = (ethan.wood, ethan.food, aishani.wood, aishani.food)

    assert outcome == "accepted"
    assert before == after
    assert len(state.trade_offers) == 1
    assert state.trade_offers[0].status == "pending"

def test_trade_acceptance_transfers_resources_only_once():
    world = World()
    state = world._state

    ethan = next(a for a in state.agents if a.id == "ethan")
    aishani = next(a for a in state.agents if a.id == "aishani")

    ethan.wood = 5
    aishani.food = 5

    # Ethan offers 2 wood for 1 food.
    outcome, _ = world._execute(
        ethan,
        Action(
            action="offer_trade",
            offer_id="trade-002",
            recipient_id="aishani",
            give_resource="wood",
            give_amount=2,
            receive_resource="food",
            receive_amount=1,
        ),
    )

    assert outcome == "accepted"

    # Aishani accepts the offer.
    outcome, _ = world._execute(
        aishani,
        Action(action="accept_trade", offer_id="trade-002"),
    )

    assert outcome == "accepted"
    assert ethan.wood == 3
    assert ethan.food == 4
    assert aishani.wood == 2
    assert aishani.food == 4
    assert state.trade_offers[0].status == "accepted"

    # Save balances after the completed trade.
    balances = (ethan.wood, ethan.food, aishani.wood, aishani.food)

    # Try accepting the same offer again.
    outcome, _ = world._execute(
        aishani,
        Action(action="accept_trade", offer_id="trade-002"),
    )

    assert outcome == "rejected"
    assert (ethan.wood, ethan.food, aishani.wood, aishani.food) == balances

def test_trade_rejected_if_resources_are_spent():
    world = World()
    state = world._state

    ethan = next(a for a in state.agents if a.id == "ethan")
    aishani = next(a for a in state.agents if a.id == "aishani")

    ethan.wood = 5
    aishani.food = 5

    outcome, _ = world._execute(
        ethan,
        Action(
            action="offer_trade",
            offer_id="trade-003",
            recipient_id="aishani",
            give_resource="wood",
            give_amount=2,
            receive_resource="food",
            receive_amount=1,
        ),
    )

    assert outcome == "accepted"

    # Ethan spends his wood before acceptance.
    ethan.wood = 0

    balances = (ethan.wood, ethan.food, aishani.wood, aishani.food)

    outcome, _ = world._execute(
        aishani,
        Action(action="accept_trade", offer_id="trade-003"),
    )

    assert outcome == "rejected"
    assert (ethan.wood, ethan.food, aishani.wood, aishani.food) == balances
    assert state.trade_offers[0].status == "pending"

def test_wrong_resident_cannot_accept_trade():
    world = World()
    state = world._state

    ethan = next(a for a in state.agents if a.id == "ethan")
    aishani = next(a for a in state.agents if a.id == "aishani")
    rylee = next(a for a in state.agents if a.id == "rylee")

    ethan.wood = 5
    aishani.food = 5

    outcome, _ = world._execute(
        ethan,
        Action(
            action="offer_trade",
            offer_id="trade-004",
            recipient_id="aishani",
            give_resource="wood",
            give_amount=2,
            receive_resource="food",
            receive_amount=1,
        ),
    )
    assert outcome == "accepted"

    before = [
        (a.food, a.wood, a.coins)
        for a in state.agents
    ]

    # Rylee tries accepting Aishani's offer.
    outcome, _ = world._execute(
        rylee,
        Action(action="accept_trade", offer_id="trade-004"),
    )

    assert outcome == "rejected"
    assert before == [
        (a.food, a.wood, a.coins)
        for a in state.agents
    ]
    assert state.trade_offers[0].status == "pending"

def test_duplicate_trade_offer_id_is_rejected():
    world = World()
    state = world._state

    ethan = next(a for a in state.agents if a.id == "ethan")
    aishani = next(a for a in state.agents if a.id == "aishani")

    ethan.wood = 5
    aishani.food = 5

    offer = Action(
        action="offer_trade",
        offer_id="trade-005",
        recipient_id="aishani",
        give_resource="wood",
        give_amount=2,
        receive_resource="food",
        receive_amount=1,
    )

    first_outcome, _ = world._execute(ethan, offer)
    assert first_outcome == "accepted"

    balances = [
        (a.food, a.wood, a.coins)
        for a in state.agents
    ]

    second_outcome, _ = world._execute(ethan, offer)

    assert second_outcome == "rejected"
    assert len(state.trade_offers) == 1
    assert state.trade_offers[0].status == "pending"
    assert balances == [
        (a.food, a.wood, a.coins)
        for a in state.agents
    ]

