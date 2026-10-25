# Ethan — Day 4 semantic retrieval

Implemented October 24, 2026, on top of Eric's Day 3–4 integration.

## What changed

- `EventStore(path, embedder=...)` ranks relevant memories with MiniLM (`sentence-transformers/all-MiniLM-L6-v2`, CPU) by cosine similarity. SQL still filters run, resident and observation tick **before** ranking, so isolation is unchanged.
- Each event is embedded once. Vectors are cached in a SQLite `embeddings` table and reused after a restart.
- If the model is missing or fails, retrieval falls back to Eric's keyword search (`mode: "lexical"`). The new mode `"semantic"` is shown in the inspector as "MiniLM meaning search".
- MiniLM is optional: `pip install -r backend/requirements-ml.txt`. The base `requirements.txt` and CI stay light (no PyTorch).
- Prompt size: Aishani's `build_input` already drops whole memories to stay inside `LLM_MAX_INPUT_TOKENS`, so no extra truncation was added.

## Verification

- `python -m pytest backend/tests -q`: 64 passed. New tests in `test_memory.py` prove meaning-based ranking, embedding caching and the keyword fallback, using a fake embedder (no download).
- `python scripts/check_retrieval.py` with real MiniLM: frozen examples 10/10 expected events in the top three (gate is 8/10). Paraphrased queries sharing no words with the event (e.g. "timber" → "two logs") 10/10. See [results](../results/day4/retrieval.json).
- With 10 events per query, top three is an easy bar; this is a smoke check, not a benchmark.
- In-app check: after 10 ticks the inspector shows `semantic` mode, five recent and three relevant events with real IDs.

## Notes for the team

- First use downloads about 90 MB of model weights from Hugging Face (free, no key), then caches them.
- Deploy RAM: PyTorch + MiniLM adds a few hundred MB; Eric/Rylee should measure it before choosing a backend size.
- Public-event visibility rules are not added yet: every event is still resident-private.
