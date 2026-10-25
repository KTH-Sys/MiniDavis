# Eric — Day 1 and Day 2 implementation

Implemented October 19, 2026. This is the integration foundation; teammates’ assigned tasks are not marked complete by this work.

## Day 1: project structure and shared configuration

- Added `backend/`, `frontend/`, `ml/`, `scripts/`, `results/`, `demo/` and `docs/`.
- Added pinned Python dependencies, exact frontend dependency versions and `package-lock.json`.
- Recorded Python 3.12 / Node 24 LTS and baseline startup commands.
- Added server-only environment loading, explicit frontend origins, safe baseline defaults and empty-key Groq configuration for the later adapter.
- Connected the frontend to real `/state`, `/reset`, `/step` and `/health` backend interfaces. The browser reads public API-base configuration only.
- Recorded hosting/budget status in [hosting-budget.md](hosting-budget.md); no paid resources activated.

## Day 2: loop and control integration

- React renders the fixed 12×12 map and the five residents from backend state.
- Next Turn advances once. Play schedules one turn after the previous request completes. Pause cancels future scheduling; an in-flight turn can finish.
- Reset aborts/discards prior browser responses and creates a fresh backend run. Reset requests cannot overlap within one browser.
- Step requests carry the run ID, expected revision and unique request ID. The backend serializes mutations, makes retries idempotent and rejects stale requests with 409.
- A small deterministic baseline policy exercises movement, gathering, eating and resting. This is temporary integration logic for the engine/agents owners to extend. It does not call Groq or use a trained model.
- State and recent events are in memory. Restart resets the town; events are not yet durable memories. The seed is recorded; the current fixed baseline policy does not randomize behavior by seed.

## Checks

From the repo root, after installing the backend dependencies:

```bash
python -m pytest backend/tests -q
python scripts/run_eval.py --mode baseline --seeds 11 --scenarios normal --ticks 100 --out results/day2
```

From `frontend/`:

```bash
npm ci
npm test
npm run build
```

The recorded baseline run completed 100 ticks, exercised move/gather/eat/rest, had zero invariant failures and made zero provider calls. See [summary](../results/day2/summary.json). Tests cover stale/duplicate/concurrent steps, reset isolation, credentials/CORS, control scheduling, failed requests and late responses after reset. CI repeats the API/control checks, baseline run and production build on pushes and pull requests.

Local results: **9 backend tests passed; 6 frontend control tests passed; production build passed.** A real Chrome browser check confirmed five rendered residents, exactly one Next Turn, repeated turns with Play, no new turns after Pause, restored initial positions after Reset, no page errors and no horizontal overflow at 390px width. These are local results; CI status is checked separately after pushing.

## Handoffs

- **Saurya:** Extend `frontend/src/components/` and the town screen; keep API mutations in `useTown` so requests remain serialized.
- **Rylee:** Extend `backend/app/world.py` and schemas for authoritative rules, trades and replay. Local state currently requires one backend process; do not deploy multiple workers against independent in-memory towns.
- **Aishani:** Extend `agents.py` with the Groq adapter, structured validation, queue/budgets and agent notebook. Live LLM modes currently fail clearly rather than pretending to be active.
- **Ethan:** Add durable event storage, visibility filtering and RAG. Current bounded events are a runtime log, not retrieved memory.
- **Gayatri:** Extend the tests and baseline evaluator for later comparisons; add reviewed data, training notebooks and classifier artifacts. No fine-tuning has run.

No hosted deployment, live model access, retrieval system, trained classifier, trade feature or Day 3 MVP completion is claimed.
