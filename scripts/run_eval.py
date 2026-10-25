"""Day 2 baseline integration check. Later ML comparisons remain Gayatri's work."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.schemas import StepRequest
from backend.app.world import World


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["baseline"], default="baseline")
    parser.add_argument("--seeds", type=int, nargs="+", default=[11])
    parser.add_argument("--scenarios", choices=["normal"], nargs="+", default=["normal"])
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--out", type=Path, default=Path("results/day2"))
    args = parser.parse_args()
    if args.ticks < 1 or any(seed < 0 or seed > 2**31 - 1 for seed in args.seeds):
        parser.error("Use positive tick counts and seeds between 0 and 2147483647.")
    args.out.mkdir(parents=True, exist_ok=True)
    report = []
    for seed in args.seeds:
        world = World(seed=seed)
        state = world.snapshot()
        actions = set()
        for turn in range(args.ticks):
            state = world.step(StepRequest(run_id=state.run_id, expected_revision=state.revision, request_id=f"eval-{turn}"))
            for agent in state.agents:
                assert 0 <= agent.x < 12 and 0 <= agent.y < 12
                assert 0 <= agent.energy <= 100
                assert min(agent.food, agent.wood, agent.coins) >= 0
            assert all(resource.stock >= 0 for resource in state.resources)
            actions.update(event.action for event in state.events if event.tick == state.tick)
        (args.out / f"baseline-{seed}.json").write_text(state.model_dump_json(indent=2) + "\n")
        report.append({"seed": seed, "mode": "baseline", "scenario": "normal", "ticks": args.ticks,
                       "invariant_failures": 0, "provider_calls": 0, "actions_seen": sorted(actions)})
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
