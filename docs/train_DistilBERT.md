# MiniDavis: train DistilBERT step by step

**Goal:** train a small model that reads a town interaction and predicts one of four labels. Gayatri runs training; Eric prepares the files and helps with the session.

Example input: `Ethan gives Rylee spare food without asking for payment.`

Expected label: `cooperation`.

We start with `distilbert/distilbert-base-uncased` and adjust its weights using our examples. This produces an interaction classifier. The town's Qwen decision model stays separate. This is the standard [Hugging Face text-classification workflow](https://huggingface.co/docs/transformers/tasks/sequence_classification), adapted to our four labels.

**Current status:** 200 synthetic draft examples and the notebook are prepared. Human reviews and actual training are still pending. The notebook's offline checks have passed; its training path has not yet been verified in Colab. No API key is needed for this public DistilBERT checkpoint. An internet connection is needed for installation and the initial model download.

## 1. Open the project on Eric's Mac

Open Terminal and run:

```bash
cd /path/to/your/MiniDavis/folder
source .venv/bin/activate
```

Use your own repository location if working on another computer. The commands in Steps 1–4 run in Terminal. Steps 5–10 run in Google Colab.

These files must be present in your local copy:

```text
ml/data/interactions.jsonl
ml/data/review_queue.csv
ml/data/split_manifest.json
ml/interaction_data.py
ml/train_classifier.py
ml/notebooks/03_finetune.ipynb
ml/requirements.txt
scripts/prepare_interactions.py
scripts/package_day5.py
```

- [ ] Project folder is open and the virtual environment is active.
- [ ] All listed files exist. Use Eric's prepared working copy if they are not yet on GitHub.

## 2. Review the examples before training

There are **200 examples: 50 per label**. Each JSONL line is one example. Open the file in a text editor; keep each example on its own line.

| Label | ID | Meaning |
| --- | --- | --- |
| cooperation | 0 | Helping, gifting or working together |
| conflict | 1 | Threats, insults or an unresolved dispute |
| trade | 2 | Offering, negotiating, completing or politely declining an exchange |
| neutral | 3 | An ordinary statement/action without help, hostility or an exchange |

Review assignments:

| Reviewer | Example IDs |
| --- | --- |
| Aishani | 001–050 |
| Ethan | 051–100 |
| Gayatri | 101–200 |

For every assigned example:

1. Read its `text` and `label` in `ml/data/interactions.jsonl`.
2. Check the [full label policy](../ml/data/README.md). A free gift is cooperation; a polite rejected price is trade; a hostile trade dispute is conflict.
3. Correct wrong labels or unclear wording in that JSONL file. Keep the example ID unchanged. Rewrite ambiguous examples rather than guessing what someone intended.
4. Keep related versions in the same `scenario_family`. If two families describe the same situation, resolve the grouping before freezing; the checks require five examples per family and 50 per class.
5. Find the same ID in `ml/data/review_queue.csv`. Add any correction note and change `pending` to `approved` only after reviewing it.
6. If approved wording or labels change later, reset the row to `pending` and review it again.

Keep IDs such as `001` as three-digit text if editing the CSV in a spreadsheet. Combine all reviewers' corrections in Eric's working copy before the next step.

- [ ] All 200 examples have been reviewed by their assigned reviewer.
- [ ] All review rows are `approved`, and the corrected JSONL file is saved.

## 3. Check and freeze the reviewed dataset

**Eric, in Terminal:** after combining corrections, run:

```bash
python scripts/prepare_interactions.py --refresh-draft
```

This updates the draft fingerprint and checks IDs, labels, balance, duplicates and family grouping. Resolve errors before continuing. The candidate split must be:

| Split | Examples | Per class | Purpose |
| --- | --- | --- | --- |
| Training | 120 | 30 | Fit the model |
| Validation | 40 | 10 | Compare models and select the checkpoint |
| Test | 40 | 10 | Final evaluation on Day 6 |

All five examples from a scenario family stay in one split. Only interaction text goes into model features; IDs, family names and reviewer details are excluded.

Freeze once, after every review is complete:

```bash
python scripts/prepare_interactions.py --freeze
python scripts/prepare_interactions.py --require-frozen
```

The final report should include `"dataset_status": "frozen"` and `"reviews_remaining": 0`. Freezing records fingerprints of the exact data and review file so later edits are detected.

If the dataset is already frozen and `--require-frozen` passes, skip refreshing/freezing. Do not move examples between splits after seeing model results. Keep the held-out test set out of Day 5 model selection.

- [ ] Frozen-data check passes.
- [ ] The reviewed JSONL, review CSV and frozen manifest are preserved together.

## 4. Build the reviewed Colab package

**Eric, in Terminal:**

```bash
python scripts/package_day5.py --out /tmp/minidavis-day5-colab.zip
open /tmp
```

Find `minidavis-day5-colab.zip` in the Finder window. This package contains the data, training helper and notebook dependencies. Rebuild it after reviews/freezing; the earlier draft ZIP will correctly fail the training gate.

Give Gayatri these two files:

- `/tmp/minidavis-day5-colab.zip`
- `ml/notebooks/03_finetune.ipynb` from the project folder

- [ ] ZIP was built from the reviewed, frozen data.
- [ ] Gayatri has both files. Sharing the notebook alone does not share runtime files. [Colab explains file sharing here.](https://research.google.com/colaboratory/faq.html#drive)

## 5. Open the notebook in Colab

**Gayatri:**

1. Open [Google Colab](https://colab.research.google.com/) and sign in.
2. Choose **Upload notebook** from the File menu and select `03_finetune.ipynb`.
3. Connect to a runtime.
4. Open the left **Files** panel and upload `minidavis-day5-colab.zip` without unzipping it first.
5. Confirm the filename is exactly `minidavis-day5-colab.zip` in `/content`. Avoid a renamed duplicate such as `minidavis-day5-colab (1).zip`.

Use a fresh runtime when switching from a draft ZIP to a reviewed ZIP. The notebook reuses an existing extracted `MiniDavis` folder, so uploading a new ZIP alone will not replace that folder.

- [ ] Notebook opens and the ZIP is uploaded.

## 6. Run the dry run first

Leave the first code cell set to:

```python
RUN_TRAINING = False
INSTALL_DEPENDENCIES = False
```

Run the six code cells in order from top to bottom. This extracts the files, validates the dataset and skips installation/training.

Check the output:

- Project path is `/content/MiniDavis`.
- Examples = `200`, families = `40`.
- Training/validation/test counts are `120/40/40`.
- Dataset status is `frozen`, reviews remaining = `0` for the training-ready package.
- The final cell says the dry run is complete. No model or validation scores are produced yet.

You may use a draft package for a practice dry run, but it must be reviewed and frozen before Step 8.

- [ ] Gayatri can run all six default cells without errors.
- [ ] Eric confirms the other teammates can open the shared notebook and repeat the dry run with their own uploaded ZIP.

## 7. Select the training runtime

Choose **Runtime → Change runtime type** and select a GPU if available, then reconnect. Reupload the ZIP if the runtime changed and the files disappeared.

GPU access is not guaranteed. If unavailable, the helper uses CPU with a smaller batch size. Training time has not been measured for this project. Save outputs to Drive because Colab runtimes are temporary. [Colab resource and runtime limits](https://research.google.com/colaboratory/faq.html).

The helper's starting settings are:

| Setting | Value |
| --- | --- |
| Model | `distilbert/distilbert-base-uncased` |
| Epochs | 3 passes through the training data |
| Maximum input length | 128 tokens |
| Learning rate | `2e-5` |
| Training batch size | 8 on CUDA GPU, 4 on CPU |
| Checkpoint selection | Highest validation macro-F1 |

- [ ] Training runtime selected; ZIP is available again if needed.

## 8. Install dependencies and start training

Change the first code cell **in the Colab copy** to:

```python
RUN_TRAINING = True
INSTALL_DEPENDENCIES = True
```

Run cells individually in order:

1. **Setup:** finds/extracts the project and sets the training switches.
2. **Data check:** confirms the reviewed dataset counts and status.
3. **Install:** verifies frozen data first, then installs the pinned packages from `ml/requirements.txt`. If Colab requests a restart, restart and rerun in order. Keep the supplied PyTorch installation unless an actual error requires a change.
4. **Output folder:** mounts Google Drive. Complete the account authorization, then check the printed output path before proceeding. It should be `/content/drive/MyDrive/MiniDavis/Models/day5-v1`.
5. **Training:** fits the baseline, fine-tunes DistilBERT, selects the best validation checkpoint and exports results. Run this cell once per output folder.
6. **CPU reload:** reloads the exported model and predicts a label for one supplied example.

If the output-folder cell does not mount Drive, add a Colab cell containing `import google.colab`, run it, then rerun the output-folder cell. Confirm the Drive path before starting training. A local `ml/artifacts/` path inside Colab would be temporary.

For a later attempt, change the Colab output-folder cell to use a new Drive folder, such as `day5-v2`. Change the line assigning the `/content/drive/MyDrive/...` path. The training helper refuses a nonempty output directory to preserve earlier results.

Keep the repository notebook's switches set to `False`. Change only the Colab training copy so repository checks remain offline by default.

- [ ] Dependency installation succeeds.
- [ ] Drive output folder is confirmed.
- [ ] Training finishes and prints `"status": "training_completed"`.
- [ ] The CPU reload cell prints a predicted label and confidence.

## 9. Read the validation results

Open `metrics.json` in the Drive output folder.

Compare:

- `baseline.macro_f1`: TF-IDF + logistic regression, our simpler comparison model.
- `distilbert.macro_f1`: the selected fine-tuned DistilBERT checkpoint.
- `per_class`: how each model performs on cooperation, conflict, trade and neutral.
- `confusion_matrix`: rows are actual labels, columns are predicted labels, using the saved `label_order`.

Macro-F1 ranges from 0 to 1 and gives each class equal weight. Report the actual scores, including if DistilBERT performs worse than the simpler baseline. The report also records the device, package versions, training time and data fingerprints.

Check that `test_evaluated` is `false`. Day 5 results are validation results; Gayatri evaluates the fixed selected models on the held-out test set on Day 6. The supplied notebook does not implement that final test evaluation.

A confident prediction on one demonstration sentence is a loading check, not a model-quality score. This small synthetic dataset does not establish performance on real conversations.

- [ ] Both validation scores and the selected checkpoint are recorded.
- [ ] Held-out test evaluation remains reserved for Day 6.

## 10. Confirm and share the saved files

In Drive, open `MiniDavis/Models/day5-v1` (or the new run folder you chose). Confirm:

```text
day5-v1/
  classifier/
    config.json
    model.safetensors
    tokenizer files...
  baseline.joblib
  baseline-validation.json
  metrics.json
  split_manifest.json
  checkpoints/
```

Tokenizer filenames can vary. Keep the **entire** `classifier/` directory together. Its config maps numeric IDs to the four label names.

Gayatri shares the output-folder link with Eric and Rylee. Confirm they can open it and that the exported files remain available in Drive after the notebook session. Keep large model files in Drive; the project ignores model artifacts in Git.

Rylee will use the saved classifier for CPU predictions during Day 6 integration. That integration is a separate step; exporting the model does not automatically connect it to the town.

- [ ] Entire classifier folder and both metric files are saved.
- [ ] The exact frozen manifest is saved alongside them.
- [ ] Eric and Rylee can access the shared Drive folder.
- [ ] Notebook settings and observed results are saved with the run.

## If something fails

| Message/problem | What to do |
| --- | --- |
| `dataset is draft` | Complete assigned reviews, freeze locally, rebuild the ZIP, and use a fresh Colab runtime with the new ZIP. |
| `human reviews are incomplete` | Have the assigned reviewers finish their checks. Do not bypass the gate by bulk-approving rows. |
| `Dataset hash changed` | Before freezing, finish corrections and run `--refresh-draft`. After freezing, preserve the original version; coordinate a versioned replacement rather than editing it silently. |
| Missing ZIP or project files | Upload the exact ZIP filename into `/content`, then rerun the first cell. |
| Missing Python package/import error | Confirm the install cell completed. Follow a requested runtime restart, rerun setup, and record the full error if it persists. |
| Public Hugging Face token warning | A token is not required for this public checkpoint. If the download actually fails, check the network/error rather than adding a Groq key. |
| No GPU available | Continue on CPU if practical, or retry a later session. The helper chooses CPU batch size 4. |
| CUDA out of memory | Restart the runtime. Retry in a new output folder with training batch size 4 in `ml/train_classifier.py`, and record the setting. Do not alter the frozen data. |
| Output directory is not empty | Choose a new run folder, such as `day5-v2`, then retry. |
| Runtime disconnects | Check Drive for completed files. Partial checkpoints are not a completed export; use a new run folder for a fresh attempt. Automatic resume is not implemented. |
| Only baseline files appear | DistilBERT training/export did not finish. Read the error and retry in a new folder. |
| Prediction seems wrong | Keep the result and inspect validation metrics. Do not edit the test set to improve the result. |

**Day 5 is complete when reviewed data are frozen, training finishes, validation results are saved, and the exported classifier reloads on CPU.** Eric's local dry run alone does not satisfy that completion check.
