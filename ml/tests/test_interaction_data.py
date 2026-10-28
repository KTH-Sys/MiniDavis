"""Prevent data leakage and accidental training on unreviewed examples."""

import csv
import json
import shutil
from pathlib import Path

import pytest

from ml.interaction_data import (
    create_manifest, read_examples, training_rows, validate_dataset,
)
from scripts.prepare_interactions import freeze_dataset

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def data(tmp_path):
    for name in ("interactions.jsonl", "split_manifest.json", "review_queue.csv"):
        shutil.copy(ROOT / "ml/data" / name, tmp_path / name)
    # Isolated draft fixtures keep these negative tests valid after the real
    # dataset is eventually reviewed/frozen. Never mutate repository reviews.
    rows = read_examples(tmp_path / "interactions.jsonl")
    (tmp_path / "split_manifest.json").write_text(json.dumps(create_manifest(rows, tmp_path / "interactions.jsonl")))
    path = tmp_path / "review_queue.csv"
    with path.open(newline="") as stream:
        reviews = list(csv.DictReader(stream))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["example_id", "reviewer", "status", "notes"])
        writer.writeheader()
        writer.writerows({**row, "status": "pending"} for row in reviews)
    return tmp_path


def edit_rows(data, edit):
    path = data / "interactions.jsonl"
    rows = read_examples(path)
    edit(rows)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return rows


def edit_manifest(data, edit):
    path = data / "split_manifest.json"
    manifest = json.loads(path.read_text())
    edit(manifest)
    path.write_text(json.dumps(manifest))


def approve_fixture(data):
    # Test copies only: this does not approve the committed examples.
    path = data / "review_queue.csv"
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["example_id", "reviewer", "status", "notes"])
        writer.writeheader()
        writer.writerows({**row, "status": "approved"} for row in rows)


def test_balanced_grouped_candidate_and_reproducibility(data):
    report = validate_dataset(data)
    assert report["examples"] == 200
    assert report["families"] == 40
    assert [report["splits"][name]["examples"] for name in ("train", "validation", "test")] == [120, 40, 40]
    assert set(report["splits"]["test"]["labels"].values()) == {10}
    rows = read_examples(data / "interactions.jsonl")
    manifest = json.loads((data / "split_manifest.json").read_text())
    assert create_manifest(list(reversed(rows)), data / "interactions.jsonl")["splits"] == manifest["splits"]


@pytest.mark.parametrize("edit, message", [
    (lambda rows: rows[1].update(example_id=rows[0]["example_id"]), "Duplicate example ID"),
    (lambda rows: rows[1].update(text=rows[0]["text"].upper() + "!!!"), "Duplicate normalized text"),
    (lambda rows: rows[0].update(label="friendly"), "Unknown label"),
    (lambda rows: rows.pop(), "Expected IDs"),
])
def test_rejects_bad_training_examples(data, edit, message):
    edit_rows(data, edit)
    with pytest.raises(ValueError, match=message):
        validate_dataset(data)


def test_rejects_changed_data_fingerprint(data):
    edit_rows(data, lambda rows: rows[0].update(text=rows[0]["text"] + " This happened today."))
    with pytest.raises(ValueError, match="hash changed"):
        validate_dataset(data)


def test_paraphrase_cannot_cross_splits_even_with_balanced_classes(data):
    def swap(manifest):
        ids = {row["example_id"]: row for row in read_examples(data / "interactions.jsonl")}
        train = manifest["splits"]["train"]
        test = manifest["splits"]["test"]
        i = next(i for i, key in enumerate(train) if ids[key]["label"] == "cooperation")
        j = next(j for j, key in enumerate(test) if ids[key]["label"] == "cooperation")
        train[i], test[j] = test[j], train[i]
    edit_manifest(data, swap)
    with pytest.raises(ValueError, match="family .* crosses splits"):
        validate_dataset(data)


def test_duplicate_split_id_is_rejected(data):
    edit_manifest(data, lambda m: m["splits"]["train"].append(m["splits"]["train"][0]))
    with pytest.raises(ValueError, match="Duplicate ID within"):
        validate_dataset(data)


def test_label_mapping_is_fixed(data):
    edit_manifest(data, lambda m: m["label2id"].update(cooperation=3))
    with pytest.raises(ValueError, match="Label mapping changed"):
        validate_dataset(data)


def test_unknown_split_id_is_rejected(data):
    edit_manifest(data, lambda m: m["splits"]["test"].__setitem__(0, "999"))
    with pytest.raises(ValueError, match="Unknown ID"):
        validate_dataset(data)


def test_draft_cannot_train_or_freeze_with_pending_reviews(data):
    before = (data / "split_manifest.json").read_bytes()
    with pytest.raises(ValueError, match="dataset is draft"):
        training_rows(data)
    with pytest.raises(ValueError, match="human review"):
        freeze_dataset(data)
    assert (data / "split_manifest.json").read_bytes() == before


def test_training_entrypoint_blocks_draft_before_import_or_download(data, tmp_path):
    from ml.train_classifier import run_training

    output = tmp_path / "models"
    with pytest.raises(ValueError, match="dataset is draft"):
        run_training(data, output)
    assert not output.exists()


def test_frozen_loader_never_returns_test_or_metadata_features(data):
    approve_fixture(data)
    assert freeze_dataset(data)["dataset_status"] == "frozen"
    rows = training_rows(data)
    assert set(rows) == {"train", "validation"}
    assert [len(rows[name]) for name in ("train", "validation")] == [120, 40]
    assert all(set(row) == {"text", "label"} for part in rows.values() for row in part)
    manifest = json.loads((data / "split_manifest.json").read_text())
    all_rows = {row["example_id"]: row for row in read_examples(data / "interactions.jsonl")}
    held_out = {all_rows[key]["text"] for key in manifest["splits"]["test"]}
    assert all(row["text"] not in held_out for part in rows.values() for row in part)
    with pytest.raises(ValueError, match="already frozen"):
        freeze_dataset(data)


def test_frozen_review_changes_block_training(data):
    approve_fixture(data)
    freeze_dataset(data)
    path = data / "review_queue.csv"
    path.write_text(path.read_text().replace("approved,", "approved,changed", 1))
    with pytest.raises(ValueError, match="review file changed"):
        training_rows(data)


def test_frozen_data_changes_block_training(data):
    approve_fixture(data)
    freeze_dataset(data)
    edit_rows(data, lambda rows: rows[0].update(text=rows[0]["text"] + " Changed."))
    with pytest.raises(ValueError, match="hash changed"):
        training_rows(data)


def test_wrong_reviewer_is_rejected(data):
    path = data / "review_queue.csv"
    path.write_text(path.read_text().replace("Aishani", "Eric", 1))
    with pytest.raises(ValueError, match="reviewer assignment"):
        validate_dataset(data)
