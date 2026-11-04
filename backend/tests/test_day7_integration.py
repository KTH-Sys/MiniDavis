import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.memory import EventStore
from backend.app.schemas import Action, ReplayRequest, StepRequest
from backend.app.world import Conflict, World


def request(world, name='step', **extra):
    state = world.snapshot()
    return dict(run_id=state.run_id, expected_revision=state.revision, request_id=name, **extra)


def demo_world(store=None, classifier=None):
    """Legal scripted fixture: walk from the real start, trade, then speak."""
    def plan(agent, state, memory):
        if agent.id == 'ethan':
            neighbor = next(a for a in state.agents if a.id == 'saurya')
            if abs(agent.x-neighbor.x)+abs(agent.y-neighbor.y) > 1:
                if agent.x != neighbor.x:
                    return Action(action='move', x=agent.x + 1, y=agent.y)
                return Action(action='move', x=agent.x, y=agent.y + 1)
            if not state.trade_offers:
                return Action(action='offer_trade', offer_id='fixture-trade', recipient_id='saurya',
                              give_resource='food', give_amount=1, receive_resource='coins', receive_amount=1)
            if state.tick == 9:
                return Action(action='talk', recipient_id='saurya', message='Thank you for the exchange.')
        if agent.id == 'saurya' and state.trade_offers and state.trade_offers[0].status == 'pending':
            return Action(action='accept_trade', offer_id='fixture-trade')
        return Action(action='rest')
    return World(store=store, classifier=classifier, context_planner=plan)


def run_fixture(world):
    for index in range(10):
        if index == 4:
            world.shortage(StepRequest(**request(world, 'shortage')))
        world.step(StepRequest(**request(world, str(index))))
    return world.snapshot()


def test_shortage_is_idempotent_nonincreasing_and_recorded(tmp_path):
    store = EventStore(tmp_path / 'events.sqlite')
    world = World(store=store)
    req = StepRequest(**request(world))
    result = world.shortage(req)
    assert result.resources[0].stock == 5
    assert world.shortage(req) == result
    assert store.get(result.events[-1].event_id).action == 'shortage'
    with pytest.raises(Conflict):
        world.step(req)  # a request ID cannot change mutation kind
    world._state.resources[0].stock = 2
    assert world.shortage(StepRequest(**request(world, 'second'))).resources[0].stock == 2
    store.close()


def test_shortage_storage_failure_rolls_back(tmp_path, monkeypatch):
    store = EventStore(tmp_path / 'events.sqlite')
    world = World(store=store)
    before = world.snapshot()
    def fail(event): raise sqlite3.OperationalError('disk full')
    monkeypatch.setattr(store, 'save', fail)
    with pytest.raises(sqlite3.OperationalError):
        world.shortage(StepRequest(**request(world)))
    assert world.snapshot() == before
    assert world.trace().operations == []
    store.close()


def test_trace_replays_actions_trades_relationships_and_shortage_without_models(tmp_path):
    original = demo_world()
    before = run_fixture(original)
    assert before.trade_offers[0].status == 'accepted'
    assert before.agents[0].relationships['saurya'] == 2
    destination = World(store=EventStore(tmp_path / 'replayed.sqlite'))
    req = ReplayRequest(**request(destination, trace=original.trace()))
    replayed = destination.replay(req)
    assert replayed.run_id != before.run_id
    assert replayed.mode == 'replay'
    assert replayed.agents == before.agents
    assert replayed.resources == before.resources
    assert replayed.trade_offers == before.trade_offers
    assert all(d.planner_mode == 'replay' for d in replayed.decisions.values())
    assert all(r.status == 'replay' for r in replayed.agent_runtime.values())
    assert destination.replay(req) == replayed
    with pytest.raises(Conflict, match='Reset'):
        destination.step(StepRequest(**request(destination, 'advance')))
    fresh = destination.reset(11)
    assert fresh.mode == 'baseline' and fresh.trade_offers == []
    assert destination.trace().operations == []


def test_tampered_trace_does_not_mutate_current_run():
    original = demo_world()
    run_fixture(original)
    trace = original.trace()
    trace.operations[0].actions[0].action.x = 99
    target = World()
    before = target.snapshot()
    with pytest.raises(Conflict):
        target.replay(ReplayRequest(**request(target, trace=trace)))
    assert target.snapshot() == before


def test_listener_remembers_actual_speech_but_bystanders_do_not(tmp_path):
    store=EventStore(tmp_path/'events.sqlite')
    world=demo_world(store=store)
    state=run_fixture(world)
    heard=store.recent(state.run_id,'saurya',limit=50)
    assert any(e.action=='talk' and 'Thank you for the exchange.' in e.text for e in heard)
    private=store.recent(state.run_id,'gayatri',limit=50)
    assert all('Thank you for the exchange.' not in e.text for e in private)
    store.close()


def test_trade_requires_proximity_at_offer_and_acceptance():
    world = World()
    a, b = world._state.agents[0], world._state.agents[2]
    offer = Action(action='offer_trade', offer_id='x', recipient_id=b.id,
                   give_resource='food', give_amount=1, receive_resource='coins', receive_amount=1)
    assert world._execute(a, offer)[0] == 'rejected'
    b.x, b.y = a.x + 1, a.y
    assert world._execute(a, offer)[0] == 'accepted'
    b.x = 10
    amounts = [(r.food, r.coins) for r in world._state.agents]
    assert world._execute(b, Action(action='accept_trade', offer_id='x'))[0] == 'rejected'
    assert amounts == [(r.food, r.coins) for r in world._state.agents]


def test_expired_and_rejected_offers_never_transfer():
    world = World(planner=lambda a, s: Action(action='rest'))
    a, b = world._state.agents[0], world._state.agents[2]
    b.x, b.y = a.x + 1, a.y
    def offer(name):
        return Action(action='offer_trade', offer_id=name, recipient_id=b.id,
                      give_resource='food', give_amount=1, receive_resource='coins', receive_amount=1)
    assert world._execute(a, offer('declined'))[0] == 'accepted'
    assert world._execute(b, Action(action='reject_trade', offer_id='declined'))[0] == 'accepted'
    assert world._execute(b, Action(action='accept_trade', offer_id='declined'))[0] == 'rejected'
    assert world._execute(a, offer('expired'))[0] == 'accepted'
    amounts = [(r.food, r.coins) for r in world._state.agents]
    for i in range(5): world.step(StepRequest(**request(world, str(i))))
    assert world.snapshot().trade_offers[-1].status == 'expired'
    assert world._execute(b, Action(action='accept_trade', offer_id='expired'))[0] == 'rejected'
    assert amounts == [(r.food, r.coins) for r in world._state.agents]


@pytest.mark.parametrize('fail', [False, True])
def test_classifier_labels_executed_events_without_controlling_transfers(tmp_path, fail):
    class Classifier:
        def predict(self, text):
            if fail: raise RuntimeError('model unavailable')
            return {'label': 'trade', 'confidence': .9}
    store = EventStore(tmp_path / 'old.sqlite')
    world = demo_world(store=store, classifier=Classifier())
    state = run_fixture(world)
    completed = [e for e in state.events if e.action in {'accept_trade','trade_completed'}]
    assert len(completed) == 2
    assert completed[0].interaction_id == completed[1].interaction_id
    assert all(e.interaction_label == (None if fail else 'trade') for e in completed)
    assert state.agents[0].food == 2 and state.agents[4].food == 4
    assert all(store.get(e.event_id) == e for e in completed)
    store.close()


def test_operator_key_guards_every_mutation_but_not_viewing(tmp_path):
    cfg = Settings(_env_file=None, memory_db_path=str(tmp_path/'api.sqlite'),
                   operator_token='test-operator', require_operator_token=True)
    with TestClient(create_app(cfg)) as client:
        for path in ['/health','/ready','/state','/trace','/agents/ethan']:
            assert client.get(path).status_code == 200
        state = client.get('/state').json()
        payload = {'run_id': state['run_id'], 'expected_revision': 0, 'request_id': 'x'}
        trace = client.get('/trace').json()
        for path, body in [('/step',payload),('/reset',{'seed':11}),('/scenario/shortage',payload),('/replay',{**payload,'trace':trace})]:
            assert client.post(path,json=body).status_code == 401
        assert client.post('/step',json=payload,headers={'X-Operator-Token':'test-operator'}).status_code == 200
        assert client.get('/state').json()['tick'] == 1


def test_public_preview_cannot_start_without_operator_key(tmp_path):
    with pytest.raises(ValueError, match='operator token'):
        create_app(Settings(_env_file=None, require_operator_token=True, operator_token='',
                            memory_db_path=str(tmp_path/'api.sqlite')))


def test_invalid_optional_classifier_does_not_break_baseline(tmp_path):
    folder = tmp_path/'classifier'; folder.mkdir()
    cfg = Settings(_env_file=None, memory_db_path=str(tmp_path/'api.sqlite'), classifier_model_path=str(folder))
    with TestClient(create_app(cfg)) as client:
        assert client.get('/ready').json()['classifier'] == 'unavailable'
        state = client.get('/state').json()
        assert client.post('/step',json={'run_id':state['run_id'],'expected_revision':0,'request_id':'x'}).status_code == 200
