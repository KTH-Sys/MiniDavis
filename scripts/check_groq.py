"""Check setup safely; --live explicitly makes up to five shared-budget Groq calls."""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.config import Settings
from backend.app.groq_planner import LivePlanner
from backend.app.schemas import StepRequest
from backend.app.validation import validate_model_action
from backend.app.agents import baseline_plan
from backend.app.world import World


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--timeout',type=int,default=180)
    parser.add_argument('--out',type=Path,default=ROOT/'results/day3-live')
    args=parser.parse_args()
    if args.timeout<1: parser.error('--timeout must be positive')
    settings=Settings()
    state=World().snapshot()
    for agent in state.agents:
        action=baseline_plan(agent,state)
        validate_model_action({'run_id':state.run_id,'agent_id':agent.id,'observation_revision':state.revision,
                               **action.model_dump()},agent,state)
    report={'model':settings.llm_model,'api_key_configured':bool(settings.llm_api_key.get_secret_value()),
            'baseline_agents_validated':5,'live_requested':args.live,'live_verified':False}
    if not args.live:
        print(json.dumps(report,indent=2)); return 0
    if not report['api_key_configured']:
        print(json.dumps(report|{'next_action':'Set LLM_API_KEY in backend/.env or the server environment; never put it in React.'},indent=2))
        return 2
    settings=settings.model_copy(update={'minidavis_mode':'llm','llm_max_calls_per_run':min(5,settings.llm_max_calls_per_run)})
    planner=LivePlanner(settings)
    world=World(live_planner=planner,mode='llm')
    try:
        deadline=time.monotonic()+args.timeout
        while time.monotonic()<deadline:
            planner.kick(world)
            snapshot=world.snapshot()
            running=planner.future is not None and not planner.future.done()
            if not running and all(status.status=='live' for status in snapshot.agent_runtime.values()): break
            if not running and (snapshot.provider_usage.calls_run>=settings.llm_max_calls_per_run
                or any('exhausted' in status.detail for status in snapshot.agent_runtime.values())): break
            time.sleep(.25)
        # The town stays paused while planning, making the observation revisions stable.
        state=world.snapshot()
        state=world.step(StepRequest(run_id=state.run_id,expected_revision=state.revision,request_id='live-check'))
        decisions={key:value.model_dump(mode='json') for key,value in state.decisions.items()}
        report.update(run_id=state.run_id,usage=state.provider_usage.model_dump(),decisions=decisions,
                      status={key:value.model_dump() for key,value in state.agent_runtime.items()})
        report['live_verified']=all(d['planner_mode']=='live' for d in decisions.values()) and len(decisions)==5
        args.out.mkdir(parents=True,exist_ok=True)
        (args.out/'live-decisions.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({key:value for key,value in report.items() if key not in {'decisions','status'}},indent=2))
        print(f'Evidence: {args.out / "live-decisions.json"}')
        return 0 if report['live_verified'] else 1
    finally:
        planner.close()


if __name__=='__main__':
    raise SystemExit(main())
