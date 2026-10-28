"""Check draft data, refresh a draft after edits, or freeze approved data. No ML calls."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.interaction_data import (  # noqa: E402
    create_manifest, fingerprint, read_examples, read_reviews, require, validate_dataset,
)


def freeze_dataset(data_dir):
    data_dir = Path(data_dir)
    path = data_dir / "split_manifest.json"
    manifest = json.loads(path.read_text())
    require(manifest.get("status") == "draft", "Refusing to overwrite an already frozen split")
    validate_dataset(data_dir)
    reviews = read_reviews(data_dir / "review_queue.csv", read_examples(data_dir / "interactions.jsonl"))
    require(all(row["status"] == "approved" for row in reviews), "Finish every assigned human review before freezing")
    manifest["status"] = "frozen"
    manifest["reviews_sha256"] = fingerprint(data_dir / "review_queue.csv")
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return validate_dataset(data_dir, require_frozen=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "ml/data")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--freeze", action="store_true")
    action.add_argument("--refresh-draft", action="store_true", help="Regenerate draft hash/grouped split after review edits; never use after results")
    parser.add_argument("--require-frozen", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        if args.refresh_draft:
            path = args.data_dir / "split_manifest.json"
            current = json.loads(path.read_text())
            require(current.get("status") == "draft", "Refusing to modify a frozen split")
            rows = read_examples(args.data_dir / "interactions.jsonl")
            read_reviews(args.data_dir / "review_queue.csv", rows)
            path.write_text(json.dumps(create_manifest(rows, args.data_dir / "interactions.jsonl"), indent=2) + "\n")
        report = freeze_dataset(args.data_dir) if args.freeze else validate_dataset(args.data_dir, args.require_frozen)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, f"Dataset check failed: {exc}\n")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
