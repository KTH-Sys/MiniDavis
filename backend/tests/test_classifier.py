
import pytest

from backend.app.classifier import InteractionClassifier

def test_missing_classifier_raises_error(tmp_path):
    missing_dir = tmp_path / "missing-classifier"

    classifier = InteractionClassifier(missing_dir)

    with pytest.raises(
        FileNotFoundError,
        match="Classifier not found",
    ):
        classifier.load()


def test_predict_before_loading_raises_error(tmp_path):
    classifier = InteractionClassifier(tmp_path)

    with pytest.raises(
        RuntimeError,
        match="Classifier has not been loaded",
    ):
        classifier.predict("Two residents traded food for wood")
