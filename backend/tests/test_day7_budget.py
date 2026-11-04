import pytest
import httpx
from backend.app.groq_planner import GroqProvider

from backend.app.config import Settings
from backend.app.groq_planner import retry_seconds
from backend.app.llm_budget import Budget
from backend.tests.test_groq import Clock
from backend.app.groq_planner import LivePlanner, ProviderFailure, ProviderReply, resolve_proposal
from backend.app.world import World
from backend.app.schemas import StepRequest


def test_actual_twenty_call_run_cap_is_shared_across_workers(tmp_path):
    clock = Clock()
    cfg = Settings(_env_file=None, llm_max_calls_per_run=20)
    workers = [Budget(tmp_path/'budget.sqlite',cfg,clock) for _ in range(2)]
    try:
        timestamps = []
        for i in range(20):
            worker = workers[i%2]
            call, reason = worker.reserve('same-run',str(i%5),100)
            assert call and not reason
            assert workers[(i+1)%2].reserve('same-run','other',100)[0] is None
            worker.finish(call,25,'accepted')
            timestamps.append(clock.now)
            clock.advance(15)
        assert workers[0].reserve('same-run','ethan',100)[1] == 'Run request budget exhausted'
        assert workers[1].usage('same-run').calls_run == 20
        assert workers[1].usage('new-run').calls_day == 20
        assert workers[1].usage('new-run').tokens_day == 500
        assert all(sum(t-60 < s <= t for s in timestamps) <= 4 for t in timestamps)
    finally:
        for worker in workers: worker.close()


@pytest.mark.parametrize('value', [0,-1,True,1.5,float('nan')])
def test_invalid_reservations_cannot_reduce_the_budget(tmp_path,value):
    budget = Budget(tmp_path/'budget.sqlite',Settings(_env_file=None))
    try:
        with pytest.raises(ValueError): budget.reserve('run','ethan',value)
        assert budget.usage('run').calls_day == 0
    finally: budget.close()


@pytest.mark.parametrize('value', [float('nan'),float('inf'),-4,True])
def test_bad_measured_usage_retains_the_conservative_charge(tmp_path,value):
    budget = Budget(tmp_path/'budget.sqlite',Settings(_env_file=None))
    try:
        call,_ = budget.reserve('run','ethan',800)
        budget.finish(call,value,'invalid')
        assert budget.usage('run').reserved_tokens_day == 800
    finally: budget.close()


@pytest.mark.parametrize('value,expected', [('NaN',60),('Infinity',60),('17',17),('-4',1),(None,60)])
def test_retry_after_is_finite_and_bounded(value,expected):
    assert retry_seconds(value) == expected


def test_provider_recovers_without_resetting_usage_or_repeating_stale_plans(tmp_path):
    clock = Clock()
    cfg = Settings(_env_file=None, memory_db_path=str(tmp_path/'events.sqlite'), llm_api_key='fake-key')
    calls = []
    def provider(payload):
        calls.append(payload)
        if len(calls) == 1: raise ProviderFailure('Groq timed out')
        return ProviderReply({'action':'rest','target':None,'explanation':'Recover energy.'},10)
    planner = LivePlanner(cfg,provider=provider,clock=clock)
    world = World(live_planner=planner,mode='llm')
    try:
        for index in range(6):
            planner.kick(world)
            planner.future.result(timeout=3)
            if index == 0: assert world.snapshot().agent_runtime['ethan'].status == 'fallback'
            clock.advance(15)
        assert world.snapshot().agent_runtime['ethan'].status == 'live'
        assert world.snapshot().provider_usage.calls_run == 6
        assert world.snapshot().provider_usage.reserved_tokens_day > 50  # first unknown charge retained
    finally: planner.close()


def test_social_plan_executes_once_from_cache(tmp_path):
    clock = Clock()
    cfg = Settings(_env_file=None,memory_db_path=str(tmp_path/'events.sqlite'),llm_api_key='fake-key')
    planner = LivePlanner(cfg,provider=lambda _:ProviderReply(
        {'action':'offer_trade','target':'gayatri','explanation':'Exchange one food for a coin.'},30),clock=clock)
    world = World(live_planner=planner,mode='llm')
    world._state.agents[1].x, world._state.agents[1].y = 2,1
    try:
        planner.kick(world); planner.future.result(timeout=3)
        state=world.snapshot()
        state=world.step(StepRequest(run_id=state.run_id,expected_revision=state.revision,request_id='one'))
        assert state.decisions['ethan'].planner_mode == 'live'
        assert len(state.trade_offers) == 1
        state=world.step(StepRequest(run_id=state.run_id,expected_revision=state.revision,request_id='two'))
        assert len(state.trade_offers) == 1
        assert state.decisions['ethan'].action != 'offer_trade'
        assert state.provider_usage.calls_run == 1
    finally: planner.close()


def test_arriving_at_a_house_rests_instead_of_trying_to_gather():
    state=World().snapshot()
    agent=state.agents[0]
    agent.x,agent.y=2,9
    assert resolve_proposal({'action':'move','target':'house-west','explanation':'Rest at home.'},agent,state).action == 'rest'


def test_malformed_json_retains_measured_usage_and_uses_fallback(tmp_path,monkeypatch):
    original=httpx.Client
    transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
        'choices':[{'message':{'content':'{broken'}}],'usage':{'total_tokens':123}}))
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=transport,**kwargs))
    cfg=Settings(_env_file=None,memory_db_path=str(tmp_path/'events.sqlite'),llm_api_key='fake-key')
    planner=LivePlanner(cfg,provider=GroqProvider(cfg))
    world=World(live_planner=planner,mode='llm')
    try:
        planner.kick(world);planner.future.result(timeout=3)
        state=world.snapshot()
        state=world.step(StepRequest(run_id=state.run_id,expected_revision=0,request_id='x'))
        assert state.decisions['ethan'].planner_mode == 'fallback'
        assert state.provider_usage.calls_run == 1 and state.provider_usage.tokens_day == 123
    finally:planner.close()
