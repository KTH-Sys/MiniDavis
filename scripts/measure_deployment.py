"""Measure actual CPU process peak RAM; never invent missing classifier measurements."""
import json
import platform
import resource
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from backend.app.config import Settings
from backend.app.classifier import InteractionClassifier
from backend.app.memory import minilm_embedder


def peak_mb():
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024*1024 if platform.system() == 'Darwin' else 1024)


def main():
    settings = Settings()
    report = {'platform':platform.platform(), 'unit':'MiB process peak RSS',
              'before_optional_models_mb':peak_mb(), 'classifier_loaded':False,
              'combined_models_measured':False, 'provider_calls':0, 'blockers':[]}
    embedder = minilm_embedder(settings.embedding_model,settings.embedding_cache_path,settings.embedding_revision)
    if embedder:
        embedder.warmup(); embedder(['Two residents exchanged food for wood.'])
        report['with_minilm_mb'] = peak_mb()
    else:
        report['blockers'].append('MiniLM dependencies are not installed')
    if (Path(settings.classifier_model_path)/'config.json').is_file():
        classifier = InteractionClassifier(settings.classifier_model_path).load()
        classifier.predict('Two residents exchanged food for wood.')
        report['classifier_loaded'] = True
        report['combined_models_measured'] = embedder is not None
        report['with_optional_models_mb'] = peak_mb()
    else:
        report['blockers'].append('Gayatri has not supplied the trained classifier export')
    report['full_ml_hosting_ready'] = report['combined_models_measured']
    out=ROOT/'results/eric-aishani-day7/deployment-memory.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
