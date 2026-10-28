"""Run notebook defaults offline; training/downloads must remain explicitly opt-in."""

import ast
import contextlib
import io
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify():
    notebook = json.loads((ROOT / "ml/notebooks/03_finetune.ipynb").read_text())
    namespace = {"__name__": "__main__"}
    output = io.StringIO()
    executed = 0
    previous = Path.cwd()
    trees = []
    # Check every cell before executing any, so an enabled training switch in
    # a later cell cannot trigger a download before verification rejects it.
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        tree = ast.parse("".join(cell["source"]))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in {"RUN_TRAINING", "INSTALL_DEPENDENCIES"}:
                        if not isinstance(node.value, ast.Constant) or node.value.value is not False:
                            raise ValueError(f"{target.id} must default to False")
        trees.append((index, tree))
    try:
        os.chdir(ROOT)
        for index, tree in trees:
            with contextlib.redirect_stdout(output):
                exec(compile(tree, f"03_finetune.ipynb:cell-{index}", "exec"), namespace)
            executed += 1
    finally:
        os.chdir(previous)
    if namespace.get("RUN_TRAINING") is not False or namespace.get("INSTALL_DEPENDENCIES") is not False:
        raise ValueError("Notebook must be a dry run by default")
    return {"notebook": "03_finetune.ipynb", "status": "passed", "code_cells_executed": executed,
            "training_executed": False, "model_downloads": 0, "provider_calls": 0,
            "held_out_model_evaluations": 0, "scope": "Offline defaults only; Colab training branch not executed"}


if __name__ == "__main__":
    report = verify()
    path = ROOT / "results/day5/notebook-check.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
