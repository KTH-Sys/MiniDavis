"""Execute the baseline cells of the two Day 1–3 notebooks; live cells stay opt-in."""

import contextlib
import io
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify():
    records=[]
    for name in ['01_agents.ipynb','02_rag.ipynb']:
        path=ROOT/'ml/notebooks'/name
        notebook=json.loads(path.read_text())
        namespace={'__name__':'__main__'}
        executed=0
        for index,cell in enumerate(notebook['cells']):
            if cell['cell_type']!='code':continue
            source=''.join(cell['source'])
            # The committed default deliberately keeps the real provider check off.
            if 'RUN_LIVE = True' in source:raise RuntimeError('Live notebook cell must default to False')
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(source,f'{name}:cell-{index}','exec'),namespace)
            executed+=1
        records.append({'notebook':name,'code_cells_executed':executed,'status':'passed','live_provider_calls':0})
    return records


if __name__=='__main__':
    os.chdir(ROOT)
    records=verify()
    out=ROOT/'results/day1-day3/notebooks.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))
