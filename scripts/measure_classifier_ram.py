
"""Measure CPU classifier memory usage on macOS."""

import resource
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.classifier import InteractionClassifier
from backend.app.config import Settings


def peak_ram_mb():
    # macOS reports ru_maxrss in bytes.
    return resource.getrusage(
        resource.RUSAGE_SELF
    ).ru_maxrss / (1024 * 1024)


def main():
    settings = Settings()
    model_dir = Path(settings.classifier_model_path)

    print(f"Classifier path: {model_dir}")

    before = peak_ram_mb()
    print(f"Peak RAM before loading: {before:.2f} MB")

    if not model_dir.is_dir():
        print("Status: Model not available yet")
        print("Classifier-loaded RAM: Not measured")
        return

    classifier = InteractionClassifier(model_dir).load()

    after = peak_ram_mb()
    print("Status: Classifier loaded on CPU")
    print(f"Peak RAM after loading: {after:.2f} MB")
    print(f"Increase in peak RAM: {after - before:.2f} MB")

    prediction = classifier.predict(
        "Two residents exchanged food for wood."
    )
    print(f"Sample prediction: {prediction}")


if __name__ == "__main__":
    main()
