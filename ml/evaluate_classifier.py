"""Evaluate a validation-selected export once on the frozen held-out test split."""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.interaction_data import LABELS, LABEL2ID, SEED, fingerprint, read_examples, validate_dataset
from backend.app.classifier import InteractionClassifier


def evaluate(model_dir, output):
    output = Path(output)
    if output.exists():
        raise ValueError('Test report already exists. Keep the original result; do not retune against test scores.')
    data = ROOT / 'ml/data'
    validate_dataset(data, require_frozen=True)
    manifest = json.loads((data / 'split_manifest.json').read_text())
    rows = {r['example_id']: r for r in read_examples(data / 'interactions.jsonl')}
    train = [rows[i] for i in manifest['splits']['train']]
    test = [rows[i] for i in manifest['splits']['test']]
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    import numpy as np
    baseline = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000, random_state=SEED))
    baseline.fit([r['text'] for r in train], [LABEL2ID[r['label']] for r in train])
    classifier = InteractionClassifier(model_dir).load()
    classifier.predict('Two neighbors exchange food for wood.')  # warmup, not a quality measurement
    predictions, times = [], []
    for row in test:
        start = time.perf_counter()
        result = classifier.predict(row['text'])
        times.append((time.perf_counter() - start) * 1000)
        predictions.append(LABEL2ID[result['label']])
    truth = [LABEL2ID[r['label']] for r in test]
    def metrics(predicted):
        return {'macro_f1': float(f1_score(truth, predicted, labels=list(range(4)), average='macro', zero_division=0)),
                'accuracy': float(accuracy_score(truth, predicted)),
                'per_class': classification_report(truth, predicted, labels=list(range(4)), target_names=list(LABELS), output_dict=True, zero_division=0),
                'confusion_matrix': confusion_matrix(truth, predicted, labels=list(range(4))).tolist()}
    report = {'evaluated_on': '2026-11-04', 'split': 'test', 'examples': len(test), 'label_order': list(LABELS),
              'dataset_sha256': manifest['dataset_sha256'], 'manifest_sha256': fingerprint(data/'split_manifest.json'),
              'model_sha256': fingerprint(Path(model_dir)/'model.safetensors'),
              'selection': 'Frozen export selected using validation before this test evaluation',
              'baseline': metrics(baseline.predict([r['text'] for r in test])), 'distilbert': metrics(predictions),
              'cpu_latency_ms': {'mean': float(np.mean(times)), 'p95': float(np.percentile(times, 95)), 'samples': len(times)},
              'predictions': [{'example_id': row['example_id'], 'true': row['label'], 'predicted': LABELS[p]} for row,p in zip(test,predictions)],
              'limitations': '40 synthetic grouped test examples; not proof of generalization to real conversations. Source checkpoint training fingerprint was unavailable; see continuation provenance.',
              'provider_calls': 0}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=ROOT/'ml/artifacts/classifier')
    parser.add_argument('--out', type=Path, default=ROOT/'results/presentation/classifier-test.json')
    args = parser.parse_args()
    report = evaluate(args.model, args.out)
    print(json.dumps({k:report[k] for k in ('examples','baseline','distilbert','cpu_latency_ms')}, indent=2))
