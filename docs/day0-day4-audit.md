# Day 0–4 audit — October 27, 2026

**All Day 0–4 tasks are complete:** the 24 Day 1–4 technical deliverables are implemented and verified, and Eric explicitly confirmed all six Day 0 task groups complete on October 27, 2026. A completed implementation does not claim that every teammate personally attended a workshop or ran it on their laptop.

The audit incorporates Ethan's MiniLM work and Gayatri's baseline comparison from main (`768b196`). Earlier unpublished Day 5 data/notebook preparation is preserved in its own commit; no human dataset reviews or classifier training were performed in this audit.

## Every owner, every checkpoint

| Owner | Day 0 | Day 1 | Day 2 | Day 3 | Day 4 |
| --- | --- | --- | --- | --- | --- |
| Eric | Done: confirmed by Eric on October 27 | Done: project/config, connected app, hosting-budget record | Done: real controls and tick loop | Done: integrated MVP and existing two-minute recording | Done: retrieved sources connect to planner and inspector |
| Saurya | Done: confirmed by Eric on October 27 | Done: React, 12×12 town, five residents | Done: Play/Pause/Next Turn/Reset | Done: inspector/log and runtime state labels | Done: source text/IDs, query, cutoff and truthful semantic/keyword labels |
| Rylee | Done: confirmed by Eric on October 27 | Done: FastAPI health/state/reset | Done: move/gather/eat/rest and safety runs | Done: model/action/run/revision validation | Done: private/old/future memory isolation, including semantic API/reset checks |
| Aishani | Done: confirmed by Eric on October 27 | Done: baseline notebook and connection checker | Done: all five legal baseline policies | Done: five actual executed live Groq decisions | Done: all five real requests carry scoped source memories, with prompt bounds |
| Ethan | Done: confirmed by Eric on October 27 | Done: SQLite and memory notebook | Done: accepted/rejected outcomes saved | Done: real recent-event IDs in inputs | Done: cached real MiniLM CPU retrieval and 10 frozen checks |
| Gayatri | Done: confirmed by Eric on October 27 | Done: starter tests and evidence | Done: invalid-action/resource checks | Done: three seeded 100-tick reports | Done: actual matched memory-on/off examples and source IDs saved |

## Repairs made

- Changed compact positional resident arrays into named fields after real Groq replies misread state. Prompts now identify resource kinds and legal actions for the current tile.
- Constrained response action enums, destination IDs and explanation length per request. Engine validation and fallback still decide whether a proposal is legal; a JSON schema alone is not world validation.
- Added a real live memory-on/off harness. Both conditions start from the same seed, state and three actual baseline ticks. The off switch removes memories from the actual provider input, not just the displayed report. Both use the existing shared persistent budget and at most five calls per condition.
- Preserved original invalid-proposal reasons instead of replacing them with a later budget message.
- Fixed stale embedding reuse: cache keys now include the model/revision and source-text fingerprint. Changed text or models cannot reuse old vectors. Legacy event-ID-only vectors remain unused. Invalid batch lengths, dimensions and nonfinite values use labelled keyword fallback.
- Made MiniLM explicit opt-in (`MEMORY_RETRIEVAL_MODE=semantic`) so base tests/startup stay download-free. A pinned CPU model is warmed during startup before serving turns. Local weights are ignored by Git.
- Fixed the terminal footer's hardcoded keyword label and the older inspector's stale claims that live AI/semantic retrieval were pending. Sources, query, cutoff and actual planner mode are shown accurately.
- Made the retrieval checker fail if it silently falls back to lexical search; it also supports an output-file argument and returns a failing exit code when its retrieval gate fails.

## Observed results

- **96 backend/data tests pass:** 80 backend and 16 Day 5 data/training-gate tests.
- **22 frontend tests pass**, including semantic labels/source IDs; the production build passes.
- **Five of five live Groq decisions verified** in [the final connection check](../results/day0-day4/live-final/live-decisions.json). Earlier failures are retained in `live/`, `live-rerun/` and `live-diagnostic/`; none are reported as successful live decisions.
- **Real CPU MiniLM: 10/10 frozen retrieval checks and 10/10 paraphrase checks** put the expected source in the top three. Every query used semantic mode. [Report](../results/day0-day4/retrieval.json). This tiny fixture is a smoke check, not a general retrieval benchmark.
- **All five semantic API inspectors match the authoritative decision/source evidence**, and reset removes old-run memories. [Report](../results/day0-day4/semantic-api.json).
- **Three seeds × 100 baseline ticks** have no invariant failures and no provider calls. [Report](../results/day0-day4/baseline/summary.json).
- The existing agent and RAG notebooks execute locally, including the two real MiniLM cells, without live provider calls. Day 5's six default cells still pass without training.
- The existing [MVP recording](../demo/eric-day3-mvp.webm) and [prior browser evidence](../results/day1-day3/browser.json) remain available; they are historical evidence, not a new browser session from this audit.

### Live memory comparison: inspect the limitations

[The full comparison](../results/day0-day4/live-memory-comparison.json) contains five paired requests per condition, matched observed state, real model outputs, the exact prompt memories and source IDs. Every memory-on request includes its own stored events; every memory-off request has an empty memory list. Inputs stay within the conservative 800-byte prompt-content bound.

**Four of five proposals were accepted in each condition.** The others used safe baseline fallback. Ethan's examples are accepted live decisions on both sides, so the Day 4 requirement to save a real matching example with and without memory is satisfied. The harness's stricter `passed` flag requires all five proposals to be live in both conditions; that flag is **false** and is preserved honestly. Do not quote this as ten accepted live decisions or proof that memory improves behavior. The Day 3 five-resident live verification is a separate successful run.

The audit made **30 provider calls total**, including failed diagnostic attempts and the ten comparison calls. They used the shared queue/counters; no extra live calls are made by the unit tests. Actual token usage is recorded in the saved live reports. The local API key is never committed. `pip check` reports no broken requirements. A Starlette/httpx deprecation warning remains non-failing.

## Day 0 completion confirmation

After reviewing this audit, Eric stated: “I confirm all day0 tasks are done.” All six Day 0 task groups are therefore complete based on the team lead's explicit confirmation. This closes the earlier GitHub/Notion/Colab access, folder-organization and Groq ownership/limit-recording follow-ups. The original independent audit observations and technical evidence remain as recorded; the confirmation is a separate evidence source.

Day 5 dataset review and actual classifier training remain future work. The live-comparison fallback counts and stricter false all-five comparison flag above are unchanged.

For local semantic RAG, install and configure:

```bash
source .venv/bin/activate
python -m pip install -r backend/requirements-ml.txt
```

In the ignored `backend/.env`, add `MEMORY_RETRIEVAL_MODE=semantic`. To use hosted decisions, also set `MINIDAVIS_MODE=llm`; Eric's local `LLM_API_KEY` is already configured. Restart the backend after changing settings. Baseline + keyword retrieval remain the default, preserving zero-call startup behavior.

Reproduce the no-provider checks:

```bash
python -m pytest backend/tests ml/tests -q
python scripts/check_retrieval.py --out results/day0-day4/retrieval.json
python scripts/check_day4_api.py
python scripts/verify_notebooks.py
python scripts/check_day5_notebook.py
```

Only when new live evidence is needed and quota is reserved:

```bash
python scripts/check_groq.py --live
python scripts/compare_live_memory.py --live
```

These scripts can spend five and ten provider calls respectively. The comparison intentionally exits nonzero when any requested live plan falls back. Do not retry repeatedly just to hide failures. Current events are resident-private; public/participant conversation visibility, trading, shortage, replay and classifier integration remain later checkpoints.
