# MiniDavis — Team Plan

A 2D town with five AI residents named Ethan, Gayatri, Aishani, Rylee, and Saurya. They move, gather food and wood, trade, talk, and remember interactions.

## Run MiniDavis

The runnable baseline connects React to FastAPI and supports Play, Pause, Next Turn and Reset without an API key or local model. The animated pixel-art town has five selectable residents and a light, terminal-style feed beside it. All activity shows recorded town actions plus the selected resident's latest memory. Decision, Memories and Interactions tabs show that resident's actual decision text and retrieved source events. Conversations and trades will appear once the backend records those actions. Keyword retrieval is connected; live Groq decisions, semantic embeddings and classifier training remain upcoming work. See the [town artwork and animation notes](frontend/public/art/README.md).

Use Python 3.12 and Node 24 LTS. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. Backend API docs: **http://127.0.0.1:8000/docs**. Windows activation is in [the technical guide](README-TECHNICAL.md). No environment file is required for baseline defaults.

See [Eric’s implementation notes](docs/eric-day1-day2.md) for checks and team handoffs, and [hosting/budget status](docs/hosting-budget.md) before choosing a cloud service.

Eric’s [Day 3–4 integration notes](docs/eric-day3-day4.md) include the MVP recording, source-evidence contract and verification results.

**Team:** Eric, Ethan, Gayatri, Aishani, Rylee, and Saurya.

**Model plan:** Use Groq’s hosted Qwen for agent decisions. No teammate needs to run the town LLM locally. Build our own RAG and fine-tune a small DistilBERT interaction classifier in Colab; run embeddings and the classifier on a CPU backend.

**Deployment plan:** Host React as a static website and FastAPI on a CPU server. Share one town across viewers. Eric selects hosting after checking backend memory use and the available budget; no paid service is assumed. Prepare a hosted preview by Day 6 when resources permit, and keep baseline/replay available for the demo.

**Free quota:** All five residents use one request queue. Start at four model calls per minute across the town, with cached plans between calls. Movement continues without new LLM requests. Development, notebooks, evaluations and demos all consume the provider quota; reserve calls before a session.

**Meetings:** Tuesdays and Thursdays, October 13–November 12, 2026. Each Day below is a meeting checkpoint. Complete its tasks by that meeting where possible; do the shared workshop together. Meeting times are TBD.

## Who does what

| Person | Responsibility |
| --- | --- |
| Eric | Lead and integration; help Saurya with frontend and Rylee with backend |
| Saurya | Frontend: build and check the town screen |
| Rylee | Backend: build and check the simulation/API |
| Aishani | Agents: build and check LLM decisions |
| Ethan | RAG: build and check memory retrieval |
| Gayatri | Fine-tuning and evaluation: prepare training and record results |

**Build the assigned feature, run its checks, and share the result.** Use the fixed map, rules, and interfaces in the technical guide. When something fails, record the exact error and fix it with the responsible teammate.

**Everyone learns agents, RAG, and fine-tuning together.** Owners run the relevant checks between meetings. Exact commands and technical checklists are in [README-TECHNICAL.md](README-TECHNICAL.md).

## Day 0 — Tuesday, 10/13: Accounts and access only

- [ ] **Eric:** Create the MiniDavis GitHub repository and invite the five teammates.
- [ ] **Saurya:** Sign in to GitHub, accept repo access, and open the shared Notion project.
- [ ] **Rylee:** Sign in to GitHub, accept repo access, and confirm access to the shared Google Drive folder.
- [ ] **Aishani:** Set up Groq access with Eric; record the Qwen model, free quota and credential owner without posting keys.
- [ ] **Ethan:** Create the shared MiniDavis Google Drive folder and give the team access.
- [ ] **Gayatri:** Create an empty shared Colab notebook in that folder and confirm everyone can open it.

**Finish:** Everyone can open GitHub, Notion, Drive, and Colab. No coding, design, dataset preparation, or training today.

## Day 1 — Thursday, 10/15: Run the starter

- [x] **Eric:** Create the project folders and shared Groq configuration; connect frontend/backend and record the hosting budget.
- [ ] **Saurya:** Set up React and render the 12×12 map with five residents.
- [ ] **Rylee:** Set up FastAPI and implement `/health`, `/state`, and `/reset`.
- [ ] **Aishani:** Create the baseline-agent notebook and a Groq connection check; return valid baseline decisions without local LLM weights.
- [ ] **Ethan:** Create the event store and memory notebook; save/read one sample event.
- [ ] **Gayatri:** Add starter tests, run them, and save the pass/fail output.

**Finish:** Everyone can run their assigned part of the starter project.

## Day 2 — Tuesday, 10/20: Run the simulation

- [x] **Eric:** Connect the simulation loop and frontend controls to backend ticks.
- [ ] **Saurya:** Add Play, Pause, Next Turn, and Reset using the real backend.
- [ ] **Rylee:** Implement movement, gathering, eating, and resting; run 100 baseline ticks.
- [ ] **Aishani:** Add baseline action selection and destination-following for all five residents.
- [ ] **Ethan:** Store completed actions as memories and mark rejected actions as rejected.
- [ ] **Gayatri:** Add invalid-move and resource tests; report any negative inventory or crash.

**Finish:** Five residents move and gather safely through the UI.

## Day 3 — Thursday, 10/22: MVP + agents together

**Shared session:** Run the agent notebook, send a short observation to Groq Qwen, and inspect its validated JSON action. Keep credentials in Colab Secrets or backend environment settings.

- [x] **Eric:** Complete the MVP integration and record a two-minute working run.
- [ ] **Saurya:** Add the inspector and event log; show live, waiting, baseline and fallback states for every resident.
- [ ] **Rylee:** Add model-action validation and run the MVP safety tests.
- [ ] **Aishani:** Implement Groq Qwen JSON decisions, a shared four-call/minute queue and cached plans; save one live decision per resident.
- [ ] **Ethan:** Pass recent memories with real event IDs into the agent input.
- [ ] **Gayatri:** Run three seeded 100-tick MVP checks and save the report.

**MVP gate:** Town, five residents, controls, inspector, and log work. Baseline mode remains usable while live AI develops.

## Day 4 — Tuesday, 10/27: RAG together

**Shared session:** Save an interaction, retrieve it, and use it in an agent decision.

- [x] **Eric:** Connect RAG to the backend and inspector; help Saurya and Rylee test it.
- [ ] **Saurya:** Display retrieved text and source event IDs in the inspector.
- [ ] **Rylee:** Run cross-resident and cross-run memory isolation tests.
- [ ] **Aishani:** Add retrieved memories to all five live agents’ prompts.
- [ ] **Ethan:** Implement recent + relevant retrieval with MiniLM CPU embeddings; run 10 checks and keep prompts within the token budget.
- [ ] **Gayatri:** Compare decisions with memory enabled and disabled; save one example of each.

**Finish:** Agents retrieve actual past events without leaking another resident’s private memory.

## Day 5 — Thursday, 10/29: Fine-tuning together

**Shared session:** Run the fine-tuning notebook to train a small interaction classifier: cooperation, conflict, trade, or neutral.

- [ ] **Eric:** Prepare the dataset with Gayatri and help the team run the notebook in Colab.
- [ ] **Saurya:** Add an interaction-label field to the UI.
- [ ] **Rylee:** Implement trade offers and acceptance; run duplicate-acceptance tests.
- [ ] **Aishani:** Review examples 001–050 and correct wrong labels.
- [ ] **Ethan:** Review examples 051–100 and check that scenario families stay in one data split.
- [ ] **Gayatri:** Prepare the Colab training notebook, review examples 101–200, train DistilBERT, and export weights/tokenizer/config and validation results.

**Finish:** Train on the fixed training split, choose using validation, and save a trained classifier. Keep test data untouched until Day 6. Fine-tune the classifier, not the main LLM.

## Day 6 — Tuesday, 11/03: Integrate and freeze features

- [ ] **Eric:** Finish integration; help deploy the static frontend and CPU backend preview within the agreed budget, or record the hosting blocker.
- [ ] **Saurya:** Connect the frontend to the deployed API when available; check shortage, trades, memories, classifier labels and waiting states.
- [ ] **Rylee:** Finish trading, shortage, reset and replay; package the CPU backend, load the classifier and measure RAM before deployment.
- [ ] **Aishani:** Test Groq timeout, invalid output, missing key and quota errors; enforce shared request/token budgets and safe fallback.
- [ ] **Ethan:** Update memories/relationships from completed interactions; verify persistent storage or document reset-on-restart preview behavior.
- [ ] **Gayatri:** Evaluate the frozen classifier on held-out test data and run the integration checklist.

**Integration gate:** Groq agents, our RAG, trades, shortage, CPU classifier and frontend work together. Check queue/budget limits and hosting readiness. Keep fixed relationship rules; the classifier supplies an observable label. Freeze new features after this meeting. A hosting blocker must be recorded and must not delay core integration.

## Day 7 — Thursday, 11/05: Stabilize and compare

- [ ] **Eric:** Reproduce and fix bugs with the responsible teammate; help backend/frontend owners rerun checks.
- [ ] **Saurya:** Run a 30-minute session with two viewers; confirm both see one town and do not multiply model calls.
- [ ] **Rylee:** Run 1,000 baseline ticks and confirm no corrupted resources or positions.
- [ ] **Aishani:** Run mocked Groq failure/quota checks; verify cached plans, stale-result rejection and aggregate call/token caps.
- [ ] **Ethan:** Rerun retrieval and memory-isolation checks.
- [ ] **Gayatri:** Run six matched comparison runs within the reserved Groq quota; save calls/tokens, latency, behavior and classifier metrics.

**Finish:** Tested runs have no crashes or invariant failures; evaluation results are saved.

## Day 8 — Tuesday, 11/10: Rehearse

- [ ] **Eric:** Prepare the five-minute script and lead two rehearsals.
- [ ] **Saurya:** Operate the town and check projector readability.
- [ ] **Rylee:** Check the deployed API or local CPU startup, restart behavior and known-good replay; confirm no local LLM is needed.
- [ ] **Aishani:** Reserve the demo Groq quota, check the configured Qwen model and demonstrate labelled fallback.
- [ ] **Ethan:** Prepare one real remembered-interaction example for the demo.
- [ ] **Gayatri:** Check presentation numbers and record a local backup demo.

**Finish:** Two five-minute rehearsals pass, including recovery from a provider failure.

## Day 9 — Thursday, 11/12: Demo and submit

- [ ] **Eric:** Present MiniDavis and submit source, notebooks, model, reports, recording and hosted URL or hosting status.
- [ ] **Saurya:** Run the frontend during the demo and save the final build.
- [ ] **Rylee:** Run the backend smoke checks and support reset/replay.
- [ ] **Aishani:** Explain agent decisions and fallback behavior.
- [ ] **Ethan:** Explain RAG using stored events and retrieved evidence.
- [ ] **Gayatri:** Explain fine-tuning results and submit the evaluation report/model.

**Finish:** Submit code, startup instructions, notebooks, model, evaluation report, and demo recording.

## Every meeting

1. Each person shows the assigned result or exact error.
2. Everyone runs the shared ML topic together when scheduled.
3. Eric assigns bug fixes to the responsible teammate and checks the next handoffs.

If behind, cut extra artwork, house building, elections and permanent hosting. Protect the core town, cloud model adapter, shared ML sessions, testing and demo practice. A local CPU app can still call Groq for live decisions.
