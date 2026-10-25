# Eric — Day 3–4 integration

Implemented October 24, 2026, on top of the team’s latest `main`. This preserves Ethan’s SQLite history and Rylee’s existing action validator and safety tests.

These notes describe the original baseline integration. The subsequent [all-member Day 1–3 audit](day1-day3-audit.md) adds the optional Groq adapter and notebooks; real provider verification still awaits a key.

## Day 3: baseline MVP

- Completed the UI/backend integration for resident selection, all five inspectors and a bounded event log. The roster, positions, resources, decisions and events come from one authoritative state response.
- Kept Play, Pause, Next Turn, Reset, duplicate-request protection and stale-run rejection intact. Reset removes the old decision and memory panels immediately with the new snapshot.
- The [two-minute working recording](../demo/eric-day3-mvp.webm) shows actual baseline controls, all five inspectors, retrieved source IDs, the event log and a reset. It contains no live LLM calls or fabricated events.
- Three baseline runs of 100 ticks for seeds 11, 22 and 33 completed without invariant failures or provider calls; see [summary](../results/eric-day3-day4/summary.json).

The baseline policy is fixed and does not randomize by seed. These are integration/safety runs, not evidence of behavioral diversity or improved AI quality.

## Day 4: retrieval → planner → inspector

`EventStore.retrieve()` scopes history in SQL to the current resident, run and observation tick before ranking. All current events are resident-private. It examines at most 500 eligible events, returns five recent events and up to three keyword-relevant events, and preserves the actual event IDs and outcomes. Recent and relevant lists may overlap; the same source is then identified in both views.

The world passes that `MemoryContext` and a detached, resident-scoped observation to the context-planner boundary. It records the exact context with the resulting executed decision. The inspector renders that stored context, rather than retrieving different evidence after the action. `GET /agents/{agent_id}` exposes the same contract and rejects stale run/revision queries.

The default `baseline_with_memory` receives evidence but delegates action selection to the existing fixed rules. **It does not claim to reason over memory.** The retrieval mode is labelled keyword search (`lexical`) or recent history only. No MiniLM model is downloaded, and no semantic retrieval, live Groq decision or classifier training is claimed by this integration.

Mutating planner copies cannot alter stored source text or world state. Events for one tick are committed as one SQLite transaction; a planner or write failure rolls the world back instead of leaving a partially applied tick.

## Verification

- 32 backend tests passed, including resident/run/future-event isolation, exact planner-to-inspector evidence, stale inspector queries, reset clearing and failed-tick rollback.
- 9 frontend tests passed, including control races, inspector selection/reset, visible source IDs and bounded accepted/rejected event display.
- Production frontend build passed.
- Ten frozen synthetic keyword-retrieval examples passed 10/10 expected-source-in-top-three checks. These test the keyword fallback; they are not a semantic-retrieval benchmark or evidence of agent behavior improvement.
- The real-browser check verifies all five residents’ visible source IDs against the backend, checks Play/Pause/Next Turn/Reset, checks reset clearing and tests layout at 390px width. See [browser evidence](../results/eric-day3-day4/browser.json).

Reproduce from the repository root:

```bash
python -m pytest backend/tests -q
python scripts/run_eval.py --mode baseline --seeds 11 22 33 --scenarios normal --ticks 100 --out results/eric-day3-day4
```

From `frontend/`:

```bash
npm ci
npm test
npm run build
```

## Team handoffs and remaining work

- **Aishani:** Connect the live Groq planner through `World(context_planner=...)`. Accept `(resident, observation, memory)`; produce a validated `Action` using Rylee’s validator. Add the agreed provider queue, limits and failure handling before enabling live mode. Build prompts only from this scoped observation/context, not an unrestricted `/state` response.
- **Ethan:** Extend retrieval with cached MiniLM embeddings and any public-event visibility rules; preserve SQL filtering and `MemoryContext` source IDs. Current memory queries include the goal/resource terms; tune them alongside real agent prompts.
- **Saurya:** Extend the inspector/event-log components and presentation while retaining the source IDs, truthful mode labels and one-snapshot consistency.
- **Rylee:** Extend the engine for trades/scenarios/replay; preserve tick transactions and run isolation. Use one backend process with the current in-memory world. Events survive a process restart; the town state itself is not resumed.
- **Gayatri:** Extend the comparison harness and training notebook. Synthetic retrieval fixtures and the fixed baseline runs do not establish an ML improvement.

No failing cases remained in Eric’s integration checks. The live-planner and semantic-retrieval work above remains assigned to its owners; this change does not mark their tasks complete or pass the Day 6 integration gate.
