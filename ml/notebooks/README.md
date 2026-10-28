# Shared notebooks

For the full DistilBERT walkthrough, follow [the training instructions](../../docs/train_DistilBERT.md): review data, freeze the split, upload to Colab, train, inspect validation results and save the model.

Aishani adds `01_agents.ipynb` (baseline and Groq decisions); Ethan adds
`02_rag.ipynb` (event storage and retrieval); Gayatri adds `03_finetune.ipynb`
(reviewed data, grouped splits, training and export). Start from the technical guide.
Keep credentials in Colab Secrets and save checkpoints outside the runtime.

`01_agents.ipynb` and `02_rag.ipynb` now run the Day 1–3 baseline checks locally or in Colab. Verify their default cells with `python scripts/verify_notebooks.py` from the repository root. The live agent cell is off by default and needs the server/Colab `LLM_API_KEY`; it makes up to five calls and saves genuine per-resident results. Run it once for the team after reserving the allowance.

The baseline notebook execution report is in `results/day1-day3/notebooks.json`. Real provider verification remains pending until a key is configured.

`03_finetune.ipynb` now provides Eric's Day 5 handoff: offline data checks, explicit training switches, TF-IDF/logistic-regression baseline, DistilBERT training selected by validation macro-F1, export, and CPU reload smoke check. **Only its six default dry-run cells have been executed.** No ML dependencies/model files were downloaded, and no Colab/GPU training or fine-tuned weights are claimed. Both switches default to False. The training path requires approved reviews and an exact frozen split; it never evaluates test examples.

Run `python scripts/check_day5_notebook.py` and see `results/day5/notebook-check.json`. Read [the data policy](../data/README.md) before approving examples. Package a self-contained Colab upload with `python scripts/package_day5.py --out /tmp/minidavis-day5-colab.zip`. Upload that ZIP in Colab and open the notebook; no provider API key is needed. Rebuild the ZIP after reviews/freeze so Colab receives the reviewed version. Save artifacts to Drive. See [Eric's handoff](../../docs/eric-day5.md) for exact remaining actions.
