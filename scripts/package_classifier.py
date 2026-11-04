"""Create a portable, checksummed inference export; weights stay outside Git."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ml.interaction_data import validate_dataset

ALLOWED={'config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt'}


def package(model, output):
    validate_dataset(ROOT/'ml/data',require_frozen=True)
    model,output=Path(model),Path(output)
    files={'classifier/'+p.name:p.read_bytes() for p in model.iterdir() if p.name in ALLOWED and p.is_file()}
    if not {'classifier/config.json','classifier/model.safetensors','classifier/tokenizer.json'} <= files.keys():
        raise ValueError('A complete safetensors model and tokenizer are required')
    for name in ['classifier-validation.json','classifier-test.json']:
        path=ROOT/'results/presentation'/name
        if path.is_file():files['results/'+name]=path.read_bytes()
    manifest={'version':1,'model':'distilbert/distilbert-base-uncased','dataset_sha256':json.loads((ROOT/'ml/data/split_manifest.json').read_text())['dataset_sha256'],
              'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
        archive.writestr('export-manifest.json',json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,default=ROOT/'ml/artifacts/classifier')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();report=package(args.model,args.out)
    print(f'Packaged {len(report["files"])} files: {args.out}')
