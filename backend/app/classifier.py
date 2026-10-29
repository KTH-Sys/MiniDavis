
from pathlib import Path

class InteractionClassifier:
    def __init__(self, model_dir):
        self.model_dir = Path(model_dir)
        self.model = None
        self.tokenizer = None

    def load(self):
        if not self.model_dir.is_dir():
            raise FileNotFoundError(
                f"Classifier not found: {self.model_dir}"
            )

        import torch
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
        )
        self.model.to("cpu")
        self.model.eval()
        return self

    def predict(self, text):
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Classifier has not been loaded")

        import torch

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
        )

        with torch.inference_mode():
            logits = self.model(**inputs).logits
            probabilities = torch.softmax(logits, dim=-1)

        confidence, index = probabilities.max(dim=-1)
        label = self.model.config.id2label[index.item()]

        return {
            "label": label,
            "confidence": round(confidence.item(), 4),
        }
