# Ethan Day 6: relationships, memories and restart behavior

## What changed

- An accepted trade adds +2 in both directions. An accepted gift adds +5 from recipient to giver. Values stay within -100 to 100.
- A gift is an offer with `receive_amount=0`, as the action rules define. The engine rejected zero before, so gifts could not exist.
- Every accepted non-gift trade counts as fair. The rules do not define an unfair trade.
- The accepter's event text now names both sides and the amounts.
- The proposer now gets a `trade_completed` event with ID `<accepter event ID>:partner`. Before, only the accepter remembered the trade. The separate ID keeps the proposer's own action on that tick from being overwritten.

## Memories describe executed events

The engine writes all event text. The model's explanation stays in `DecisionRecord.model_explanation` and never reaches the event store or relationships. `backend/tests/test_relationships.py` proves this with a planner that makes a false claim.

## Restart behavior: reset on restart

Checked against the real server on port 8011, with 5 steps, a stop and a start.

| Check | Result |
| --- | --- |
| Tick before and after restart | 5, then 0 |
| Same run after restart | No, a new `run_id` starts |
| Old events on disk | 25 before, 25 after |
| Ethan's memories after restart | 0 |

The town lives in server memory, so a restart starts a new town. SQLite keeps the old events, but retrieval filters by `run_id`, so the new run does not see them. This protects run isolation.

Any hosted preview resets on restart. Do not call it durable. On Render's free tier the SQLite file is lost too, so export traces before a restart if the run matters.

## Open items for the team

These items block the trade demo, and they are outside this task:

- No planner creates `offer_trade` or `accept_trade`, so normal runs have no trades and relationships stay at 0. Only a fixture can show a trade today.
- `POST /scenario/shortage`, `GET /trace` and `POST /replay` are not in `backend/app/main.py`.
- `accept_trade` does not check that residents are nearby, and offers do not expire after 5 ticks.
- There is no reject action, and the rules list one.

## Verification

`python -m pytest backend/tests ml/tests -q`: 112 passed, with 6 new tests. The 4 tests for new behavior failed before the change.

## Day 7 checks, run early on November 2

Run on branch `ethan/day6-memory-relationships`, not on the final merged code.

- Retrieval with real MiniLM: frozen 10/10, paraphrase 10/10. See `results/day7/retrieval.json`.
- Isolation and stale/future checks: `backend/tests/test_isolation.py` and `backend/tests/test_memory.py` pass. The new tests cover trade memories: bystanders do not see them, they stay hidden before their tick, and a new run cannot see the old run.
- Full suite: 115 passed.

Run these again on November 5 after teammates merge, then tick the Day 7 box.

`python scripts/check_retrieval.py --out results/day7/retrieval.json`

`python -m pytest backend/tests -q`
