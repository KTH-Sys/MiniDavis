# Day 1–3 audit and remaining setup

Audited October 24, 2026. The checked boxes describe working project deliverables; they do not claim that each teammate personally ran a workshop or verified their own account access.

**17 of 18 deliverables are verified. Aishani's Day 3 implementation is complete, but the required five real Groq decisions await a server API key. No live response, semantic embedding model or fine-tuned classifier is claimed.**

| Owner | Day 1 | Day 2 | Day 3 |
| --- | --- | --- | --- |
| Eric | Project/configuration, connected app, recorded hosting budget: done | Real backend loop and controls: done | Integrated MVP and existing two-minute recording: done |
| Saurya | React 12×12 map and five residents: done | Play/Pause/Next Turn/Reset: done | All five inspectors, bounded activity feed and live/waiting/baseline/fallback labels: done |
| Rylee | FastAPI health/state/reset: done | Movement/gather/eat/rest and 100-turn safety: done | Model/action/run/revision validation and safety tests: done |
| Aishani | Runnable baseline notebook and explicit connection checker: done; provider access not yet verified | All five baseline policies follow destinations and eat/rest: done | Groq adapter, shared queue, cached plans and failure handling: done; **five real executed decisions pending key** |
| Ethan | SQLite event store and runnable memory notebook: done | Accepted/rejected events stored with correct outcomes: done | Real recent source IDs passed to the planner and inspector: done |
| Gayatri | Starter test pass/fail evidence: done | Invalid-action/resource tests and 100-turn checks: done | Three seeded 100-turn MVP checks saved: done |

## What was completed in this audit

- Added `ml/notebooks/01_agents.ipynb`; repaired repository discovery and expanded `02_rag.ipynb`. Both execute their default cells without a key or model weights. Live cells are off by default and support Colab Secrets.
- Added the Groq HTTP adapter with strict JSON output, non-thinking Qwen requests, bounded source-backed prompts and server-bound run/resident/revision metadata. Public model explanations are separate from executed outcomes.
- Added one background worker. Model calls run outside the world's lock. Readiness/state/reset remain usable while waiting; obsolete run/revision responses are discarded.
- Added cached location plans. The engine follows a shortest orthogonal route and validates every step; cached plans do not cause a Groq call for every movement. On reaching farm/forest, a destination plan gathers while legal. Baseline handles unavailable/invalid plans.
- Added four requests/minute, 15-second spacing, 30-second resident replan cooldown, 20 requests/run, 500 requests/day and a conservative 160,000-token daily budget by default. Reservations, failures and provider Retry-After cooldowns are persisted beside the event database in `llm-budget.sqlite`.
- Added honest per-resident UI states, source context for the actual model request, model observation revision, executed decision mode and aggregate request counts. Paused read-only status polling makes no provider calls.
- Added `test_world.py`, provider/queue/cache/failure tests, API-setting compatibility checks, UI state tests, and default notebook execution in GitHub CI.

The shared SQLite budget coordinates users/processes pointing to that same database. Separate laptops and Colab clones do not share those counters; Groq's account limits still cover all teammates. Use one central development backend when possible and reserve live notebook/demo allowances together. Start with one backend worker and one town.

The prompt-content limit uses UTF-8 byte length as a conservative token bound. The daily reservation also includes schema/protocol allowance and the maximum completion size. Reported total token usage replaces that reservation; unknown usage retains the full charge. This is deliberately conservative, not a model-specific tokenizer measurement.

## Verification evidence

- [Verification summary](../results/day1-day3/verification.json): 61 backend tests, 21 frontend tests, production build and browser checks pass.
- [Backend output](../results/day1-day3/backend-tests.txt): actual pass/fail log. A Starlette/httpx deprecation warning remains; it does not fail the checks.
- [Notebook execution](../results/day1-day3/notebooks.json): 6 agent and 4 memory code cells pass; zero live provider calls.
- [Seeded baseline summary](../results/day1-day3/summary.json): seeds 11, 22, 33; 100 ticks each; zero invariant failures and zero provider calls. Baseline is deterministic, so these are safety checks, not a diversity experiment.
- [Browser checks](../results/day1-day3/browser.json): all residents, backend positions, controls, source IDs, responsive terminal UI and reduced motion.
- [Existing two-minute MVP recording](../demo/eric-day3-mvp.webm).

Provider success cases in automated tests use mocked responses. Actual account availability, Colab execution by the team and real Groq outputs have not been verified.

## Your remaining setup

1. Sign in to [Groq](https://console.groq.com/keys), create a project API key, and confirm the project can access `qwen/qwen3.8-27b` with an adequate request/token allowance. This is currently a preview model; verify it again before the final demo. Check your account's [actual limits](https://console.groq.com/settings/limits).
2. Open the ignored `backend/.env` file. A blank baseline configuration has been prepared locally if that file did not already exist. Add `LLM_API_KEY=your_key_here`. Keep the key out of React, GitHub, Notion and chat. Use Colab Secret `LLM_API_KEY` for the optional notebook cell.
3. Reserve five calls for the team and run the real check from the repository root:

   ```bash
   source .venv/bin/activate
   python scripts/check_groq.py --live
   ```

   It can take roughly a minute because requests are paced. It makes at most five calls, validates and executes the resulting decisions, and saves `results/day3-live/live-decisions.json`. Success requires `"live_verified": true` and a live decision for all five residents. Missing keys exit with code 2 and make zero calls. Other failures return code 1 with partial evidence. Inspect the status details in the report; do not mark the task done for fallback or mocked results.

4. After successful verification, set `MINIDAVIS_MODE=llm` in `backend/.env`, restart the backend, and run the frontend using the [startup commands](../README.md#run-minidavis).
5. Click **Next Turn**, then let the pending request finish while paused. Its status should become live; the next turn can execute the ready plan. **Play** continues normal movement using cached plans/baseline while the shared queue rotates. If a slow response misses its observation revision it is discarded safely; pausing gives a request time to finish against a stable state. All five first requests require about a minute of paced active steps. Reset preserves the selected mode and does not erase daily usage.
6. Put the two notebooks in the shared Drive or open them from GitHub in Colab, and run the agent session with the team. One person should run the live cell once; everyone can run the baseline cells without using quota.

To return to offline baseline, set `MINIDAVIS_MODE=baseline` and restart the backend. No local LLM is required. Semantic RAG, training, conversations and trades remain later checkpoints.

Provider implementation references: [Groq structured output](https://console.groq.com/docs/structured-outputs), [API](https://console.groq.com/docs/api-reference), [reasoning controls](https://console.groq.com/docs/reasoning), [limits](https://console.groq.com/docs/rate-limits).
