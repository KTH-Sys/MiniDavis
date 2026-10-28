"""Offline dataset checks and immutable, reviewed training-input gates."""

import csv
import hashlib
import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ("cooperation", "conflict", "trade", "neutral")
LABEL2ID = {name: index for index, name in enumerate(LABELS)}
SEED = 20261029
SPLIT_FAMILIES = {"train": 6, "validation": 2, "test": 2}


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reviewer(example_id):
    number = int(example_id)
    return "Aishani" if number <= 50 else "Ethan" if number <= 100 else "Gayatri"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def normalized_text(text):
    return re.sub(r"[\W_]+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def read_examples(path):
    examples = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {number}") from exc
        require(isinstance(row, dict), f"Line {number}: expected an object")
        require(set(row) == {"example_id", "text", "label", "scenario_family"},
                f"Line {number}: unexpected or missing fields")
        require(all(isinstance(value, str) and value.strip() for value in row.values()),
                f"Line {number}: fields must be nonempty strings")
        require(bool(re.fullmatch(r"\d{3}", row["example_id"])), "Invalid example ID")
        require(row["label"] in LABELS, f"Unknown label at {row['example_id']}")
        require(20 <= len(row["text"]) <= 700, f"Text length at {row['example_id']}")
        examples.append(row)
    return examples


def validate_examples(examples):
    ids = [row["example_id"] for row in examples]
    require(len(ids) == len(set(ids)), "Duplicate example ID")
    require(set(ids) == {f"{n:03}" for n in range(1, 201)}, "Expected IDs 001–200")
    normalized = [normalized_text(row["text"]) for row in examples]
    require(len(normalized) == len(set(normalized)), "Duplicate normalized text")
    require(Counter(row["label"] for row in examples) == {label: 50 for label in LABELS},
            "Expected 50 examples per class")
    families = defaultdict(list)
    for row in examples:
        families[row["scenario_family"]].append(row)
    require(len(families) == 40, "Expected 40 scenario families")
    for name, rows in families.items():
        require(len(rows) == 5, f"Family {name} must contain five examples")
        require(len({row["label"] for row in rows}) == 1,
                f"Family {name} has mixed labels; regroup before freezing")
    return families


def create_manifest(examples, dataset_path):
    families = validate_examples(examples)
    rng = random.Random(SEED)
    assignments = {name: [] for name in SPLIT_FAMILIES}
    for label in LABELS:
        names = sorted(name for name, rows in families.items() if rows[0]["label"] == label)
        rng.shuffle(names)
        start = 0
        for split, count in SPLIT_FAMILIES.items():
            chosen = names[start:start + count]
            assignments[split].extend(row["example_id"] for name in chosen for row in families[name])
            start += count
    return {
        "schema_version": 1, "dataset_version": "minidavis-synthetic-v1",
        "seed": SEED, "status": "draft", "label2id": LABEL2ID,
        "dataset_sha256": fingerprint(dataset_path),
        "splits": {split: sorted(ids) for split, ids in assignments.items()},
    }


def read_reviews(path, examples):
    with Path(path).open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == ["example_id", "reviewer", "status", "notes"],
                "Review CSV columns are invalid")
        reviews = list(reader)
    ids = [row["example_id"] for row in reviews]
    require(len(ids) == len(set(ids)), "Duplicate review ID")
    require(set(ids) == {row["example_id"] for row in examples}, "Missing/extra review IDs")
    for row in reviews:
        require(row["reviewer"] == reviewer(row["example_id"]), "Incorrect reviewer assignment")
        require(row["status"] in {"pending", "changes_requested", "approved"}, "Unknown review status")
        require(isinstance(row["notes"], str), "Malformed review row")
        require(set(row) == {"example_id", "reviewer", "status", "notes"}, "Malformed review row")
    return reviews


def validate_dataset(data_dir, require_frozen=False):
    data_dir = Path(data_dir)
    path = data_dir / "interactions.jsonl"
    examples = read_examples(path)
    families = validate_examples(examples)
    manifest = json.loads((data_dir / "split_manifest.json").read_text())
    require(manifest.get("schema_version") == 1, "Unknown manifest schema")
    require(manifest.get("dataset_version") == "minidavis-synthetic-v1", "Unknown dataset version")
    require(manifest.get("seed") == SEED, "Unexpected split seed")
    require(manifest.get("status") in {"draft", "frozen"}, "Unknown manifest status")
    require(manifest.get("label2id") == LABEL2ID, "Label mapping changed")
    require(manifest.get("dataset_sha256") == fingerprint(path), "Dataset hash changed; regenerate draft manifest after review edits")
    splits = manifest.get("splits", {})
    require(set(splits) == set(SPLIT_FAMILIES), "Expected train/validation/test splits")
    lookup = {row["example_id"]: row for row in examples}
    seen, family_split, summary = set(), {}, {}
    for split, family_count in SPLIT_FAMILIES.items():
        ids = splits[split]
        require(isinstance(ids, list) and all(isinstance(i, str) for i in ids), "Split IDs must be strings")
        require(len(ids) == len(set(ids)), f"Duplicate ID within {split}")
        require(set(ids) <= lookup.keys(), f"Unknown ID in {split}")
        require(not seen.intersection(ids), "Example crosses splits")
        seen.update(ids)
        rows = [lookup[i] for i in ids]
        counts = Counter(row["label"] for row in rows)
        require(counts == {label: family_count * 5 for label in LABELS}, f"Class balance in {split} is wrong")
        for row in rows:
            family = row["scenario_family"]
            require(family_split.setdefault(family, split) == split,
                    f"Scenario family {family} crosses splits")
        summary[split] = {"examples": len(rows), "families": len({r["scenario_family"] for r in rows}), "labels": dict(counts)}
    require(seen == lookup.keys(), "Split manifest does not cover all examples")
    expected = create_manifest(examples, path)["splits"]
    require(splits == expected, "Split assignments differ from the reproducible grouped split")
    reviews = read_reviews(data_dir / "review_queue.csv", examples)
    pending = sum(row["status"] != "approved" for row in reviews)
    if require_frozen or manifest["status"] == "frozen":
        require(manifest["status"] == "frozen", "Training blocked: dataset is draft; finish reviews and freeze")
        require(pending == 0, "Training blocked: human reviews are incomplete")
        require(manifest.get("reviews_sha256") == fingerprint(data_dir / "review_queue.csv"),
                "Frozen review file changed")
    return {
        "status": "passed", "dataset_status": manifest["status"], "examples": len(examples),
        "families": len(families), "splits": summary, "reviews_remaining": pending,
        "dataset_sha256": manifest["dataset_sha256"], "held_out_model_evaluations": 0,
    }


def training_rows(data_dir):
    """Return training/validation input only after exact reviewed data are frozen."""
    validate_dataset(data_dir, require_frozen=True)
    data_dir = Path(data_dir)
    rows = {row["example_id"]: row for row in read_examples(data_dir / "interactions.jsonl")}
    manifest = json.loads((data_dir / "split_manifest.json").read_text())
    return {
        split: [{"text": rows[i]["text"], "label": LABEL2ID[rows[i]["label"]]} for i in manifest["splits"][split]]
        for split in ("train", "validation")
    }
