"""Day 4: run the same seed twice, with memory on and off, and save both sides.

Memory off = the planner gets an empty memory (no recent or relevant events).
Baseline mode only: no API key and no provider calls. The baseline planner
follows fixed rules, so identical decisions are the expected honest result.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.agents import baseline_with_memory
from backend.app.memory import EventStore
from backend.app.schemas import MemoryContext, StepRequest
from backend.app.world import World


def make_planner(memory_on, seen):
    """Wrap the baseline planner and record exactly what memory it was given."""
    def planner(agent, observation, memory):
        if not memory_on:
            memory = MemoryContext(mode=memory.mode, query=memory.query, as_of_tick=memory.as_of_tick)
        seen[agent.id] = memory
        return baseline_with_memory(agent, observation, memory)
    return planner


def run(seed, ticks, memory_on):
    store = EventStore(Path(tempfile.mkdtemp()) / "memory.sqlite")
    seen = {}
    world = World(seed=seed, store=store, context_planner=make_planner(memory_on, seen))
    rows = []
    for tick in range(ticks):
        state = world.snapshot()
        state = world.step(StepRequest(run_id=state.run_id, expected_revision=state.revision,
                                       request_id=f"compare-{tick}"))
        for agent_id, d in sorted(state.decisions.items()):
            given = seen[agent_id]
            rows.append({
                "tick": d.tick, "agent_id": agent_id, "action": d.action, "outcome_text": d.explanation,
                "memory": "on" if memory_on else "off",
                "recent_ids": [e.event_id for e in given.recent],
                "relevant_ids": [e.event_id for e in given.relevant],
            })
    store.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--ticks", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path("results/day4-memory"))
    args = parser.parse_args()

    on, off = run(args.seed, args.ticks, True), run(args.seed, args.ticks, False)
    same = [a["action"] == b["action"] for a, b in zip(on, off)]
    # One example of each side: the last decision for the first resident.
    pick = lambda rows: [r for r in rows if r["agent_id"] == "ethan"][-1]
    report = {
        "seed": args.seed, "ticks": args.ticks, "mode": "baseline", "provider_calls": 0,
        "decisions_compared": len(same), "same_action": sum(same), "different_action": len(same) - sum(same),
        "note": "Baseline uses fixed rules; it receives memory but does not reason over it. "
                "No behavioral change from memory is claimed.",
        "example_memory_on": pick(on), "example_memory_off": pick(off),
        "memory_on": on, "memory_off": off,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"memory_on", "memory_off"}}, indent=2))
    print(f"Saved: {args.out / 'comparison.json'}")


if __name__ == "__main__":
    main()