"""Reproducible town checks and opt-in, bounded baseline/LLM/RAG comparisons.

Live modes use one frozen planning window after the same baseline warmup. This
is a small exploratory comparison, not a long autonomous-civilization benchmark.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import Settings
from backend.app.groq_planner import GroqProvider, LivePlanner, resolve_proposal
from backend.app.memory import EventStore, minilm_embedder
from backend.app.schemas import StepRequest
from backend.app.world import World


def invariants(state):
    assert all(0 <= a.x < state.map.width and 0 <= a.y < state.map.height
               and 0 <= a.energy <= 100 and min(a.food,a.wood,a.coins) >= 0 for a in state.agents)
    assert all(r.stock >= 0 for r in state.resources)


def run_episode(mode, seed, scenario, ticks, settings=None, embedder=None, timeout=180):
    settings = settings or Settings()
    if mode != 'baseline' and not settings.llm_api_key.get_secret_value():
        raise ValueError('Set the server LLM_API_KEY before requesting a live comparison')
    attempts, decisions, action_counts = [], Counter(), Counter()
    accepted = rejected = trades = 0
    with tempfile.TemporaryDirectory(prefix='minidavis-eval-') as folder:
        store = EventStore(Path(folder)/'events.sqlite', embedder=embedder if mode=='rag' else None)
        planner = None
        world = None
        if mode != 'baseline':
            provider = GroqProvider(settings)
            def record(payload):
                started = time.perf_counter()
                context = json.loads(payload['messages'][1]['content'])
                row = {'agent_id':context['resident']['id'], 'memory_source_ids':[m['id'] for m in context['memories']]}
                attempts.append(row)
                try:
                    reply = provider(payload)
                    state = world.snapshot()
                    agent = next(a for a in state.agents if a.id==row['agent_id'])
                    row['proposal'] = reply.proposal
                    row['tokens'] = reply.tokens
                    try: resolve_proposal(reply.proposal,agent,state); row['valid_proposal']=True
                    except ValueError: row['valid_proposal']=False
                    return reply
                finally: row['latency_seconds']=time.perf_counter()-started
            planner=LivePlanner(settings.model_copy(update={'llm_max_calls_per_run':min(5,settings.llm_max_calls_per_run)}),
                                provider=record,use_memory=mode=='rag')
        world=World(seed=seed,store=store,live_planner=planner,mode='baseline')
        before_planning=None
        shortage=None
        try:
            for turn in range(ticks):
                state=world.snapshot()
                if scenario=='shortage' and turn==30:
                    previous_stock=next(r.stock for r in state.resources if r.id=='farm')
                    state=world.shortage(StepRequest(run_id=state.run_id,expected_revision=state.revision,request_id='shortage-30'))
                    current_stock=next(r.stock for r in state.resources if r.id=='farm')
                    shortage={'tick':30,'stock_before':previous_stock,'stock_after':current_stock,'changed_stock':previous_stock!=current_stock}
                if turn==30:
                    before_planning={'tick':state.tick,'revision':state.revision,
                        'agents':[a.model_dump() for a in state.agents], 'resources':[r.model_dump() for r in state.resources]}
                    if planner:
                        # Controlled evaluation: retain this run's real warmup memories.
                        # Public mode changes use Reset and correctly clear the old run.
                        world._state.mode='llm'
                        deadline=time.monotonic()+timeout
                        while time.monotonic()<deadline:
                            planner.kick(world)
                            state=world.snapshot()
                            running=planner.future is not None and not planner.future.done()
                            if not running and (len(planner.cache)==5 or state.provider_usage.calls_run>=5
                                or any('exhausted' in s.detail for s in state.agent_runtime.values())):break
                            time.sleep(.25)
                        if planner.future is not None: planner.future.result(timeout=settings.llm_timeout_seconds+5)
                state=world.snapshot()
                state=world.step(StepRequest(run_id=state.run_id,expected_revision=state.revision,request_id=f'eval-{turn}'))
                invariants(state)
                for decision in state.decisions.values():
                    decisions[decision.planner_mode]+=1
                    action_counts[decision.action]+=1
                    event=next(e for e in state.events if e.event_id==decision.event_id)
                    accepted+=event.outcome=='accepted'; rejected+=event.outcome=='rejected'
                    trades+=event.action=='accept_trade' and event.outcome=='accepted'
            state=world.snapshot()
            sources_valid=all((e:=store.get(source)) is not None and e.run_id==state.run_id
                and e.agent_id==row['agent_id'] and e.tick<=30 for row in attempts for source in row['memory_source_ids'])
            return {'seed':seed,'mode':mode,'scenario':scenario,'run_id':state.run_id,'ticks':ticks,
                'invariant_failures':0,'provider_calls':state.provider_usage.calls_run if planner else 0,
                'usage':state.provider_usage.model_dump() if planner else None,
                'decisions':dict(decisions),'actions':dict(action_counts),'engine_accepted':accepted,'engine_rejected':rejected,
                'completed_trades':trades,'fallback_fraction':(decisions['fallback']+decisions['waiting'])/(5*ticks),
                'proposal_valid':sum(row.get('valid_proposal',False) for row in attempts), 'proposal_attempts':len(attempts),
                'memory_sources_verified':sources_valid, 'memory_source_counts':[len(r['memory_source_ids']) for r in attempts],
                'shortage':shortage,'before_planning':before_planning,'attempts':attempts,
                'final':{'farm_stock':next(r.stock for r in state.resources if r.id=='farm'),
                    'agents':[a.model_dump() for a in state.agents]},
                'scope':'One planning window after 30 actual baseline turns; max five calls; later turns use cached plans/fallback. No guaranteed social behavior or causal memory benefit.'}
        finally:
            if planner:planner.close()
            store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['baseline','llm','rag','all'],default='baseline')
    parser.add_argument('--scenarios',choices=['normal','shortage'],nargs='+',default=['normal'])
    parser.add_argument('--seeds',type=int,nargs='+',default=[11])
    parser.add_argument('--ticks',type=int,default=100)
    parser.add_argument('--out',type=Path,default=ROOT/'results/day2')
    parser.add_argument('--live',action='store_true',help='Authorize up to five shared-budget calls per non-baseline episode')
    parser.add_argument('--timeout',type=int,default=180)
    args=parser.parse_args()
    if args.ticks<1 or any(seed<0 or seed>2**31-1 for seed in args.seeds) or args.timeout<1:
        parser.error('Use positive tick/timeout values and seeds between 0 and 2147483647.')
    modes=['baseline','llm','rag'] if args.mode=='all' else [args.mode]
    if any(mode!='baseline' for mode in modes) and (not args.live or args.ticks<=30):
        parser.error('Live comparisons require --live and more than 30 ticks.')
    if 'shortage' in args.scenarios and args.ticks<=30:parser.error('Shortage is applied at tick 30; request more than 30 ticks.')
    settings=Settings()
    if args.live and not settings.llm_api_key.get_secret_value():parser.error('Configure the server LLM_API_KEY first.')
    embedder=None
    if 'rag' in modes:
        embedder=minilm_embedder(settings.embedding_model,settings.embedding_cache_path,settings.embedding_revision)
        if embedder is None:parser.error('Install backend/requirements-ml.txt before RAG comparisons.')
        embedder.warmup()
    args.out.mkdir(parents=True,exist_ok=True)
    reports=[]
    for seed in args.seeds:
        for scenario in args.scenarios:
            for mode in modes:
                print(f'Checking {mode}, {scenario}, seed {seed}',flush=True)
                report=run_episode(mode,seed,scenario,args.ticks,settings,embedder,args.timeout)
                (args.out/f'{mode}-{scenario}-{seed}.json').write_text(json.dumps(report,indent=2)+'\n')
                reports.append(report)
    summary=[{k:r[k] for k in ('seed','mode','scenario','run_id','ticks','invariant_failures','provider_calls',
        'decisions','actions','engine_accepted','engine_rejected','completed_trades','fallback_fraction',
        'proposal_valid','proposal_attempts','memory_sources_verified','memory_source_counts','shortage')} for r in reports]
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    matched=all(len({json.dumps(r['before_planning'],sort_keys=True) for r in reports if r['seed']==s and r['scenario']==c})==1
                for s in args.seeds for c in args.scenarios)
    live_passed=all(r['proposal_valid']==r['provider_calls']==min(5,settings.llm_max_calls_per_run)
        and r['memory_sources_verified'] and (r['mode']!='rag' or all(r['memory_source_counts'])) for r in reports if r['mode']!='baseline')
    (args.out/'comparison.json').write_text(json.dumps({'matched_observations':matched,'live_checks_passed':live_passed,'model':settings.llm_model,
        'embedding_revision':settings.embedding_revision,'calls':sum(r['provider_calls'] for r in reports),
        'scope':'Exploratory matched-state comparison, not statistical proof of improved behavior.'},indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return 0 if matched and live_passed else 1


if __name__=='__main__':raise SystemExit(main())
