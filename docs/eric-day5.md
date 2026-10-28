# Eric — Day 5 data and notebook preparation

Prepared 2026-10-27 for the Day 5 session on Thursday, 10/29.

## Ready now

- [200 draft synthetic interactions](../ml/data/interactions.jsonl): 50 cooperation, 50 conflict, 50 trade, 50 neutral.
- [Label policy and review instructions](../ml/data/README.md), including gifts, polite refusals, hostile trades and neutral mentions of past events.
- [Review queue](../ml/data/review_queue.csv): Aishani 001–050, Ethan 051–100, Gayatri 101–200. All 200 are deliberately still `pending`.
- [Candidate split](../ml/data/split_manifest.json): seed 20261029; 40 families with five examples each. Whole families stay together. Train 120 (30/class), validation 40 (10/class), test 40 (10/class).
- [Colab notebook](../ml/notebooks/03_finetune.ipynb): offline preflight by default; explicit switches for installation/training. The training helper compares TF-IDF/logistic regression with DistilBERT, selects by validation macro-F1 and exports model/tokenizer/config and metrics. Test rows are not returned to the training routine.
- Review/freeze guards reject incomplete approvals, changed data/review hashes, wrong labels, duplicate text/IDs and family leakage. Exact class IDs match the notebook/export.
- CI runs the ML data tests and offline notebook checks alongside the existing backend checks.

## Verification actually performed

- `python -m pytest backend/tests ml/tests -q`: **77 passed** (61 existing backend + 16 data/training-gate tests). One dependency deprecation warning from Starlette's test client; no test failures.
- `python scripts/prepare_interactions.py --out results/day5/data-check.json`: passes schema, balance, normalized-duplicate, reproducibility and family-isolation checks. [Report](../results/day5/data-check.json).
- `python scripts/check_day5_notebook.py`: all **six default code cells** pass, without ML libraries, provider calls or model downloads. [Report](../results/day5/notebook-check.json).
- Existing agent/memory notebooks still execute their offline defaults successfully.
- The self-contained nine-file ZIP was extracted into an isolated folder; all six notebook cells execute using only its files. [Package report](../results/day5/package-check.json).
- `python scripts/prepare_interactions.py --require-frozen` correctly exits with `Training blocked: dataset is draft; finish reviews and freeze`.

No human reviews, Google-account access checks, actual Colab/GPU run, trained weights, classifier metrics, held-out model evaluation or live town interactions are claimed. The opt-in training branch is prepared and syntax-checked, but has not been run with Transformers/PyTorch installed. Synthetic examples are teaching material, not evidence that the town already talks/trades or that its ML improves behavior.

## Eric: do next

1. Give the team the notebook and ZIP. For a fresh ZIP, from the repository root run:

   ```bash
   python scripts/package_day5.py --out /tmp/minidavis-day5-colab.zip
   ```

2. Confirm that all six people can open Colab. Upload the ZIP in Colab's Files panel, open `03_finetune.ipynb`, and run with both switches left `False`. This dry run needs **no API key and no GPU**. The local packaging check does not verify anyone's Google access.
3. Ask Aishani/Ethan/Gayatri to review their assigned rows. Correct text/labels in `interactions.jsonl`; mark each CSV row `approved` only after review. If wording/labels change after approval, reset that row and review it again. Revisit family grouping if related scenarios have been placed in separate families.
4. After corrections, check and freeze the reviewed data:

   ```bash
   python scripts/prepare_interactions.py --refresh-draft
   python scripts/prepare_interactions.py --freeze
   python scripts/prepare_interactions.py --require-frozen
   ```

   The freeze command intentionally fails while reviews are pending. Preserve the same frozen dataset/manifest for training and Day 6 evaluation. Do not inspect model performance to rearrange the held-out split.
5. Rebuild/reupload the ZIP from the reviewed repository. Gayatri selects a GPU if available, sets `RUN_TRAINING = True` and `INSTALL_DEPENDENCIES = True`, and runs the notebook in a fresh session. Install pinned notebook dependencies only in that training environment; retain and record its PyTorch/CUDA runtime. If Colab requests a runtime restart, restart and rerun in order.
6. Mount Drive when prompted. Use a new output folder for every run. Confirm that `classifier/`, `baseline.joblib`, `baseline-validation.json`, `metrics.json` and the frozen split manifest are saved in Drive and that the CPU reload cell succeeds. Share the artifact location with Rylee for Day 6. Keep held-out test evaluation for Day 6.

If GPU availability or installation blocks the session, record the actual error; the notebook can use CPU batch size 4, but its training time has not been measured. Do not report training success based on the dry run.

The classifier uses a public DistilBERT checkpoint; a Groq key is unrelated to this data-preparation/training task. Existing hosted-agent API configuration stays separate.

Workflow references: [Hugging Face text classification](https://huggingface.co/docs/transformers/tasks/sequence_classification), [Trainer](https://huggingface.co/docs/transformers/main_classes/trainer). The package versions selected for the notebook are published releases: [Transformers 4.57.1](https://pypi.org/project/transformers/4.57.1/), [Accelerate 1.11.0](https://pypi.org/project/accelerate/1.11.0/), [scikit-learn 1.7.2](https://pypi.org/project/scikit-learn/1.7.2/). Exact installed runtime versions are recorded when actual training runs.
