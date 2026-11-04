"""Verify real CPU models against scripted engine events, with no provider calls."""
import argparse
import json
import platform
import resource
import sys
import tempfile
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app.classifier import InteractionClassifier
from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.memory import EventStore,minilm_embedder
from backend.app.schemas import RunTrace,StepRequest
from backend.app.world import World
from ml.interaction_data import fingerprint,validate_dataset
from fastapi.testclient import TestClient


def peak():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024*1024 if platform.system()=='Darwin' else 1024)


def verify(output):
    validate_dataset(ROOT/'ml/data',require_frozen=True)
    cfg=Settings()
    before=peak()
    embedder=minilm_embedder(cfg.embedding_model,cfg.embedding_cache_path,cfg.embedding_revision)
    if embedder is None:raise RuntimeError('Install semantic-memory dependencies first')
    embedder.warmup()
    classifier=InteractionClassifier(cfg.classifier_model_path).load()
    classifier.predict('Two neighbors exchange food for wood.')
    combined=peak()
    trace=RunTrace.model_validate_json((ROOT/'frontend/public/demo/sample-run.json').read_text())
    with tempfile.TemporaryDirectory(prefix='minidavis-presentation-') as tmp:
        store=EventStore(Path(tmp)/'events.sqlite',embedder=embedder)
        plans={}
        world=World(seed=trace.seed,store=store,classifier=classifier,context_planner=lambda a,s,m:plans[a.id])
        for i,operation in enumerate(trace.operations):
            state=world.snapshot()
            request=StepRequest(run_id=state.run_id,expected_revision=state.revision,request_id=f'fixture-{i}')
            if operation.kind=='shortage':world.shortage(request)
            else:
                plans={a.agent_id:a.action for a in operation.actions}
                world.step(request)
            assert world._digest()==operation.digest
        state=world.snapshot()
        labelled=[e for e in state.events if e.interaction_label and not e.event_id.endswith(':partner')]
        assert any(e.action=='accept_trade' for e in labelled) and any(e.action=='talk' for e in labelled)
        sources=[e for d in state.decisions.values() for e in d.memory.recent+d.memory.relevant]
        assert all(store.get(e.event_id)==e for e in sources)
        assert all(e.agent_id==agent for agent,d in state.decisions.items() for e in d.memory.recent+d.memory.relevant)
        assert all(d.memory.mode=='semantic' for d in state.decisions.values())
        original_digest=world._digest()
        world.reset(11)
        assert not world.snapshot().events and not world.inspect('ethan').retrieval.recent
        store.close()
        # Test real startup/readiness, without a Groq credential or network calls.
        strict=Settings(_env_file=None,memory_db_path=str(Path(tmp)/'api.sqlite'),memory_retrieval_mode='semantic',
            embedding_cache_path=cfg.embedding_cache_path,classifier_model_path=cfg.classifier_model_path,classifier_required=True)
        with TestClient(create_app(strict)) as client:
            ready=client.get('/ready').json()
            assert ready['classifier']=='loaded' and ready['classifier_required']
            a=client.get('/state').json();b=client.get('/state').json()
            assert a['run_id']==b['run_id'] and a['tick']==b['tick']==0
            prediction=client.post('/classify',json={'text':'Ethan gives Saurya spare food without asking for payment.'})
            assert prediction.status_code==200
            assert client.get('/state').json()==a
    report={'checked_on':'2026-11-04','passed':True,'fixture':True,'provider_calls':0,
        'fixture_description':'Scripted movement/trade/speech/shortage executed through real world rules and real classifier; not autonomous AI behavior',
        'model_sha256':fingerprint(Path(cfg.classifier_model_path)/'model.safetensors'),
        'classifier_loaded':True,'semantic_retrieval_verified':True,'sources_verified':True,'reset_isolation_verified':True,
        'strict_api_readiness':ready,'two_readers_same_run_no_turns':True,'final_factual_digest':original_digest,
        'real_cpu_api_prediction':prediction.json(),'classification_does_not_mutate_town':True,
        'labelled_events':[e.model_dump(mode='json') for e in labelled],
        'local_cpu_memory':{'platform':platform.platform(),'unit':'MiB process peak RSS',
            'before_models':before,'with_both_models':combined,'peak_after_api_check':peak()},
        'limits':'Local Mac CPU only; no hosted deployment or Linux RAM measurement claimed. Classifier labels may be wrong.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'labelled_events':len(labelled),'with_both_models_mib':combined},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'results/presentation/ml-integration.json')
    verify(parser.parse_args().out)
