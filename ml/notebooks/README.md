# MiniDavis learning notebooks

- `01_agents.ipynb`: world decisions and opt-in hosted Groq planning.
- `02_rag.ipynb`: stored events, private memories and semantic retrieval.
- `03_finetune.ipynb`: data checks, opt-in DistilBERT training, validation and export.

All notebook defaults remain offline-safe. Run `python scripts/verify_notebooks.py` and `python scripts/check_day5_notebook.py` from the repository root to check them. Live agent cells need a server/Colab Groq key; the classifier training notebook does not.

**November 4:** the data is reviewed/frozen. The completed presentation classifier continues Gayatri's saved epoch-1 checkpoint for two additional epochs; its selected export and held-out results are recorded separately. See the [model card](../../docs/model-card.md) and [training walkthrough](../../docs/train_DistilBERT.md). The default notebook itself does not run final held-out evaluation; `ml/evaluate_classifier.py` provides that separate, explicit step.

For a fresh Colab training run, package the frozen data with `scripts/package_day5.py`, upload that ZIP, and change training switches only in your Colab copy. Keep test data out of model selection, save artifacts outside the temporary runtime, and preserve the original report after final evaluation. Weights are shared separately from Git.
