# MiniDavis — Technical Guide and Checklists

Use [README.md](README.md) for who does what on each date. This guide defines the implementation and exact checks.

**Current verification:** The [Day 0–4 audit](docs/day0-day4-audit.md) verifies all 24 Day 1–4 technical deliverables, including five real Groq decisions, CPU MiniLM retrieval, source isolation and a live memory-on/off comparison with explicit fallback counts. Day 0 account/sharing confirmations remain separate. The baseline includes resident selection, decision/source inspectors, the event log and the two-minute MVP recording. Eric's [Day 5 preparation](docs/eric-day5.md) adds 200 draft interaction examples, grouped splits, review/freeze gates and an offline-checked Colab notebook. Human dataset review, actual classifier training and later routes remain assigned work. Complete checkboxes only after observing results.

## Model and hosting decision

- **Agent LLM:** Groq-hosted Qwen; starting model ID `qwen/qwen3.8-27b`. All five residents share this service with separate observations, goals and memories. Verify availability in the project account on Day 1 and freeze the working model/config on Day 6. No local town LLM or Ollama installation is required.
- **RAG:** Our SQLite event store, filtering and retrieval; `sentence-transformers/all-MiniLM-L6-v2` embeddings on CPU. Cache event embeddings. Use scoped recent/lexical retrieval if embedding loading fails and label the mode.

Install `backend/requirements-ml.txt` and set `MEMORY_RETRIEVAL_MODE=semantic` in the server environment to enable MiniLM. The default is `lexical` so ordinary tests/startup do not download models. `EMBEDDING_CACHE_PATH=data/model-cache` stores ignored local weights; `EMBEDDING_REVISION` pins the model commit in `.env.example`. Startup warms the optional model before serving turns. Failed loading uses labelled keyword retrieval. Vector cache keys include the model/revision and source-text fingerprint; the previous event-ID-only cache is not trusted. A custom embedder must use a distinct `embedding_key` when its model changes.
- **Fine-tuning:** Train our four-label DistilBERT classifier in Colab and export the model/tokenizer/config. Load it on the CPU backend. This does not change the hosted Qwen weights. Hosting a future fine-tuned town LLM requires a separate checkpoint-compatible service and budget.
- **App hosting:** Static React frontend plus a CPU FastAPI service. Render is a starting option; Eric/Rylee select a backend size only after measuring classifier + embeddings + app RAM. Groq runs the large LLM. No GPU server purchase is assumed.

Groq currently lists Qwen at 30 requests/minute, 1,000 requests/day, 8,000 tokens/minute and 200,000 tokens/day on its free plan; actual account limits/model availability must be checked before use. Free quota is suitable for bounded development and demos, not an always-running town. See [Groq limits](https://console.groq.com/docs/rate-limits), [models](https://console.groq.com/docs/models), and [JSON schema support](https://console.groq.com/docs/structured-outputs).

Training and runtime are separate: Colab produces the classifier files; the backend loads them for prediction. Use the provider API key only in server environment settings or Colab Secrets. Never put it in React configuration.

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
- [ ] Confirm Groq access, the Qwen model, the free quota and credential ownership with Aishani; record the hosting budget separately.

### Saurya

- [ ] Sign in to GitHub and accept the repository invitation.
- [ ] Open the repository and the shared Notion project.
- [ ] Confirm that the shared links are visible.

### Rylee

- [ ] Sign in to GitHub and accept the repository invitation.
- [ ] Open Ethan’s shared Drive folder.
- [ ] Confirm GitHub and Drive access.

### Aishani

- [ ] Sign in to Groq and confirm access to the authorized project.
- [ ] Confirm with Eric who controls the Groq credential and shared development/demo quota.
- [ ] Record `groq`, the available Qwen model and account limits; keep credentials out of GitHub, Notion and chat. Do not run inference today.

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

Use Python 3.12 and Node.js 24 LTS, as recorded in `.python-version` and `.nvmrc`. The frontend requires Node 22.12+; use the team’s Node 24 LTS version. Follow the committed lockfile rather than upgrading packages independently. See [Vite’s setup guide](https://vite.dev/guide/).

Clone the project repository:

```bash
git clone https://github.com/KTH-Sys/MiniDavis.git
cd MiniDavis
python3.12 -m venv .venv
```

Activate the environment on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell, create it with `py -3.12 -m venv .venv` and activate with:

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
LLM_PROVIDER=groq
LLM_MODEL=qwen/qwen3.8-27b
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=20
LLM_MIN_AGENT_REPLAN_SECONDS=30
LLM_MAX_REQUESTS_PER_MINUTE=4
LLM_MAX_CALLS_PER_RUN=20
LLM_MAX_CALLS_PER_DAY=500
LLM_MAX_TOKENS_PER_DAY=160000
LLM_MAX_INPUT_TOKENS=800
LLM_MAX_COMPLETION_TOKENS=512
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MEMORY_RETRIEVAL_MODE=lexical
EMBEDDING_REVISION=1110a243fdf4706b3f48f1d95db1a4f5529b4d41
EMBEDDING_CACHE_PATH=data/model-cache
CLASSIFIER_MODEL_PATH=ml/artifacts/classifier
MEMORY_DB_PATH=data/minidavis.sqlite
FRONTEND_ORIGINS=http://localhost:5173
```

```dotenv
# frontend/.env — public browser configuration only
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The starter loads these server-only settings from `backend/.env`; baseline works without a key. Set `MINIDAVIS_MODE=llm` and a server `LLM_API_KEY` to enable Groq. Set `MEMORY_RETRIEVAL_MODE=semantic` after installing the optional ML requirements to use CPU MiniLM. Reset preserves the active mode unless an explicit mode is supplied. No key is returned by health/state or exposed to React. Actual five-resident verification is saved in `results/day0-day4/live-final/live-decisions.json`; rerun the bounded live checker only when needed and within the team's quota.

### Shared request and token budget

- Aishani creates one Groq adapter using strict JSON schema and a short public explanation; Rylee still checks action legality, run and revision.
- Queue at most four requests/minute across all five agents, spaced at least 15 seconds apart. Replan each resident no sooner than 30 seconds and only when needed; the shared queue means busy residents may wait longer. Show waiting state. Movement/BFS and animations use cached plans between calls.
- Allow one in-flight model request; capture its observation revision, apply only if still valid, and discard stale results after reset. Do not freeze frontend rendering while waiting.
- Enforce 20 calls/run, 500 calls/day and 160,000 total tokens/day as conservative application defaults, plus actual provider limits. Count retries and completion/reasoning tokens. Enforce input/output bounds and record measured usage, not just estimates.
- On 429 honor `Retry-After`; avoid repeated immediate retries. On unavailable model, missing key, timeout or invalid output use labelled legal baseline/rest fallback. Budget exhaustion makes no further provider calls.
- Provider limits include notebooks and all teammates’ development. Use mocked provider responses for routine tests. Reserve session/evaluation budgets in a shared tracker; use a central development adapter when available. Separate local counters do not enforce account-wide limits.
- A typical five-minute demo may need about 20 calls, but token use must be measured. Reserve that allowance before the demo. Do not make extra live calls simply for more viewers.

### Starter acceptance checklist

- [x] **Eric:** Frontend and backend run on the same machine.
- [x] **Saurya:** The map renders five residents from the real `/state` response.
- [x] **Rylee:** `/health` returns ready; reset returns the same seeded initial state.
- [x] **Aishani:** `01_agents.ipynb` returns legal baseline actions.
- [x] **Ethan:** `02_rag.ipynb` stores and reads one event.
- [x] **Gayatri:** Starter tests pass using the command below.

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

- [x] **Eric:** Connect the backend action loop to the frontend controls and run both.
- [x] **Saurya:** Play changes tick/positions; Pause stops new ticks; Next Turn advances once; Reset returns the initial town.
- [x] **Rylee:** Run `test_world.py` and `test_api.py`; check legal coordinates, energy 0–100, and nonnegative stock/inventory.
- [x] **Aishani:** Verify all five baseline residents move toward resources and choose eat/rest when needed.
- [x] **Ethan:** Inspect an accepted gather event and a rejected invalid-move event; check their outcomes differ.
- [x] **Gayatri:** Run 100 baseline ticks and save the seed, final state, and any failed check.

```bash
python -m pytest backend/tests/test_api.py -q
python scripts/run_eval.py --mode baseline --seeds 11 --scenarios normal --ticks 100 --out results/day2
```

### Day 3 shared agent session

Open `ml/notebooks/01_agents.ipynb` in Colab. Run cells in order: imports → resident observation → baseline decision → live provider adapter → validation → failure examples. The notebook must support Colab Secrets/local environment settings without printing keys.

Aishani implements structured plans with `run_id`, `agent_id`, `observation_revision`, action/target fields, and a short public explanation. Rylee validates them and rejects unknown actions, bad targets, missing resources, and obsolete run/revision values. Use the Groq adapter and shared queue above, a configurable 20-second timeout, cached plans and call/token caps. Strict JSON schema does not prove world legality. Use legal baseline/rest fallback for invalid or failed calls.

- [x] **Eric:** Save a two-minute MVP recording and assign failing cases to the responsible teammate.
- [x] **Saurya:** Click every resident; inspector and event log match the backend snapshot.
- [x] **Rylee:** Run `test_agents.py`; invalid output cannot mutate authoritative state.
- [x] **Aishani:** Saved one actual live decision per resident with mode/model identified in `results/day0-day4/live-final/live-decisions.json`.
- [x] **Ethan:** Check that recent memories cite existing event IDs.
- [x] **Gayatri:** Run seeds 11, 22, and 33 for 100 baseline ticks each.

```bash
python -m pytest backend/tests/test_agents.py -q
python scripts/run_eval.py --mode baseline --seeds 11 22 33 --scenarios normal --ticks 100 --out results/day3
```

**Day 3 MVP passes:** all controls/inspectors work, five residents act, and the three baseline runs have zero crashes or state invariant failures. A working baseline MVP is preserved while live agents improve.

## 6. Day 4: RAG checklist

Open `ml/notebooks/02_rag.ipynb` in Colab. Run cells in order: store events → filter visible history → embed/rank events → retrieve sources → generate with/without memory → evaluate retrieval.

Ethan implements SQLite events containing `event_id`, `run_id`, `tick`, `agent_id`, participants, visibility, event type, outcome, factual text, and optional embedding. Filter by run/agent/visibility and exclude future events **before** ranking. Use cached MiniLM CPU embeddings. Return up to five recent events plus the top three relevant unique events with source IDs, truncating factual text to the planner input budget. Use scoped recent/lexical fallback if embeddings fail.

- [x] **Eric:** Confirm retrieved evidence travels from memory service to the planner and inspector.
- [x] **Saurya:** UI tests confirm memory text, source IDs, query and actual retrieval mode; the footer no longer mislabels semantic memory.
- [x] **Rylee:** Memory tests exclude private/old/future events before embedding; real MiniLM API/reset checks cover all five residents.
- [x] **Aishani:** All five real live requests include their own retrieved facts; tests enforce scoped source IDs and the 800-byte conservative prompt bound.
- [x] **Ethan:** The 10 frozen retrieval checks and 10 paraphrased queries each score 10/10 with real CPU MiniLM.
- [x] **Gayatri:** Matched observations, live decisions, source IDs and memory-on/off examples are saved. Four of five proposals per condition were accepted; others safely fell back. This is an exploratory comparison, not proof of improvement.

```bash
python -m pytest backend/tests/test_memory.py -q
```

## 7. Day 5–6: fine-tuning checklist

### Dataset and model

Eric and Gayatri prepare 200 labelled synthetic town interactions, 50/class, with `example_id` 001–200, `text`, `label`, and `scenario_family`. Labels: cooperation, conflict, trade, neutral.

Before training, correct labels and check duplicates. Ethan and Gayatri create a reproducible 60/20/20 grouped split: target 120 train, 40 validation, 40 test, with 10 test examples/class. Keep all paraphrases from the same scenario family in one split. If these constraints conflict, revise the example families before freezing the split; do not move test examples after viewing results.

Eric's draft now includes these counts with 40 scenario families, assigned review rows and a reproducible **candidate** split. Follow [the label policy and review steps](ml/data/README.md); no human reviews or training are claimed. Run `python scripts/prepare_interactions.py` and `python -m pytest ml/tests -q`. After review edits, use `--refresh-draft`; after all assigned reviews, use `--freeze`. Training verifies exact frozen hashes and review completion. Only text is used as model input; IDs/families/reviewers are excluded. `python scripts/check_day5_notebook.py` verifies the notebook's offline defaults. Training dependencies in `ml/requirements.txt` are separate from backend dependencies.

Train a small DistilBERT sequence classifier using `distilbert/distilbert-base-uncased`, four labels, maximum length 128, initial learning rate `2e-5`, batch size 8, and three epochs. Treat these as starting settings; choose a checkpoint using validation macro-F1 only. Compare with TF-IDF + logistic regression trained on the same training split. This follows the general workflow in [Hugging Face’s classification guide](https://github.com/huggingface/transformers/blob/main/docs/source/en/tasks/sequence_classification.md).

### Day 5 shared Colab session

Open `ml/notebooks/03_finetune.ipynb`. Run cells in order: install pinned notebook dependencies → load reviewed data → verify frozen split → train baseline → fine-tune → validate → export model/config/tokenizer. Do not run the final test evaluation yet.

Use a GPU runtime if available. Colab availability varies; save checkpoints/results to Drive rather than depending on runtime persistence. If unavailable, run on CPU with batch size 4 and record the configuration and training time. See [Colab’s resource FAQ](https://research.google.com/colaboratory/faq.html).

- [ ] **Eric:** Dataset preparation, structural tests and offline notebook preflight are complete ([evidence](docs/eric-day5.md)); confirm team access and the actual shared Colab run after assigned reviews/freeze.
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

### CPU deployment checklist — prepare Day 5, preview Day 6

- [ ] **Eric:** Choose static frontend hosting and CPU backend hosting using measured RAM and the agreed budget. Record URLs/costs or a specific blocker; do not enable paid resources without an agreed budget.
- [ ] **Rylee:** Package FastAPI, pinned dependencies and the exported classifier/tokenizer/config. Fetch model files during build or store them in an accessible artifact location. Load models once per process and measure peak memory; start with one backend worker and one shared town scheduler.
- [ ] **Rylee:** Bind to `0.0.0.0` and the host-provided port. Configure readiness, frontend origins, Groq server secrets and classifier/database paths. Keep backend mutation controls restricted to the demo operator; viewers read the same town state.
- [ ] **Saurya:** Build React with `VITE_API_BASE_URL` set to the HTTPS backend URL. Configure static hosting for `frontend/dist`; verify CORS and controls in the deployed build.
- [ ] **Ethan:** Use a persistent disk for SQLite or adapt storage to a managed database. Verify memory/run isolation after restart. An ephemeral preview must explicitly reset on restart and export traces; do not describe it as durable storage.
- [ ] **Gayatri:** Check real classifier loading, CPU inference latency and RAM, two viewers seeing one run, no added provider calls per viewer, reset/replay and missing-key/429 recovery.
- [ ] **Eric/Aishani:** Check account-wide remaining request/token quota before the preview and reserve the demo allowance.

Render offers static/frontend and Python web-service hosting, but free backend services sleep after inactivity and lose local SQLite files on restart; choose durable storage separately. A free backend must pass actual RAM/startup checks with both small models loaded. If it cannot, record the resource blocker and use a suitable CPU plan only within the agreed budget. See [Render service types](https://render.com/docs/your-first-deploy) and [free-service limits](https://render.com/docs/free).

If hosting is blocked, preserve a local CPU frontend/backend that calls Groq. No teammate must install or serve the town LLM. Rehearse both the live route and a labelled baseline/replay/recording route. Permanent hosting is secondary to Day 6 integration and Days 7–9 stabilization.

## 9. Day 7 evaluation and stabilization

Gayatri implements `run_eval.py` with modes `baseline`, `llm`, `rag`, fixed seeds, normal/shortage scenarios, configurable tick counts, and output directories. Aishani and Ethan connect the planner/retrieval modes. `llm` excludes episodic memory; `rag` includes it. Keep relationships, rules, initial state, model, prompts, and budgets identical for matching comparisons.

```bash
python scripts/run_eval.py --mode baseline --seeds 11 --scenarios normal --ticks 1000 --out results/stress
python scripts/run_eval.py --mode all --seeds 11 --scenarios normal shortage --ticks 100 --out results/comparison
```

Default to one matched seed (11) across three modes and two scenarios: six exploratory runs. Four of those runs use Groq, capped at 20 calls/run; baseline uses zero. Reserve calls/tokens first and pace all live requests through the shared queue. Apply shortage at tick 30 in every shortage episode. Expand to seeds 11/22/33 (18 runs) only when the shared quota permits; split over days while freezing model/prompt/config and record dates. A fast baseline stress test must not call Groq. Report budget-exhausted comparisons rather than treating fallback as live LLM behavior.

- [ ] **Eric:** Collect reproducible bugs, fix them with their owners, and rerun affected checks.
- [ ] **Saurya:** Complete a 30-minute UI session without freezing; show at most 200 recent events on screen.
- [ ] **Rylee:** Complete 1,000 baseline ticks with legal state and verify reset afterward.
- [ ] **Aishani:** Verify Groq recovery, the shared four-call/minute queue, 20-call/run cap and daily token budget; record actual usage including retries.
- [ ] **Ethan:** Rerun retrieval hit-rate, isolation, and stale/future-event checks.
- [ ] **Gayatri:** Save run IDs/configs, proposal validity, engine acceptance, fallback rate, trades, latency, tokens/calls, and classifier metrics.

Report actual denominators and observed behavior. Three seeds do not establish statistical significance or guarantee emergent cooperation.

## 10. Day 8–9 demo and handover

### Day 8: two rehearsals

- [ ] **Eric:** Present for five minutes: town → live decision → retrieved memory → shortage/trade → training/comparison results.
- [ ] **Saurya:** Operate the UI and verify readability at 1280×720.
- [ ] **Rylee:** Check the deployed API or written local CPU startup, restart behavior and a known replay; no local town LLM is required.
- [ ] **Aishani:** Reserve the Groq demo quota, confirm the configured Qwen model and demonstrate labelled fallback on simulated failure.
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
