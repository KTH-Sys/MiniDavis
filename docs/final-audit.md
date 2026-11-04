# Final presentation audit — November 4, 2026

**Status: local demo implementation is ready for presentation checks; venue rehearsal remains the team's final step.** The code, model artifacts and measured evidence are separate from claims about deployment or long autonomous behavior. The machine-readable record is [verification.json](../results/presentation/verification.json).

## Audience presentation update

The main interface now shows only resident stories and simple playback controls. Technical inspectors, model probes, memory sources and configuration stay behind **Presenter tools**. The [single illustrated LaTeX guide](../output/pdf/MiniDavis-Presentation-Guide.pdf) follows the requested speaker assignments and contains no presentation timestamps or suggested durations. See [guide verification](../results/presentation/guide-verification.json) for the new checks.

## Repairs and completion

- Preserved the original root project plan, technical checklist and legacy frontend README in `docs/archive/`. The root README now describes the actual project, architecture, setup, evaluation and demo.
- Added explicit baseline/live mode selection and setup status. Local runs no longer display an unexplained operator-password prompt; protected shared previews retain access controls.
- Live playback waits for pending replies and advances at a slower pace, avoiding responses being discarded simply because the UI advanced every 700 ms. Manual stepping also waits for pending planning.
- Added a labelled sample-run button for reproducible trades, speech and shortage, plus correct replay labels and relationship display.
- Fixed mirrored interaction headings to retain the original speaker's event rather than attributing speech to the listener.
- Added a real CPU classifier test panel and `/classify` endpoint. It does not mutate town state or memories and respects shared operator access.
- Recovered Gayatri's saved epoch-1 DistilBERT checkpoint, completed two additional epochs on the unchanged frozen training data, selected by validation and exported a portable model. The original ten-epoch training configuration was not completed or claimed. Source checkpoint data fingerprints were unavailable.
- Evaluated the fixed export once on the held-out test set. Validation macro-F1: 0.6508; test macro-F1: 0.8499; accuracy: 85% on 40 synthetic examples. The simpler baseline scored 0.7089 test macro-F1 / 72.5% accuracy.
- Added checksummed inference packaging and safe installation, plus an opt-in baseline/LLM/RAG comparison runner with honest denominators and bounded calls.

## Observed checks

| Check | Result |
| --- | --- |
| Backend and data suite | 152 tests passed |
| Frontend suite | 42 tests passed after audience-view simplification |
| Production frontend build | Passed |
| Reviewed dataset | Frozen 200 examples; 120/40/40 grouped split; unchanged hashes |
| Notebook defaults | Offline checks, no training/provider calls |
| Real CPU models | Classifier and pinned MiniLM loaded; source/private/run isolation checks pass |
| Scripted integration | Legal trade, speech and shortage carry real classifier predictions; world accounting is independent of predictions |
| Classifier API | Real label/confidence returned; town unchanged |
| Six exploratory comparison runs | 20/20 valid live proposals; zero invariant failures; actual source IDs verified |
| Browser | Live decision, semantic memory status, sample interactions, real classifier response and desktop layout checked; see browser evidence |
| Model package | Installed from the ZIP with file hashes and label mapping verified |
| GitHub checks | Verify on the final pushed commit; local evidence alone does not imply CI passed |

Earlier Day 7 evidence also includes 1,000 baseline ticks without invariant failures. A fresh stress report and current retrieval checks are included in the final evidence.

## Important presentation limits

- The twenty-call comparison produced three talks and two offers, but no completed autonomous trade. The accepted-trade demonstration is clearly scripted.
- The normal and shortage runs use the same starter world and apply shortage at tick 30. Its farm is already empty then, so the shortage operation has no further stock effect. These results cannot establish behavior under a distinct shortage shock.
- Each live comparison episode contains a single planning window. Cached/fallback decisions make up most later turns. These are exploratory demonstrations, not evidence of sustained autonomy or a causal RAG benefit.
- The model can mislabel inputs: a free-food gift example was predicted as trade with low confidence. The small synthetic test and missing original checkpoint fingerprint limit generalization claims.
- Local CPU RAM is measured in [ml-integration.json](../results/presentation/ml-integration.json). No Linux-hosted RAM or public deployment has been verified. The baseline preview blueprint remains optional.
- No thirty-minute human rehearsal, two stage rehearsals or team-recorded video is claimed. Complete those using [presentation.md](presentation.md) on the actual presentation computer.

## Reproduce without spending provider quota

Follow the root README's verification commands. For installed ML artifacts, also run:

```bash
python scripts/check_presentation_ml.py
python scripts/check_retrieval.py --out /tmp/minidavis-retrieval.json
```

Keep the original held-out model report. Re-running training or selecting changes after looking at test scores would require a new evaluation decision, not replacement of the saved result. Reuse the existing live evidence unless the provider/planner changes or a specific failure needs investigation.
