# MiniDavis interaction classifier

Presentation export, November 4, 2026. This is a four-label text classifier based on `distilbert/distilbert-base-uncased`. Qwen remains the separate hosted decision model; it was not fine-tuned.

## Provenance and training

Gayatri shared `day5-v2` containing a usable `checkpoint-15` at epoch 1, plus the TF-IDF baseline. The `checkpoint-30` and `checkpoint-45` folders in the supplied ZIP were empty; no final classifier export or `metrics.json` was present. The first checkpoint recorded validation macro-F1 0.3629 and a planned ten-epoch run. Those files prove a saved epoch, not completion of ten epochs.

Eric explicitly authorized completing missing work. The presentation export continues those weights for **two additional epochs**, giving three observed weight-training epochs in total. It uses a **fresh optimizer**, rather than claiming an exact optimizer-state resume. The continuation uses the repository's unchanged, reviewed 120-example training split. Checkpoints are selected only by validation macro-F1 over 40 examples. The source checkpoint's original dataset fingerprint was unavailable; that provenance limitation remains in the report.

Starting settings: maximum length 128, learning rate `2e-5`, CPU batch size 4, seed 20261029, two CPU threads for this run. The model, tokenizer, config and hashes are saved in the inference export. The repository notebook still defaults to a dry run; the completed presentation continuation is recorded separately in [classifier-validation.json](../results/presentation/classifier-validation.json).

## Dataset and results

The synthetic dataset has 200 examples: 50/class and 40 scenario families. The grouped split is 120 train / 40 validation / 40 test. Only text enters model features. IDs, reviewer names and family labels are excluded. Data and split hashes were preserved throughout this audit.

| Model | Validation macro-F1 | Test macro-F1 | Test accuracy |
| --- | ---: | ---: | ---: |
| TF-IDF + logistic regression | 0.6154 | 0.7089 | 72.5% |
| Presentation DistilBERT | 0.6508 | 0.8499 | 85.0% |

The export was frozen after validation selection, then evaluated once on the 40 test examples. No further tuning followed that result. Both models used the same training/test assignments. See [classifier-test.json](../results/presentation/classifier-test.json) for per-class scores, predictions and confusion matrices. Rows of the matrices are actual labels; columns are predictions in cooperation, conflict, trade, neutral order.

CPU single-example inference after warmup averaged **13.1 ms** (p95 **15.0 ms**) over those 40 examples on the local Mac with two threads. Hardware, concurrent work and text length affect latency.

## Use and limits

- Valid labels: cooperation=0, conflict=1, trade=2, neutral=3.
- The world attaches label/confidence after a social action executes. Classifier output cannot move inventory or set relationship scores.
- `/classify` and **Try the trained classifier** test real inference without adding a town event or memory.
- The labelled sample replay makes no model calls, so replayed interactions remain unclassified. A separate scripted engine check ran the same legal actions through the real classifier and semantic memory; see [ml-integration.json](../results/presentation/ml-integration.json).
- A known browser smoke example, “Ethan gives Saurya spare food without asking for payment,” was incorrectly classified as trade at about 34.1% confidence. Its intended label is cooperation. The trade example in the panel was classified as trade at about 57.4%. Confidence is not calibrated accuracy.
- These small synthetic results do not establish real-world generalization. There is no demographic, multilingual or adversarial robustness evaluation. The source checkpoint's original data fingerprint was not supplied.

## Export and reproduction

Weights stay outside Git. Share `minidavis-classifier.zip`, produced by:

```bash
python scripts/package_classifier.py --out /path/to/minidavis-classifier.zip
python scripts/install_classifier.py --archive /path/to/minidavis-classifier.zip
```

The installer checks paths, file hashes, dataset version and label mapping before writing inference-only files. It refuses to overwrite a different existing model. Use a new empty destination if retaining several exports.

Model SHA-256: `e8d59c293252734b9e0644839884fd1ca369a249a7eb46cd638caed079199880`.

Run `python scripts/check_presentation_ml.py` to verify loading, real engine labels, private source retrieval and strict API readiness with the installed export. This check uses scripted actions and zero provider calls. Keep the saved test report; do not repeatedly tune against it.
