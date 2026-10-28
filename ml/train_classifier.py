"""Opt-in Day 5 training. Test data are excluded from fitting and model selection."""

import importlib.metadata
import json
import platform
import time
from pathlib import Path

from ml.interaction_data import LABEL2ID, LABELS, SEED, fingerprint, training_rows

MODEL = "distilbert/distilbert-base-uncased"


def run_training(data_dir, output_dir):
    # Run before importing/downloading models or creating an output directory.
    splits = training_rows(data_dir)
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Use a new empty output directory; do not overwrite an earlier run")

    import joblib
    import numpy as np
    import torch
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    from sklearn.pipeline import make_pipeline
    from transformers import (
        AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
        Trainer, TrainingArguments, set_seed,
    )

    started = time.perf_counter()
    set_seed(SEED)
    output_dir.mkdir(parents=True, exist_ok=True)
    train, validation = splits["train"], splits["validation"]
    x_train, y_train = [r["text"] for r in train], [r["label"] for r in train]
    x_validation, y_validation = [r["text"] for r in validation], [r["label"] for r in validation]
    label_ids = list(range(len(LABELS)))

    def metrics(truth, predictions):
        return {
            "macro_f1": float(f1_score(truth, predictions, labels=label_ids, average="macro", zero_division=0)),
            "per_class": classification_report(truth, predictions, labels=label_ids,
                                                target_names=list(LABELS), output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(truth, predictions, labels=label_ids).tolist(),
            "label_order": list(LABELS), "examples": len(truth), "split": "validation",
        }

    # Fit vocabulary and weights on training text only, never validation/test text.
    baseline = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)),
                             LogisticRegression(max_iter=1000, random_state=SEED))
    baseline.fit(x_train, y_train)
    baseline_metrics = metrics(y_validation, baseline.predict(x_validation))
    joblib.dump(baseline, output_dir / "baseline.joblib")
    (output_dir / "baseline-validation.json").write_text(json.dumps(baseline_metrics, indent=2) + "\n")

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL, num_labels=len(LABELS), label2id=LABEL2ID,
        id2label={index: name for name, index in LABEL2ID.items()},
    )
    revision = getattr(model.config, "_commit_hash", None)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=revision)

    class Interactions(torch.utils.data.Dataset):
        def __init__(self, rows):
            self.encodings = tokenizer([r["text"] for r in rows], truncation=True, max_length=128)
            self.labels = [r["label"] for r in rows]

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, index):
            return {**{key: values[index] for key, values in self.encodings.items()},
                    "labels": self.labels[index]}

    use_gpu = torch.cuda.is_available()
    batch_size = 8 if use_gpu else 4
    args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"), learning_rate=2e-5,
        per_device_train_batch_size=batch_size, per_device_eval_batch_size=batch_size,
        num_train_epochs=3, eval_strategy="epoch", save_strategy="epoch",
        save_total_limit=2, load_best_model_at_end=True, metric_for_best_model="macro_f1",
        greater_is_better=True, seed=SEED, data_seed=SEED, report_to=[],
        use_cpu=not use_gpu, fp16=False, bf16=False,
    )

    def compute_metrics(prediction):
        logits = prediction.predictions
        if isinstance(logits, tuple):
            logits = logits[0]
        return {"macro_f1": metrics(prediction.label_ids, np.argmax(logits, axis=-1))["macro_f1"]}

    trainer = Trainer(
        model=model, args=args, train_dataset=Interactions(train), eval_dataset=Interactions(validation),
        processing_class=tokenizer, data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()
    # load_best_model_at_end has selected the checkpoint by validation macro-F1.
    predicted = trainer.predict(Interactions(validation))
    logits = predicted.predictions[0] if isinstance(predicted.predictions, tuple) else predicted.predictions
    classifier_metrics = metrics(y_validation, np.argmax(logits, axis=-1))
    classifier_dir = output_dir / "classifier"
    trainer.save_model(str(classifier_dir))
    tokenizer.save_pretrained(str(classifier_dir))
    manifest_path = Path(data_dir) / "split_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    report = {
        "status": "training_completed", "model": MODEL, "model_revision": revision,
        "dataset_sha256": manifest["dataset_sha256"], "manifest_sha256": fingerprint(manifest_path),
        "label2id": LABEL2ID, "seed": SEED, "max_length": 128, "learning_rate": 2e-5,
        "epochs": 3, "batch_size": batch_size, "device": "cuda" if use_gpu else "cpu",
        "selection_metric": "validation_macro_f1", "best_checkpoint": trainer.state.best_model_checkpoint,
        "baseline": baseline_metrics, "distilbert": classifier_metrics,
        "training_seconds": time.perf_counter() - started, "test_evaluated": False,
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in
                     ("torch", "transformers", "accelerate", "scikit-learn", "numpy")},
        "limitations": "Small synthetic teaching dataset; held-out evaluation is reserved for Day 6.",
    }
    (output_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    (output_dir / "split_manifest.json").write_text(manifest_path.read_text())
    return report
