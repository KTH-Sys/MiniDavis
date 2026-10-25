# Shared notebooks

Aishani adds `01_agents.ipynb` (baseline and Groq decisions); Ethan adds
`02_rag.ipynb` (event storage and retrieval); Gayatri adds `03_finetune.ipynb`
(reviewed data, grouped splits, training and export). Start from the technical guide.
Keep credentials in Colab Secrets and save checkpoints outside the runtime.

`01_agents.ipynb` and `02_rag.ipynb` now run the Day 1–3 baseline checks locally or in Colab. Verify their default cells with `python scripts/verify_notebooks.py` from the repository root. The live agent cell is off by default and needs the server/Colab `LLM_API_KEY`; it makes up to five calls and saves genuine per-resident results. Run it once for the team after reserving the allowance.

The baseline notebook execution report is in `results/day1-day3/notebooks.json`. Real provider verification remains pending until a key is configured. The fine-tuning notebook and trained classifier remain Day 5 work; no training run or fine-tuned weights are claimed.
