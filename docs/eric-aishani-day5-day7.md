# Eric and Aishani — tasks through Day 7

Implemented and checked November 3, 2026. Day 7 checks were run early for the November 5 checkpoint; rerun affected checks after further teammate changes. Day 0 remains complete based on Eric's confirmation, and prior Day 1–4 evidence remains available.

## Task status

| Owner/checkpoint | Result |
| --- | --- |
| Aishani, Day 5 | Reviewed 001–050 against the label policy. All labels matched; no text/label edits were needed. Eric explicitly delegated this review. Notes and a 50-row evidence file attribute it as AI-assisted; no personal human sign-off is claimed. |
| Eric, Day 5 | Prepared all 200 examples, incorporated Ethan's/Gayatri's recorded reviews, froze the unchanged 120/40/40 grouped split, and rebuilt the self-contained Colab package. All six notebook default cells pass. **Actual shared Colab training remains pending Gayatri.** |
| Aishani, Day 6 | Timeout, malformed JSON, illegal output, missing key, HTTP quota, recovery and shared-budget checks pass. The latest real check returns five accepted live decisions. |
| Eric, Day 6 | Local integration now supports social actions, safe trade lifecycle, actual classifier-to-event wiring, shortage, trace/replay and operator/viewer controls. Baseline preview packaging and explicit hosting blockers are ready. **The full trained-classifier/hosted ML gate remains pending the actual export and combined-RAM check.** |
| Aishani, Day 7 | Mocked failure/recovery, cached plans, stale-result rejection, 4/min pacing, a real 20-call cap across shared budget connections, daily charges and invalid Retry-After handling pass. |
| Eric, Day 7 | Reproduced integration bugs, fixed them, ran backend/frontend regressions and 1,000 baseline ticks, and recorded reproducible evidence and remaining dependencies. |

## Integration fixes

- Incorporated Ethan's relationship/memory branch (PR #4) into this implementation branch, preserving his commits and the newer main-branch data reviews. This does not itself merge his PR into main.
- Existing positive trade fixtures previously traded between distant residents. The engine now requires distance ≤1 for offers and acceptance. Fixtures place participants nearby to test successful transfers; new tests prove far-away attempts fail without changing inventory.
- Offers expire five ticks after creation; rejection and expired acceptance cannot transfer resources. Accepted transfers still commit once and conserve items/coins. Gifts preserve the fixed relationship rules.
- Residents can talk and initiate/respond to bounded exchanges through the LLM planner. The response schema now offers complete legal choices such as `move:farm` or `offer_trade:ethan`, removing action/destination mismatches. Schema choices are translated into validated engine actions. Social cached actions execute only once; arrival at a house rests instead of attempting to gather there.
- Both participants retain private source events for speech/offers/declines/completed trades. Bystanders do not retrieve those memories. Matching interaction IDs prevent duplicate UI entries for mirrored memories.
- The optional CPU classifier labels executed social events and saves label/confidence with the source. SQLite migrates existing event tables without dropping history. Inference failure leaves the interaction unclassified and cannot change resource/relationship accounting. Invalid/missing optional exports no longer break baseline startup; `CLASSIFIER_REQUIRED=true` provides a strict full-ML gate.
- `POST /scenario/shortage` reduces remaining farm stock to `min(current, 5)`, records an event and checks run/revision/request identity. Storage failure rolls back the mutation.
- `GET /trace` exports authoritative actions and shortage operations. `POST /replay` validates action outcomes and per-step state checksums, reproduces inventory/resources/relationships, and makes no model calls. Tampered traces leave the current town untouched. Replay is labelled and must be reset before advancing.
- Operator keys guard every mutation in a shared preview. Viewers can read state and traces. The key is entered at runtime and held only in the browser tab; it is separate from the server-only Groq credential. Paused viewers poll the same town without advancing it or multiplying provider calls.
- Nonfinite Retry-After values are bounded; invalid token reservations cannot reduce usage, and invalid measured usage retains the conservative charge. Provider failure reasons remain visible without exposing raw errors or credentials.

## Evidence and limits

- [Verification summary](../results/eric-aishani-day7/verification.json) records exact test counts, model status and gates.
- [Review evidence](../results/eric-aishani-day7/aishani-review.json) records all 50 delegated reviews; the frozen manifest binds the full review queue to the unchanged data.
- [Latest live decisions](../results/eric-aishani-day7/live-final/live-decisions.json) verify all five residents. The earlier run is retained in `live/` and includes one rejected reply; it is not called a five-resident success. Ten actual provider calls were used across both checks; all routine tests are mocked/no-call.
- [Retrieval checks](../results/eric-aishani-day7/retrieval.json) use the real pinned CPU MiniLM: 10/10 frozen and 10/10 paraphrase source checks.
- [Stress report](../results/eric-aishani-day7/stress/summary.json) runs 1,000 baseline ticks with no invariant failures and no provider calls.
- [Deployment RAM](../results/eric-aishani-day7/deployment-memory.json) measures 443.34 MiB process peak with MiniLM on the local Mac. No trained classifier was loaded, so combined RAM and real classifier latency are unverified.

New integration tests use a clearly scripted fixture that walks from the real starting positions, offers/accepts a trade and speaks. Stub classifier predictions in tests verify the event plumbing, not trained-model quality. They are never presented as trained results. No Colab training, held-out model score, paid hosting or hosted ML preview is claimed.

## Next handoff

1. Gayatri receives a fresh `minidavis-day5-colab.zip` built from this frozen dataset. The notebook defaults to dry run; enable its training switches only for the actual training session. The unchanged data hash is `82ccf456076109235a4bc1b0d5a53dfdcf8af5db056051e17c187396612ef71b`.
2. Save the actual `classifier/`, tokenizer/config, validation metrics and frozen manifest. Give Eric/Rylee the artifact path. Keep model weights out of Git.
3. Eric/Rylee load that export, verify real CPU predictions in the UI, measure both models together and finish the full-ML gate. Use the recorded [deployment plan](deployment.md); the free baseline blueprint is not a full ML deployment.
4. Gayatri's held-out evaluation and six-run model comparison remain her tasks. The generic `run_eval.py` currently implements baseline safety runs; no full three-mode evaluation result is invented here.

Reproduce the core checks from the repository root:

```bash
python -m pytest backend/tests ml/tests -q
python scripts/prepare_interactions.py --require-frozen
python scripts/check_day5_notebook.py
python scripts/run_eval.py --mode baseline --seeds 11 --ticks 1000 --out results/eric-aishani-day7/stress
```

From `frontend/`, run `npm test` and `npm run build`. Live checks are opt-in and spend quota; the saved successful run is sufficient unless the planner/model/config changes again.
