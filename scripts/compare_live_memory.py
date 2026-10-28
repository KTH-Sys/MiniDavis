"""Day 4 live memory on/off pairs. Explicit --live makes at most ten Groq calls."""

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.config import Settings
from backend.app.groq_planner import GroqProvider, LivePlanner
from backend.app.memory import EventStore, minilm_embedder
from backend.app.schemas import StepRequest
from backend.app.world import World


def run_condition(settings, embedder, memory_on, timeout):
    prompts = []
    provider = GroqProvider(settings)

    def record(payload):
        context = json.loads(payload['messages'][1]['content'])
        prompts.append({'agent_id': context['resident']['id'], 'context': context,
                        'content_bytes': sum(len(m['content'].encode()) for m in payload['messages'])})
        return provider(payload)

    with tempfile.TemporaryDirectory(prefix='minidavis-live-memory-') as folder:
        store = EventStore(Path(folder) / 'events.sqlite', embedder=embedder)
        planner = LivePlanner(settings, provider=record, use_memory=memory_on)
        world = World(seed=11, store=store, live_planner=planner, mode='baseline')
        try:
            # Three actual baseline ticks produce the same state/history in each
            # condition. No provider is called during this warmup.
            for index in range(3):
                state = world.snapshot()
                world.step(StepRequest(run_id=state.run_id, expected_revision=state.revision,
                                       request_id=f'warmup-{index}'))
            before = world.snapshot()
            # Controlled evaluation fixture: preserve this run's real memories
            # when activating planning. The public Reset route clears them.
            world._state.mode = 'llm'
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                state = world.snapshot()
                running = planner.future is not None and not planner.future.done()
                if not running and len(planner.cache) == 5:
                    break
                if not running and state.provider_usage.calls_run >= settings.llm_max_calls_per_run:
                    break
                if not running and any('exhausted' in s.detail for s in state.agent_runtime.values()):
                    break
                planner.kick(world)
                time.sleep(.25)
            state = world.snapshot()
            state = world.step(StepRequest(run_id=state.run_id, expected_revision=state.revision,
                                           request_id='execute-live-plans'))
            decisions = {key: value.model_dump(mode='json') for key, value in state.decisions.items()}
            source_check = all(store.get(event.event_id) == event
                               for d in state.decisions.values() for event in d.memory.recent + d.memory.relevant)
            complete = len(decisions) == 5 and all(d['planner_mode'] == 'live' for d in decisions.values())
            memory_check = len(prompts) == 5 and all(bool(p['context']['memories']) == memory_on for p in prompts)
            return {'memory': 'on' if memory_on else 'off', 'run_id': state.run_id,
                    'before': {'tick': before.tick, 'revision': before.revision, 'seed': before.seed,
                               'agents': [a.model_dump() for a in before.agents],
                               'resources': [r.model_dump() for r in before.resources]},
                    'all_five_live': complete, 'prompt_memory_verified': memory_check,
                    'sources_verified': source_check, 'decisions': decisions, 'prompts': prompts,
                    'usage': state.provider_usage.model_dump(),
                    'status': {key: value.model_dump() for key, value in state.agent_runtime.items()}}
        finally:
            planner.close()
            store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--timeout', type=int, default=180, help='Maximum seconds per condition')
    parser.add_argument('--out', type=Path, default=ROOT / 'results/day0-day4/live-memory-comparison.json')
    args = parser.parse_args()
    if not args.live:
        parser.exit(2, 'Use --live to explicitly authorize up to ten shared-budget Groq calls.\n')
    if args.timeout < 1:
        parser.error('--timeout must be positive')
    settings = Settings()
    if not settings.llm_api_key.get_secret_value():
        parser.exit(2, 'Set the server LLM_API_KEY locally; do not put it in the report.\n')
    embedder = minilm_embedder(settings.embedding_model, settings.embedding_cache_path, settings.embedding_revision)
    if embedder is None:
        parser.exit(2, 'Install backend/requirements-ml.txt first; no provider calls made.\n')
    embedder.warmup()  # fail before consuming Groq quota if weights cannot load
    settings = settings.model_copy(update={'llm_max_calls_per_run': min(5, settings.llm_max_calls_per_run)})
    print('Memory on: planning five residents through the shared queue.', flush=True)
    on = run_condition(settings, embedder, True, args.timeout)
    print('Memory off: planning five residents with the same observed state.', flush=True)
    off = run_condition(settings, embedder, False, args.timeout)
    matched = on['before'] == off['before']
    passed = matched and all(row['all_five_live'] and row['prompt_memory_verified'] and row['sources_verified']
                             for row in (on, off))
    report = {'passed': passed, 'model': settings.llm_model, 'seed': 11,
              'retrieval': 'semantic', 'embedding_cache_key': embedder.cache_key,
              'matched_observations': matched, 'memory_on': on, 'memory_off': off,
              'provider_calls': on['usage']['calls_run'] + off['usage']['calls_run'],
              'example_memory_on': on['decisions'].get('ethan'), 'example_memory_off': off['decisions'].get('ethan'),
              'note': 'Five exploratory matched-state pairs, not statistical evidence or a guaranteed memory benefit.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'model', 'matched_observations', 'provider_calls')}, indent=2))
    print(f'Evidence: {args.out}')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
