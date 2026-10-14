# MiniDavis — Team Plan

A 2D town with five AI residents. They move, gather food and wood, trade, talk, and remember interactions.

**Team:** Eric, Ethan, Gayatri, Aishani, Rylee, and Saurya.

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
- [ ] **Aishani:** Confirm LLM-provider account access with Eric; record the provider/model and agreed budget without posting keys.
- [ ] **Ethan:** Create the shared MiniDavis Google Drive folder and give the team access.
- [ ] **Gayatri:** Create an empty shared Colab notebook in that folder and confirm everyone can open it.

**Finish:** Everyone can open GitHub, Notion, Drive, and Colab. No coding, design, dataset preparation, or training today.

## Day 1 — Thursday, 10/15: Run the starter

- [ ] **Eric:** Create the project folders and shared configuration; connect frontend and backend.
- [ ] **Saurya:** Set up React and render the 12×12 map with five residents.
- [ ] **Rylee:** Set up FastAPI and implement `/health`, `/state`, and `/reset`.
- [ ] **Aishani:** Create the baseline-agent notebook and return one valid decision per resident.
- [ ] **Ethan:** Create the event store and memory notebook; save/read one sample event.
- [ ] **Gayatri:** Add starter tests, run them, and save the pass/fail output.

**Finish:** Everyone can run their assigned part of the starter project.

## Day 2 — Tuesday, 10/20: Run the simulation

- [ ] **Eric:** Connect the simulation loop and frontend controls to backend ticks.
- [ ] **Saurya:** Add Play, Pause, Next Turn, and Reset using the real backend.
- [ ] **Rylee:** Implement movement, gathering, eating, and resting; run 100 baseline ticks.
- [ ] **Aishani:** Add baseline action selection and destination-following for all five residents.
- [ ] **Ethan:** Store completed actions as memories and mark rejected actions as rejected.
- [ ] **Gayatri:** Add invalid-move and resource tests; report any negative inventory or crash.

**Finish:** Five residents move and gather safely through the UI.

## Day 3 — Thursday, 10/22: MVP + agents together

**Shared session:** Run the agent notebook, send an observation to the LLM, and inspect the returned action.

- [ ] **Eric:** Complete the MVP integration and record a two-minute working run.
- [ ] **Saurya:** Add the resident inspector and event log; check every resident.
- [ ] **Rylee:** Add model-action validation and run the MVP safety tests.
- [ ] **Aishani:** Implement the live LLM adapter and save five residents’ decisions.
- [ ] **Ethan:** Pass recent memories with real event IDs into the agent input.
- [ ] **Gayatri:** Run three seeded 100-tick MVP checks and save the report.

**MVP gate:** Town, five residents, controls, inspector, and log work. Baseline mode remains usable while live AI develops.

## Day 4 — Tuesday, 10/27: RAG together

**Shared session:** Save an interaction, retrieve it, and use it in an agent decision.

- [ ] **Eric:** Connect RAG to the backend and inspector; help Saurya and Rylee test it.
- [ ] **Saurya:** Display retrieved text and source event IDs in the inspector.
- [ ] **Rylee:** Run cross-resident and cross-run memory isolation tests.
- [ ] **Aishani:** Add retrieved memories to all five live agents’ prompts.
- [ ] **Ethan:** Implement recent + relevant memory retrieval and run 10 retrieval checks.
- [ ] **Gayatri:** Compare decisions with memory enabled and disabled; save one example of each.

**Finish:** Agents retrieve actual past events without leaking another resident’s private memory.

## Day 5 — Thursday, 10/29: Fine-tuning together

**Shared session:** Run the fine-tuning notebook to train a small interaction classifier: cooperation, conflict, trade, or neutral.

- [ ] **Eric:** Prepare the dataset with Gayatri and help the team run the notebook in Colab.
- [ ] **Saurya:** Add an interaction-label field to the UI.
- [ ] **Rylee:** Implement trade offers and acceptance; run duplicate-acceptance tests.
- [ ] **Aishani:** Review examples 001–050 and correct wrong labels.
- [ ] **Ethan:** Review examples 051–100 and check that scenario families stay in one data split.
- [ ] **Gayatri:** Prepare the training notebook, review examples 101–200, train, and save the model and validation results.

**Finish:** Train on the fixed training split, choose using validation, and save a trained classifier. Keep test data untouched until Day 6. Fine-tune the classifier, not the main LLM.

## Day 6 — Tuesday, 11/03: Integrate and freeze features

- [ ] **Eric:** Finish integration, run the whole app, and resolve blocking issues.
- [ ] **Saurya:** Check shortage controls, trade status, memories, and classifier labels on screen.
- [ ] **Rylee:** Finish atomic trading, shortage, reset, and replay; run their checks.
- [ ] **Aishani:** Add timeout/invalid-output fallback and call limits; test live and failure modes.
- [ ] **Ethan:** Update memories and relationships from actual completed interactions.
- [ ] **Gayatri:** Evaluate the frozen classifier on held-out test data and run the integration checklist.

**Integration gate:** Live agents, RAG, trades, shortage, classifier predictions, and frontend work together. Keep fixed relationship rules; the classifier supplies an observable label. Freeze new features after this meeting.

## Day 7 — Thursday, 11/05: Stabilize and compare

- [ ] **Eric:** Reproduce and fix bugs with the responsible teammate; help backend/frontend owners rerun checks.
- [ ] **Saurya:** Run a 30-minute UI session and report slow rendering or broken controls.
- [ ] **Rylee:** Run 1,000 baseline ticks and confirm no corrupted resources or positions.
- [ ] **Aishani:** Run provider-failure checks and check repeated/invalid plans.
- [ ] **Ethan:** Rerun retrieval and memory-isolation checks.
- [ ] **Gayatri:** Run matched baseline, LLM-only, and LLM + RAG comparisons; save metrics.

**Finish:** Tested runs have no crashes or invariant failures; evaluation results are saved.

## Day 8 — Tuesday, 11/10: Rehearse

- [ ] **Eric:** Prepare the five-minute script and lead two rehearsals.
- [ ] **Saurya:** Operate the town and check projector readability.
- [ ] **Rylee:** Check clean-machine startup and the known-good replay.
- [ ] **Aishani:** Check live model access and labelled fallback.
- [ ] **Ethan:** Prepare one real remembered-interaction example for the demo.
- [ ] **Gayatri:** Check presentation numbers and record a local backup demo.

**Finish:** Two five-minute rehearsals pass, including recovery from a provider failure.

## Day 9 — Thursday, 11/12: Demo and submit

- [ ] **Eric:** Present MiniDavis and collect the final submission links.
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

If behind, cut extra artwork, house building, elections, and hosting. Protect the core town, shared ML sessions, testing, and demo practice.
