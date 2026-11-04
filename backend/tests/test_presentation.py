import hashlib
import json
from zipfile import ZipFile
import pytest
from fastapi.testclient import TestClient
from backend.app.config import Settings
from backend.app.main import create_app
from scripts.install_classifier import install
from scripts.run_eval import run_episode


def test_classifier_requires_a_loaded_model_and_operator_when_protected(tmp_path):
    cfg=Settings(_env_file=None,memory_db_path=str(tmp_path/'events.sqlite'),classifier_model_path=str(tmp_path/'missing'),operator_token='fixture')
    with TestClient(create_app(cfg)) as client:
        before=client.get('/state').json()
        assert client.post('/classify',json={'text':'Neighbors exchange food.'}).status_code==401
        response=client.post('/classify',headers={'X-Operator-Token':'fixture'},json={'text':'Neighbors exchange food.'})
        assert response.status_code==503
        assert client.get('/state').json()==before


def test_shortage_evaluation_changes_stock_without_provider_calls():
    report=run_episode('baseline',11,'shortage',35,Settings(_env_file=None))
    assert report['provider_calls']==0 and report['invariant_failures']==0
    assert report['before_planning']['revision']==31
    assert next(r['stock'] for r in report['before_planning']['resources'] if r['id']=='farm')<=5
    assert sum(report['decisions'].values())==35*5


@pytest.mark.parametrize('name',['../outside.txt','/outside.txt','classifier/evil.py'])
def test_model_installer_rejects_unexpected_paths_before_writing(tmp_path,name):
    archive=tmp_path/'bad.zip'
    with ZipFile(archive,'w') as z:z.writestr(name,b'bad')
    destination=tmp_path/'model'
    with pytest.raises(ValueError):install(archive,destination)
    assert not destination.exists()


def test_model_installer_rejects_corrupted_weights_before_writing(tmp_path):
    archive=tmp_path/'corrupt.zip'
    files={'classifier/config.json':json.dumps({'id2label':{'0':'cooperation','1':'conflict','2':'trade','3':'neutral'}}).encode(),
           'classifier/tokenizer.json':b'{}','classifier/model.safetensors':b'corrupted'}
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    dataset=json.loads((root/'ml/data/split_manifest.json').read_text())['dataset_sha256']
    manifest={'version':1,'dataset_sha256':dataset,'files':{n:hashlib.sha256(v).hexdigest() for n,v in files.items()}}
    manifest['files']['classifier/model.safetensors']='0'*64
    with ZipFile(archive,'w') as z:
        for n,v in files.items():z.writestr(n,v)
        z.writestr('export-manifest.json',json.dumps(manifest))
    destination=tmp_path/'model'
    with pytest.raises(ValueError,match='checksum'):install(archive,destination)
    assert not destination.exists()
