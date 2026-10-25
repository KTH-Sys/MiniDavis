# Gayatri — Day 3: Seeded MVP Checks

## Task
Run three seeded 100-tick MVP checks in baseline mode and save the report.

## What I ran
- `python -m pytest backend/tests/test_agents.py -q`
- `python scripts/run_eval.py --mode baseline --seeds 11 22 33 --scenarios normal --ticks 100 --out results/day3`

## Results
| Seed | Ticks | Invariant failures | Provider calls | Actions seen |
|---|---|---|---|---|
| 11 | 100 | 0 | 0 | eat, gather, move, rest |
| 22 | 100 | 0 | 0 | eat, gather, move, rest |
| 33 | 100 | 0 | 0 | eat, gather, move, rest |

- Agent safety tests: 13 passed
- Results saved to `results/day3/summary.json`
- My results match Rylee's Day 3 run.

## Problems
- Python 3.12 was not installed on my laptop; fixed with `brew install python@3.12`. No problems with the project itself.