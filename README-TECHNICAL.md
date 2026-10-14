# MiniDavis — Technical Guide and Checklists

Use [README.md](README.md) for who does what on each date. This guide defines the implementation and exact checks.

**Day 1:** Create the starter application, notebooks, fixtures, and test commands specified below. Run the commands after creating their corresponding files. Complete each checkbox only after observing the required result.

## 1. Fixed responsibilities

| Person | Build and check | Collaboration |
| --- | --- | --- |
| Eric | Project structure, integration, release checks | Help Saurya with frontend and Rylee with backend |
| Saurya | React town, controls, inspector, event log | Work with Eric and Rylee on API connections |
| Rylee | FastAPI world, validation, trading, replay | Work with Eric and Saurya on state and controls |
| Aishani | Agent notebook, planner, prompts, fallback | Work with Ethan on memory-aware decisions |
| Ethan | Event store, RAG, retrieval/isolation checks | Work with Aishani and Rylee on observations/events |
| Gayatri | Dataset, training notebook, model, evaluation | Work with Eric on shared sessions and reports |

Everyone participates in agents on Day 3, RAG on Day 4, and fine-tuning on Day 5. These are shared learning sessions, not isolated assignments.

## 2. Day 0: accounts and collaboration only

### Eric

- [ ] Sign in to GitHub and create a repository named `MiniDavis`.
- [ ] Add Ethan, Gayatri, Aishani, Rylee, and Saurya as collaborators using their actual usernames.
- [ ] Grant the team access to the existing Notion project.
- [ ] Record repo, Notion, Drive, and Colab links in one shared location.
- [ ] Confirm the LLM provider/model and a project budget with Aishani.

### Saurya

- [ ] Sign in to GitHub and accept the repository invitation.
- [ ] Open the repository and the shared Notion project.
- [ ] Confirm that the shared links are visible.

### Rylee

- [ ] Sign in to GitHub and accept the repository invitation.
- [ ] Open Ethan’s shared Drive folder.
- [ ] Confirm GitHub and Drive access.

### Aishani

- [ ] Sign in to the agreed LLM-provider account or authorized project.
- [ ] Confirm with Eric who controls the API credential and budget.
- [ ] Record the provider/model name; keep the credential out of GitHub, Notion, and chat.

### Ethan

- [ ] Create a Drive folder named `MiniDavis`.
- [ ] Give the five teammates access through their actual Google accounts.
- [ ] Add empty `Notebooks`, `Data`, `Models`, and `Results` folders.

### Gayatri

- [ ] Sign in to Google Colab.
- [ ] Create an empty `MiniDavis Setup` notebook in the shared folder.
- [ ] Check that every teammate can open the notebook.

**Day 0 gate:** All six people have the required access. Do not install project dependencies, design the town, label data, or train models today.

## 3. Day 1: create the starter project

Eric creates the shared folders and configuration. Rylee builds the FastAPI state/reset endpoints; Saurya builds the React town; Aishani creates baseline decisions; Ethan creates the event store; Gayatri adds starter tests. Commit a runnable baseline starter with pinned Python dependencies and a frontend lockfile.

```text
MiniDavis/
  README.md
  README-TECHNICAL.md
  .gitignore
  backend/
    .env.example
    requirements.txt
    app/
      __init__.py
      main.py
      schemas.py
      world.py
      agents.py
      memory.py
      classifier.py
      replay.py
    tests/
      test_world.py
      test_api.py
      test_agents.py
      test_memory.py
      test_trade.py
      test_replay.py
  frontend/
    .env.example
    package.json
    package-lock.json
    src/
      App.tsx
      api.ts
      components/
        TownMap.tsx
        Controls.tsx
        ResidentInspector.tsx
        EventLog.tsx
  ml/
    requirements.txt
    notebooks/
      01_agents.ipynb
      02_rag.ipynb
      03_finetune.ipynb
    data/
      interactions.jsonl
      split_manifest.json
    artifacts/
  scripts/
    run_eval.py
  results/
  demo/
```

Ignore `.venv`, `.env`, `node_modules`, local SQLite files, and large model weights in Git. Store model weights in the shared Models folder. Notebook outputs must not contain credentials.

### Install and start after creating the starter

Use Python 3.11 and a supported Node.js LTS version meeting the frontend’s requirements. Vite currently documents Node 20.19+ or 22.12+; use Node 22.12+ or a newer supported LTS. Follow the committed lockfile rather than upgrading packages independently. See [Vite’s setup guide](https://vite.dev/guide/).

Clone the team repository:

```bash
git clone https://github.com/KTH-Sys/MiniDavis.git
cd MiniDavis
python3 -m venv .venv
```

Activate the environment on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell, create it with `py -3.11 -m venv .venv` and activate with:

```powershell
.venv\Scripts\Activate.ps1
```

Install and start the backend from the repo root:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` and `http://127.0.0.1:8000/health`. Using a virtual environment keeps the project’s dependencies isolated; see [FastAPI’s environment guide](https://fastapi.tiangolo.com/virtual-environments/).

In another terminal, start the frontend:

```bash
cd MiniDavis/frontend
npm ci
npm run dev -- --port 5173
```

If that terminal already starts in the repo root, use `cd frontend` instead. Open `http://localhost:5173`.

Create the example environment files, then copy them to `backend/.env` and `frontend/.env` using your file editor. Keep the backend in baseline mode until Day 3.

```dotenv
# backend/.env — loaded by the application
MINIDAVIS_MODE=baseline
LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=8
MAX_LLM_CALLS_PER_100_TICKS=80
```

```dotenv
# frontend/.env — public browser configuration only
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Rylee makes baseline mode work with empty provider fields. Eric and Aishani fill the agreed provider settings locally before using live mode.

### Starter acceptance checklist

- [ ] **Eric:** Frontend and backend run on the same machine.
- [ ] **Saurya:** The map renders five residents from the real `/state` response.
- [ ] **Rylee:** `/health` returns ready; reset returns the same seeded initial state.
- [ ] **Aishani:** `01_agents.ipynb` returns legal baseline actions.
- [ ] **Ethan:** `02_rag.ipynb` stores and reads one event.
- [ ] **Gayatri:** Starter tests pass using the command below.

```bash
python -m pytest backend/tests -q
```

## 4. Fixed world and interfaces

Use the following map, rules, and interfaces directly.

### Town

- Grid: 12×12, with simple colored tiles and characters.
- Forest: `(2,2)`; farm: `(9,3)`; market: `(5,5)`; town hall: `(6,5)`.
- Houses: `(2,9)` and `(9,9)`; remaining tiles are traversable grass.
- Coordinates are `(x,y)` with each component in 0–11. Residents may share a traversable tile.
- Agent IDs: `ethan`, `gayatri`, `aishani`, `rylee`, `saurya`. Use these consistently in state, actions, memories, and tests.
- Residents: Ethan `(1,1)`, Gayatri `(8,3)`, Aishani `(5,4)`, Rylee `(8,9)`, Saurya `(2,8)`.
- Starting coins: Ethan 10, Gayatri 5, Aishani 15, Rylee 8, Saurya 6.
- Each starts with 3 food, 0 wood, and 100 energy. Farm has 30 food; forest has 40 wood.
- Ethan seeks wealth; Gayatri seeks supplies for shelter; Aishani trades food; Rylee seeks cooperation; Saurya helps others. Building and elections stay outside the core demo.

### Action rules

| Action | Exact effect |
| --- | --- |
| Move | One orthogonal tile; costs 1 energy; destination must be in bounds |
| Gather | On farm/forest, take up to 2 available resources; costs 5 energy |
| Eat | Consume 1 held food; restore 15 energy, capped at 100 |
| Rest | Restore 10 energy, capped at 100 |
| Talk | Public message of at most 240 characters to a resident within Manhattan distance 1 |
| Offer trade | Offer held food/wood/coins; no transfer until the counterpart accepts nearby |
| Accept/reject trade | Accept rechecks both inventories and commits once; reject changes no inventory; offers expire after 5 ticks |

The engine processes residents sequentially and owns all state changes. BFS executes routes; the LLM selects plans rather than deciding every movement tile. Rejected actions cannot change inventory. Gifts are accepted zero-price trade offers.

Relationships are bounded in `[-100,100]`: accepted fair trade adds +2 in both directions; an accepted gift adds +5 recipient-to-giver. Neutral talk/refusal adds 0. The classifier labels interactions and does not control resource or relationship accounting.

### API contract to implement

| Route | Purpose/check |
| --- | --- |
| `GET /health` | Readiness and mode; no credentials |
| `GET /state` | `run_id`, `tick`, `revision`, `seed`, `mode`, map, agents, resources, events |
| `POST /reset` | New run with seed/mode; clears pending offers/plans and isolates memory |
| `POST /step` | Advance one tick using expected run/revision and unique request ID |
| `GET /agents/{agent_id}` | Goal, inventory, energy, relationships, retrieved event evidence |
| `POST /scenario/shortage` | Reduce remaining farm food to `min(current_stock, 5)`; record the operator event |
| `GET /trace` | Initial snapshot plus ordered applied actions/events |
| `POST /replay` | Reproduce a recorded run without provider calls; label replay mode |

Send one step at a time from frontend Play. Pause stops scheduling new steps; an in-flight step may finish. Reject stale responses after Reset. Rylee allows the frontend origin in backend CORS configuration.

## 5. Day 2–3: simulation and agent checklists

### Day 2

- [ ] **Eric:** Connect the backend action loop to the frontend controls and run both.
- [ ] **Saurya:** Play changes tick/positions; Pause stops new ticks; Next Turn advances once; Reset returns the initial town.
- [ ] **Rylee:** Run `test_world.py` and `test_api.py`; check legal coordinates, energy 0–100, and nonnegative stock/inventory.
- [ ] **Aishani:** Verify all five baseline residents move toward resources and choose eat/rest when needed.
- [ ] **Ethan:** Inspect an accepted gather event and a rejected invalid-move event; check their outcomes differ.
- [ ] **Gayatri:** Run 100 baseline ticks and save the seed, final state, and any failed check.

```bash
python -m pytest backend/tests/test_world.py backend/tests/test_api.py -q
python scripts/run_eval.py --mode baseline --seeds 11 --scenarios normal --ticks 100 --out results/day2
```

### Day 3 shared agent session

Open `ml/notebooks/01_agents.ipynb` in Colab. Run cells in order: imports → resident observation → baseline decision → live provider adapter → validation → failure examples. The notebook must support Colab Secrets/local environment settings without printing keys.

Aishani implements structured plans with `run_id`, `agent_id`, `observation_revision`, action/target fields, and a short public explanation. Rylee validates them and rejects unknown actions, bad targets, missing resources, and obsolete run/revision values. Use an 8-second timeout, cached plans, and a run call cap. Use legal baseline/rest fallback for invalid or failed calls.

- [ ] **Eric:** Save a two-minute MVP recording and assign failing cases to the responsible teammate.
- [ ] **Saurya:** Click every resident; inspector and event log match the backend snapshot.
- [ ] **Rylee:** Run `test_agents.py`; invalid output cannot mutate authoritative state.
- [ ] **Aishani:** Save at least one actual live decision for each resident with mode/model identified.
- [ ] **Ethan:** Check that recent memories cite existing event IDs.
- [ ] **Gayatri:** Run seeds 11, 22, and 33 for 100 baseline ticks each.

```bash
python -m pytest backend/tests/test_agents.py -q
python scripts/run_eval.py --mode baseline --seeds 11 22 33 --scenarios normal --ticks 100 --out results/day3
```

**Day 3 MVP passes:** all controls/inspectors work, five residents act, and the three baseline runs have zero crashes or state invariant failures. A working baseline MVP is preserved while live agents improve.

## 6. Day 4: RAG checklist

Open `ml/notebooks/02_rag.ipynb` in Colab. Run cells in order: store events → filter visible history → embed/rank events → retrieve sources → generate with/without memory → evaluate retrieval.

Ethan implements SQLite events containing `event_id`, `run_id`, `tick`, `agent_id`, participants, visibility, event type, outcome, factual text, and optional embedding. Filter by run/agent/visibility and exclude future events **before** ranking. Return five recent events plus the top three relevant unique events with source IDs. Use scoped recent/lexical fallback if embeddings fail.

- [ ] **Eric:** Confirm retrieved evidence travels from memory service to the planner and inspector.
- [ ] **Saurya:** Confirm the screen displays memory text, IDs, and retrieval mode.
- [ ] **Rylee:** Run `test_memory.py`; another resident’s private event and an old run’s event stay excluded.
- [ ] **Aishani:** Confirm all five live planners use the retrieved facts in their input.
- [ ] **Ethan:** Run the 10 frozen retrieval examples; at least 8 include the expected event in the top three relevant results.
- [ ] **Gayatri:** Save matching memory-on/off observations, decisions, and retrieved IDs without claiming a guaranteed behavioral change.

```bash
python -m pytest backend/tests/test_memory.py -q
```

## 7. Day 5–6: fine-tuning checklist

### Dataset and model

Eric and Gayatri prepare 200 labelled synthetic town interactions, 50/class, with `example_id` 001–200, `text`, `label`, and `scenario_family`. Labels: cooperation, conflict, trade, neutral.

Before training, correct labels and check duplicates. Ethan and Gayatri create a reproducible 60/20/20 grouped split: target 120 train, 40 validation, 40 test, with 10 test examples/class. Keep all paraphrases from the same scenario family in one split. If these constraints conflict, revise the example families before freezing the split; do not move test examples after viewing results.

Train a small DistilBERT sequence classifier using `distilbert/distilbert-base-uncased`, four labels, maximum length 128, initial learning rate `2e-5`, batch size 8, and three epochs. Treat these as starting settings; choose a checkpoint using validation macro-F1 only. Compare with TF-IDF + logistic regression trained on the same training split. This follows the general workflow in [Hugging Face’s classification guide](https://github.com/huggingface/transformers/blob/main/docs/source/en/tasks/sequence_classification.md).

### Day 5 shared Colab session

Open `ml/notebooks/03_finetune.ipynb`. Run cells in order: install pinned notebook dependencies → load reviewed data → verify frozen split → train baseline → fine-tune → validate → export model/config/tokenizer. Do not run the final test evaluation yet.

Use a GPU runtime if available. Colab availability varies; save checkpoints/results to Drive rather than depending on runtime persistence. If unavailable, run on CPU with batch size 4 and record the configuration and training time. See [Colab’s resource FAQ](https://research.google.com/colaboratory/faq.html).

- [ ] **Eric:** Prepare the dataset with Gayatri and confirm everyone can run the shared notebook.
- [ ] **Saurya:** Check the classifier label field displays correctly using a supplied fixture.
- [ ] **Rylee:** Run `test_trade.py`; offers transfer nothing until valid acceptance and cannot commit twice.
- [ ] **Aishani:** Review examples 001–050 and save label corrections.
- [ ] **Ethan:** Review examples 051–100 and verify no scenario family crosses splits.
- [ ] **Gayatri:** Review examples 101–200; train after reviews finish; save baseline/validation metrics and exported classifier.

### Day 6 final classifier check

- [ ] Freeze selected weights, tokenizer, label mapping, and training configuration.
- [ ] Gayatri evaluates the baseline and selected fine-tuned model on untouched test data once.
- [ ] Save macro-F1, per-class precision/recall, confusion matrix, example count, and split manifest.
- [ ] Save `classifier/`, `metrics.json`, and the notebook in the shared Models/Results folders.
- [ ] Rylee implements the classifier-loading hook and loads the exported model.
- [ ] Saurya confirms a real completed interaction displays its predicted label and confidence.
- [ ] Keep deterministic world/relationship rules even when the label is wrong; report poor results honestly.

## 8. Day 6 integration gate

- [ ] **Eric:** Run the integrated build and fix blockers with the responsible teammate before feature freeze.
- [ ] **Saurya:** Controls, memories, offers/acceptances, classifier labels, and shortage are visible.
- [ ] **Rylee:** Trade conserves transferred items/coins; shortage lowers stock; reset clears offers; replay reproduces final state.
- [ ] **Aishani:** All five agents make live decisions; malformed JSON, timeout, missing key, and quota error fall back safely.
- [ ] **Ethan:** Memories and relationships describe executed events, not invented model claims.
- [ ] **Gayatri:** Save integration results and held-out classifier metrics, including failures.

```bash
python -m pytest backend/tests -q
python scripts/run_eval.py --mode rag --seeds 11 --scenarios normal shortage --ticks 100 --out results/day6
```

Require no invariant failures, an accepted bilateral trade demonstrated by a documented fixture/trace, source-backed memory retrieval, working shortage/fallback, and successful classifier loading. The UI labels fixture, baseline, live, fallback, and replay honestly. Freeze feature additions after this gate.

## 9. Day 7 evaluation and stabilization

Gayatri implements `run_eval.py` with modes `baseline`, `llm`, `rag`, fixed seeds, normal/shortage scenarios, configurable tick counts, and output directories. Aishani and Ethan connect the planner/retrieval modes. `llm` excludes episodic memory; `rag` includes it. Keep relationships, rules, initial state, model, prompts, and budgets identical for matching comparisons.

```bash
python scripts/run_eval.py --mode baseline --seeds 11 --scenarios normal --ticks 1000 --out results/stress
python scripts/run_eval.py --mode all --seeds 11 22 33 --scenarios normal shortage --ticks 100 --out results/comparison
```

The comparison is 3 modes × 3 seeds × 2 scenarios = 18 runs. Apply shortage at tick 30 in every shortage episode. If the agreed provider budget is insufficient, use one matched seed across every mode/scenario (6 runs) and label results exploratory.

- [ ] **Eric:** Collect reproducible bugs, fix them with their owners, and rerun affected checks.
- [ ] **Saurya:** Complete a 30-minute UI session without freezing; show at most 200 recent events on screen.
- [ ] **Rylee:** Complete 1,000 baseline ticks with legal state and verify reset afterward.
- [ ] **Aishani:** Verify recovery and the 80-call/100-tick default cap; record actual calls and failures.
- [ ] **Ethan:** Rerun retrieval hit-rate, isolation, and stale/future-event checks.
- [ ] **Gayatri:** Save run IDs/configs, proposal validity, engine acceptance, fallback rate, trades, latency, tokens/calls, and classifier metrics.

Report actual denominators and observed behavior. Three seeds do not establish statistical significance or guarantee emergent cooperation.

## 10. Day 8–9 demo and handover

### Day 8: two rehearsals

- [ ] **Eric:** Present for five minutes: town → live decision → retrieved memory → shortage/trade → training/comparison results.
- [ ] **Saurya:** Operate the UI and verify readability at 1280×720.
- [ ] **Rylee:** Run the written startup steps on the demo machine and load a known replay.
- [ ] **Aishani:** Confirm provider access and demonstrate labelled fallback on simulated failure.
- [ ] **Ethan:** Show a retrieved event and the interaction that actually created it.
- [ ] **Gayatri:** Confirm every displayed result matches saved metrics; record a backup video that opens locally.

### Day 9: before presentation

- [ ] **Eric:** Collect the source tag, setup guide, notebooks, model, metrics, and recording links.
- [ ] **Saurya:** Run the frontend build and final controls check.
- [ ] **Rylee:** Run backend tests and smoke-check health/reset/step/trade/retrieval/replay.
- [ ] **Aishani:** Show the correct provider/mode and explain safe recovery.
- [ ] **Ethan:** Show source-backed memories and explain retrieval.
- [ ] **Gayatri:** Explain held-out training results and comparison limitations; submit the evidence files.

```bash
python -m pytest backend/tests -q
```

From `frontend/`:

```bash
npm run build
```

Release only after crash, corrupted-state, privacy-isolation, and broken-core-flow issues are repaired. If a provider fails during the presentation, state it and switch to labelled baseline/replay or the local recording.

## 11. Report and fix bugs

Each person reports:

- Name and checkpoint, e.g. `Rylee — Day 2`.
- Exact command or button clicked.
- Expected result and actual result.
- Full relevant error text with credentials removed.
- Seed, mode, tick/run ID, and commit version if available.

Eric assigns the reproduction to the responsible teammate and helps resolve integration issues. Fix the code, rerun the failing check, and attach the result. Mark a checkbox complete only after its result is observed.

Use a small branch and pull request for code changes; Eric reviews/merges after the relevant checks pass. Report account access, implementation progress, and measured results clearly.
