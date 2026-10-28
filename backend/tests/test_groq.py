import json
import threading
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.groq_planner import (GroqProvider, LivePlanner, ProviderFailure, ProviderReply,
                                      build_input, resolve_proposal)
from backend.app.llm_budget import Budget
from backend.app.main import create_app
from backend.app.memory import EventStore
from backend.app.schemas import Event, MemoryContext, StepRequest
from backend.app.world import World


class Clock:
    def __init__(self): self.now = 1800000000.0
    def __call__(self): return self.now
    def advance(self, seconds=15): self.now += seconds


def settings(tmp_path, **kwargs):
    return Settings(_env_file=None, memory_db_path=str(tmp_path/'events.sqlite'),
                    llm_api_key='fake-test-key', **kwargs)


def step(world, request='step'):
    s=world.snapshot()
    return world.step(StepRequest(run_id=s.run_id, expected_revision=s.revision, request_id=request))


def wait(planner):
    if planner.future:
        planner.future.result(timeout=3)


def rest(_): return ProviderReply({'action':'rest','target':None,'explanation':'Recover energy.'}, 35)


def test_prompt_is_scoped_bounded_and_contains_real_sources(tmp_path):
    state=World().snapshot()
    agent=state.agents[0]
    events=[Event(event_id=f'{state.run_id}:{i}:ethan',run_id=state.run_id,tick=i,agent_id='ethan',
                  action='gather',outcome='accepted',text='Ethan gathered wood.') for i in range(1,7)]
    hidden=events[0].model_copy(update={'agent_id':'gayatri','event_id':'private'})
    future=events[0].model_copy(update={'tick':99,'event_id':'future'})
    memory=MemoryContext(query='wood',as_of_tick=6,recent=events+[hidden,future],relevant=events)
    payload, used, reserved=build_input(agent,state,memory,settings(tmp_path))
    content=payload['messages'][1]['content']
    assert 'private' not in content and 'future' not in content
    assert used.recent and all(e.event_id in content for e in used.recent+used.relevant)
    assert len(''.join(m['content'] for m in payload['messages']).encode()) <= 800
    assert payload['response_format']['json_schema']['strict'] is True
    assert payload['reasoning_effort']=='none'
    assert reserved > 512
    context = json.loads(content)
    assert context['resident']['energy'] == agent.energy
    schema = payload['response_format']['json_schema']['schema']
    assert 'gather' not in schema['properties']['action']['enum']
    assert schema['properties']['explanation']['maxLength'] == 180
    assert 'farm' in schema['properties']['target']['anyOf'][0]['enum']


@pytest.mark.parametrize('agent_index', range(5))
def test_every_resident_prompt_carries_only_its_actual_previous_sources(tmp_path, agent_index):
    state = World().snapshot()
    agent = state.agents[agent_index]
    sources = [Event(event_id=f'{state.run_id}:{i}:{agent.id}', run_id=state.run_id,
                     tick=i, agent_id=agent.id, action='gather', outcome='accepted',
                     text=f'{agent.name} gathered food.') for i in range(1, 6)]
    hidden = sources[0].model_copy(update={'event_id': 'not-visible', 'agent_id': 'someone-else'})
    memory = MemoryContext(mode='semantic', query='supplies', as_of_tick=5,
                           recent=sources + [hidden], relevant=sources)
    payload, used, _ = build_input(agent, state, memory, settings(tmp_path))
    observed = json.loads(payload['messages'][1]['content'])
    assert observed['memories']
    assert {row['id'] for row in observed['memories']} <= {event.event_id for event in sources}
    assert used.mode == 'semantic'
    assert 'not-visible' not in payload['messages'][1]['content']
    assert len(''.join(m['content'] for m in payload['messages']).encode()) <= 800


def test_destination_is_followed_without_repeated_provider_calls(tmp_path):
    clock=Clock()
    planner=LivePlanner(settings(tmp_path),provider=lambda _:ProviderReply(
        {'action':'move','target':'forest','explanation':'Collect wood at the forest.'},50),clock=clock)
    world=World(live_planner=planner,mode='llm')
    try:
        planner.kick(world); wait(planner)
        first=step(world)
        assert first.decisions['ethan'].planner_mode=='live'
        assert (first.agents[0].x,first.agents[0].y)==(2,1)
        second=step(world,'second')
        assert (second.agents[0].x,second.agents[0].y)==(2,2)
        assert second.decisions['ethan'].planner_mode=='cached'
        third=step(world,'third')
        assert third.decisions['ethan'].action=='gather'
        assert third.agents[0].wood==2
        assert third.provider_usage.calls_run==1
    finally: planner.close()


@pytest.mark.parametrize('kind',['reset','revision'])
def test_stale_background_result_is_discarded_and_does_not_block_world(tmp_path,kind):
    started, release=threading.Event(),threading.Event()
    def provider(payload):
        started.set(); assert release.wait(3); return rest(payload)
    planner=LivePlanner(settings(tmp_path),provider=provider)
    world=World(live_planner=planner,mode='llm')
    try:
        planner.kick(world); assert started.wait(1)
        assert world.snapshot().agent_runtime['ethan'].pending
        if kind=='reset': world.reset(22)
        else: step(world)
        release.set(); wait(planner)
        assert not planner.cache
        assert world.snapshot().provider_usage.calls_day==1
        if kind=='reset': assert world.snapshot().tick==0
    finally: release.set(); planner.close()


@pytest.mark.parametrize('failure',[ProviderFailure('Groq timed out'),ProviderFailure('Groq quota/rate limit',60),
    ProviderReply({'action':'fly','target':None,'explanation':'No.'},40),
    ProviderReply({'action':'move','target':'unknown','explanation':'Go.'},40)])
def test_provider_errors_and_invalid_plans_use_labelled_fallback(tmp_path,failure):
    def provider(_):
        if isinstance(failure,Exception): raise failure
        return failure
    planner=LivePlanner(settings(tmp_path),provider=provider)
    world=World(live_planner=planner,mode='llm')
    try:
        planner.kick(world); wait(planner)
        result=step(world)
        assert result.decisions['ethan'].planner_mode=='fallback'
        assert result.decisions['ethan'].action in {'move','eat','rest','gather'}
        assert result.agent_runtime['ethan'].status=='fallback'
        assert result.provider_usage.calls_run==1
        if isinstance(failure,ProviderFailure) and failure.retry_after:
            assert result.provider_usage.cooldown_seconds>0
    finally: planner.close()


def test_all_five_residents_share_one_queue_and_twenty_call_run_cap(tmp_path):
    clock=Clock(); called=[]
    def provider(payload):
        called.append(json.loads(payload['messages'][1]['content'])['resident']['id']); return rest(payload)
    planner=LivePlanner(settings(tmp_path,llm_max_calls_per_run=5),provider=provider,clock=clock)
    world=World(live_planner=planner,mode='llm')
    try:
        for _ in range(5):
            planner.kick(world); wait(planner); planner.kick(world); wait(planner)
            clock.advance(15)
        assert called==['ethan','gayatri','aishani','rylee','saurya']
        clock.advance(60); planner.kick(world); wait(planner)
        assert len(called)==5
        assert world.snapshot().provider_usage.calls_run==5
    finally: planner.close()


def test_budget_is_persistent_shared_and_reset_does_not_erase_daily_usage(tmp_path):
    clock=Clock(); cfg=settings(tmp_path,llm_max_calls_per_day=2,llm_max_tokens_per_day=2000)
    path=tmp_path/'budget.sqlite'; a=Budget(path,cfg,clock); b=Budget(path,cfg,clock)
    try:
        call,reason=a.reserve('run-1','ethan',800); assert call and not reason
        assert b.reserve('run-2','gayatri',800)[0] is None
        a.finish(call,100,'failed'); clock.advance(15)
        call,_=b.reserve('run-2','gayatri',800); assert call
        b.finish(call,None,'failed'); clock.advance(60)
        assert a.reserve('run-3','aishani',800)[1]=='Daily request budget exhausted'
        usage=a.usage('run-3')
        assert (usage.calls_run,usage.calls_day,usage.tokens_day,usage.reserved_tokens_day)==(0,2,100,900)
    finally:a.close(); b.close()


def test_daily_token_cap_and_retry_after_are_enforced(tmp_path):
    clock=Clock(); b=Budget(tmp_path/'budget.sqlite',settings(tmp_path,llm_max_tokens_per_day=900),clock)
    try:
        call,_=b.reserve('run','ethan',800); b.finish(call,None,'failed',60)
        clock.advance(15)
        assert b.reserve('run','gayatri',800)[1]=='Provider cooldown (Retry-After)'
        clock.advance(60)
        assert b.reserve('run','gayatri',800)[1]=='Daily token budget exhausted'
    finally:b.close()


def test_missing_key_and_baseline_make_no_provider_calls(tmp_path):
    cfg=Settings(_env_file=None,minidavis_mode='llm',memory_db_path=str(tmp_path/'api.sqlite'),llm_api_key='')
    with TestClient(create_app(cfg)) as client:
        state=client.get('/state').json()
        assert client.get('/health').json()['live_llm_enabled'] is False
        result=client.post('/step',json={'run_id':state['run_id'],'expected_revision':0,'request_id':'one'}).json()
        assert all(d['planner_mode']=='fallback' for d in result['decisions'].values())
        assert result['provider_usage']['calls_day']==0
        assert client.post('/reset',json={'seed':11}).json()['mode']=='llm'
        assert client.post('/reset',json={'seed':11,'mode':'baseline'}).json()['mode']=='baseline'


def test_groq_http_payload_usage_and_no_automatic_retries(tmp_path,monkeypatch):
    calls=[]; original=httpx.Client
    def handle(request):
        calls.append(request)
        assert request.headers['authorization']=='Bearer fake-test-key'
        assert json.loads(request.content)['response_format']['json_schema']['strict']
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(rest(None).proposal)}}],
                                      'usage':{'total_tokens':123}})
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    state=World().snapshot();cfg=settings(tmp_path)
    payload,_,_=build_input(state.agents[0],state,MemoryContext(query='',as_of_tick=0),cfg)
    reply=GroqProvider(cfg)(payload)
    assert len(calls)==1 and reply.tokens==123 and reply.proposal['action']=='rest'


def test_live_prompt_uses_persisted_previous_events(tmp_path):
    cfg=settings(tmp_path); store=EventStore(tmp_path/'events.sqlite'); seen=[]
    planner=LivePlanner(cfg,provider=lambda p:(seen.append(p) or rest(p)))
    world=World(store=store,live_planner=planner)
    try:
        step(world,'baseline')
        world._state.mode='llm'  # preserve the existing run/history for this integration fixture
        planner.kick(world);wait(planner)
        assert world.snapshot().agent_runtime['ethan'].status=='live'
        decision=step(world,'live').decisions['ethan']
        assert decision.planner_mode=='live' and decision.memory.recent
        for event in decision.memory.recent:
            assert store.get(event.event_id)==event
            assert event.event_id in seen[0]['messages'][1]['content']
    finally:planner.close();store.close()


@pytest.mark.parametrize('memory_on', [True, False])
def test_all_five_live_prompts_use_the_memory_toggle_without_changing_world_observation(tmp_path, memory_on):
    cfg = settings(tmp_path, llm_max_calls_per_run=5)
    clock = Clock()
    store = EventStore(tmp_path / 'events.sqlite')
    prompts = []
    def provider(payload):
        prompts.append(json.loads(payload['messages'][1]['content']))
        return rest(payload)
    planner = LivePlanner(cfg, provider=provider, clock=clock, use_memory=memory_on)
    world = World(store=store, live_planner=planner, mode='baseline')
    try:
        state = step(world, 'warmup')
        world._state.mode = 'llm'
        for _ in range(5):
            planner.kick(world)
            wait(planner)
            clock.advance(15)
        assert len(prompts) == 5
        for context in prompts:
            agent_id = context['resident']['id']
            actual = next(agent for agent in state.agents if agent.id == agent_id)
            assert context['resident']['position'] == [actual.x, actual.y]
            assert bool(context['memories']) is memory_on
            for source in context['memories']:
                event = store.get(source['id'])
                assert event.agent_id == agent_id and event.run_id == state.run_id
                assert event.text == source['text']
    finally:
        planner.close()
        store.close()


@pytest.mark.parametrize('status',[400,401,403,429,503])
def test_http_failures_are_sanitized_and_never_retried(tmp_path,monkeypatch,status):
    original=httpx.Client; calls=[]
    def handle(request):
        calls.append(request)
        return httpx.Response(status,headers={'retry-after':'17'},json={'error':'Do not expose fake-test-key'})
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    with pytest.raises(ProviderFailure) as error:
        GroqProvider(settings(tmp_path))({})
    assert len(calls)==1 and 'fake-test-key' not in str(error.value)
    if status==429:assert error.value.retry_after==17


def test_http_timeout_is_sanitized(tmp_path,monkeypatch):
    original=httpx.Client
    def handle(_):raise httpx.ReadTimeout('Never expose fake-test-key')
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    with pytest.raises(ProviderFailure,match='Groq timed out'):
        GroqProvider(settings(tmp_path))({})
