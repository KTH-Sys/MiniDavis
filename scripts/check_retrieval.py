"""Day 4: run the 10 frozen retrieval examples with real MiniLM embeddings.

Pass = at least 8 of 10 expected events appear in the top three relevant results.
Also runs the same events with paraphrased queries that share no words, which
keyword search cannot match. Needs: pip install -r backend/requirements-ml.txt
"""

import json
import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.memory import EventStore, minilm_embedder  # noqa: E402
from backend.app.schemas import Event  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PARAPHRASES = ["trees", "crops", "meal", "home", "shop", "city government building",
               "edge of the map", "timber", "tired", "east"]


def hits(store, queries):
    rows = []
    for tick, query in enumerate(queries, 1):
        memory = store.retrieve("fixture", "ethan", query, 10)
        top = [event.event_id for event in memory.relevant]
        rows.append({"query": query, "expected": f"fixture:{tick}:ethan", "top3": top,
                     "mode": memory.mode, "hit": f"fixture:{tick}:ethan" in top})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'results/day4/retrieval.json')
    args = parser.parse_args()
    embedder = minilm_embedder()
    if embedder is None:
        sys.exit("sentence-transformers is not installed: pip install -r backend/requirements-ml.txt")
    fixtures = json.loads((ROOT / "ml/data/retrieval_examples.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        store = EventStore(Path(tmp) / "check.sqlite", embedder=embedder)
        for tick, row in enumerate(fixtures, 1):
            store.save(Event(event_id=f"fixture:{tick}:ethan", run_id="fixture", agent_id="ethan",
                             tick=tick, action=row["action"], outcome=row["outcome"], text=row["text"]))
        frozen, paraphrased = hits(store, [row["query"] for row in fixtures]), hits(store, PARAPHRASES)
        store.close()
    semantic_verified = all(row['mode'] == 'semantic' for row in frozen + paraphrased)
    result = {"model": "sentence-transformers/all-MiniLM-L6-v2", "cache_key": embedder.cache_key,
              "semantic_verified": semantic_verified,
              "frozen_hits": sum(r["hit"] for r in frozen), "paraphrase_hits": sum(r["hit"] for r in paraphrased),
              "passed": semantic_verified and sum(r["hit"] for r in frozen) >= 8,
              "frozen": frozen, "paraphrased": paraphrased}
    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"frozen {result['frozen_hits']}/10, paraphrase {result['paraphrase_hits']}/10, "
          f"{'PASS' if result['passed'] else 'FAIL'} -> {out}")
    return 0 if result['passed'] else 1


if __name__ == "__main__":
    raise SystemExit(main())
