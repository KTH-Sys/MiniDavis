"""Package only Day 5 learning material for Colab; never include app secrets or weights."""

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "ml/interaction_data.py", "ml/train_classifier.py", "ml/requirements.txt", "ml/data/README.md",
    "ml/data/interactions.jsonl", "ml/data/split_manifest.json", "ml/data/review_queue.csv",
    "ml/notebooks/03_finetune.ipynb", "scripts/prepare_interactions.py",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(ROOT / name, "MiniDavis/" + name)
    print(f"Packaged {len(FILES)} learning files: {args.out}")


if __name__ == "__main__":
    main()
