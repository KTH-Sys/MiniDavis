# Interaction data — Day 5

`interactions.jsonl` contains **200 assistant-authored synthetic examples**, not recorded town events or human-reviewed ground truth. There are 50 examples per label and 40 scenario families, each with five related examples. These describe planned social interactions; they do not establish that talk/trade is implemented.

Only `text` is model input. Never include `label`, example IDs, reviewer names, scenario families or split names in model features. Class IDs are fixed: cooperation=0, conflict=1, trade=2, neutral=3.

## Label policy

- **cooperation:** voluntary help, gifts without payment, sharing useful information, or coordinating a shared task.
- **conflict:** explicit hostility, threats, accusations, intentional obstruction, or an unresolved dispute. This takes precedence if a trade is also mentioned.
- **trade:** a specific exchange, price negotiation, offer, acceptance, or polite refusal of an exchange. Payment can be food, wood or coins. A polite rejection is not itself conflict.
- **neutral:** factual observations, greetings, ordinary questions or independent actions without help, hostility or an exchange. Mentioning a market, gift or argument alone does not determine the label.

Label the observable interaction, not imagined intentions, positive/negative sentiment, an agent's personality, or whether a world action was legal. If two labels seem equally plausible, rewrite the text to resolve the ambiguity before approving it. Keep mutually related scenarios and paraphrases in one family; regroup them before freezing if reviewers discover related families. Changes must preserve the 120/40/40 split and class balance.

## Review and freeze

1. Aishani reviews 001–050, Ethan 051–100, Gayatri 101–200. Open `review_queue.csv`; each row starts `pending`.
2. Read the text in `interactions.jsonl`. Correct its `label` or wording there. Add a note in the CSV. Use `approved` only after the assigned reviewer has actually checked it; do not bulk-approve unreviewed rows. Reset a row to `pending` and review it again whenever its reviewed wording/label changes.
3. Run `python scripts/prepare_interactions.py`. This checks data/schema, normalized duplicates, IDs, labels, reviewer assignment, dataset fingerprint, balance and family isolation. Structural checks may inspect held-out data; do not use test examples for model/prompt selection.
4. After review edits, run `python scripts/prepare_interactions.py --refresh-draft` to update the candidate fingerprint and check all constraints. Once all 200 rows are approved, run `python scripts/prepare_interactions.py --freeze`. This binds the fixed split to the exact data, label mapping and review-file hashes. Commit the reviewed files together. The script refuses to replace an existing frozen split.
5. Open `ml/notebooks/03_finetune.ipynb`. Dry-run checks need no key, model download or ML dependencies. Training refuses draft, changed or unreviewed data. Gayatri enables training after reviews finish; use validation only for checkpoint selection.

The reproducible candidate split uses seed 20261029, assigns entire families, and has 30/10/10 examples per class in train/validation/test. The manifest is **not yet frozen**. Test metrics stay reserved for Day 6. Do not change assignments after inspecting model results. A substantive post-freeze change requires an explicitly versioned new dataset and manifest, rather than silently overwriting the old one.

Example: `python scripts/prepare_interactions.py --out results/day5/data-check.json` saves a metadata-only check report. `--require-frozen` checks the training gate without training. No command here calls Groq.

## Limits

This is a small, deliberately balanced synthetic teaching dataset. Five paraphrases in one family are not five independent situations. The 40 held-out examples cover only eight families. Scores will not establish generalization to real conversations or emergent behavior. Add independently collected, reviewed town interactions later and keep a separate evaluation set.
