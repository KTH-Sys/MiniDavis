"""Validate a MiniDavis model package before installing its inference-only files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MODEL_FILES={'config.json','model.safetensors','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt'}
EXPECTED={'0':'cooperation','1':'conflict','2':'trade','3':'neutral'}


def install(archive_path,destination):
    destination=Path(destination)
    with zipfile.ZipFile(archive_path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or len(names)>12 or sum(i.file_size for i in archive.infolist())>400_000_000:
            raise ValueError('Invalid or oversized model package')
        for name in names:
            member=Path(name)
            if member.is_absolute() or '..' in member.parts or '\\' in name:
                raise ValueError('Unsafe archive path')
            if name!='export-manifest.json' and name not in {'classifier/'+n for n in MODEL_FILES} | {'results/classifier-validation.json','results/classifier-test.json'}:
                raise ValueError('Unexpected package file')
        manifest=json.loads(archive.read('export-manifest.json'))
        if manifest.get('version')!=1 or set(manifest.get('files',{}))!=set(names)-{'export-manifest.json'}:
            raise ValueError('Invalid export manifest')
        if not {'classifier/config.json','classifier/model.safetensors','classifier/tokenizer.json'} <= set(names):
            raise ValueError('Incomplete classifier package')
        for name,expected in manifest['files'].items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=expected:raise ValueError('Model package checksum mismatch')
        if json.loads(archive.read('classifier/config.json')).get('id2label')!=EXPECTED:
            raise ValueError('Wrong MiniDavis label mapping')
        frozen=json.loads((ROOT/'ml/data/split_manifest.json').read_text())
        if manifest.get('dataset_sha256')!=frozen['dataset_sha256']:raise ValueError('Model dataset version mismatch')
        if destination.exists() and any(destination.iterdir()):
            if all((destination/Path(name).name).is_file() and hashlib.sha256((destination/Path(name).name).read_bytes()).hexdigest()==sha
                   for name,sha in manifest['files'].items() if name.startswith('classifier/')):
                return 'Already installed and verified'
            raise ValueError('Destination contains a different model; choose a new empty folder')
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
            stage=Path(tmp)/'classifier';stage.mkdir()
            for name in names:
                if name.startswith('classifier/'):(stage/Path(name).name).write_bytes(archive.read(name))
            (stage/'export-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            if destination.exists():destination.rmdir() # empty only; never deletes existing weights
            shutil.move(str(stage),str(destination))
    return 'Classifier installed and verified'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--destination',type=Path,default=ROOT/'ml/artifacts/classifier')
    args=parser.parse_args();print(install(args.archive,args.destination))
