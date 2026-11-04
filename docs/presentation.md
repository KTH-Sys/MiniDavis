# MiniDavis presentation guide

**Pitch:** “MiniDavis is a tiny town for AI agents. Each resident has a goal, sees the world, retrieves memories and asks a language model what to do. The town checks whether that action is legal. A smaller model we fine-tuned labels their interactions.”

## Before the room opens

- [ ] Pull the final `main` and install the supplied classifier package. Weights are separate from Git.
- [ ] Run the backend and frontend using the root README. Open the app on the actual presentation computer.
- [ ] Confirm `/ready`: classifier loaded, semantic retrieval requested, expected operator setting. In Memories, confirm the actual retrieval mode says MiniLM meaning search.
- [ ] Confirm `/health`: `mode=llm` and `live_llm_enabled=true`. A real cached/live decision, rather than just key configuration, verifies provider access.
- [ ] Check remaining Groq allowance and leave it for the demo. The saved six-run comparison already used twenty calls; do not rerun it unnecessarily.
- [ ] Check projector readability and browser zoom. Rehearse using the same display and network.
- [ ] Save any current run before replacing it. Load sample once, inspect Ethan/Saurya, then start a fresh live town if beginning with live AI.
- [ ] Keep the sample run, model ZIP and the two saved screenshots available locally for recovery.
- [ ] Rehearse twice. A thirty-minute two-viewer rehearsal remains a team activity; automated tests are not evidence that it happened.

## Five-minute speaking and operating script

| Time | Speaker | What to say/show |
| --- | --- | --- |
| 0:00–0:35 | Eric | Introduce the tiny town and the five residents. Explain the project question: can agents use goals and memories within a rule-governed world? |
| 0:35–1:20 | Aishani / Saurya | Select Live AI and start a new town. Advance once, wait for the reply, then advance again. Show the executed decision separately from the model's explanation and point to live/cached/fallback status. |
| 1:20–2:00 | Ethan | Open Memories. Show a real event ID and a previous action. Explain that RAG retrieves stored evidence before the next decision; it does not train Qwen. Say whether the actual mode is semantic or keyword search. |
| 2:00–2:50 | Rylee / Saurya | Load the sample run and say: “This is a scripted mechanics demonstration, with no AI calls.” Select Ethan or Saurya, show accepted trade, speech, farm stock and the +2 relationship change under Decision. Explain that the engine moves resources once and validates nearby participants. |
| 2:50–3:45 | Gayatri | Open Try the trained classifier. Classify the example with the real CPU model. Explain the four labels and show the saved comparison: 85% test accuracy on 40 synthetic examples versus 72.5% for the simpler baseline. Credit the available checkpoint and the two-epoch completion; do not claim ten completed epochs. |
| 3:45–4:30 | Aishani | Explain missing-key, timeout and quota fallback. Point out that replay makes no new model calls and a configured API key differs from a trained classifier. Use saved failure-test evidence rather than deliberately changing secrets during the talk. |
| 4:30–5:00 | Eric | State what was measured and the limits: small synthetic test, short exploratory town comparison and no guaranteed autonomous completed trade. Finish with what the team learned about agents, memory and fine-tuning. |

## If the live service fails

1. Read the status reason: waiting, invalid reply, missing key, quota or fallback. Do not present fallback as a live model decision.
2. Avoid repeatedly pressing Next Turn. Pending replies disable that control; live Play waits and paces turns.
3. Load the sample run and continue with the clearly labelled mechanics demonstration.
4. The classifier works locally once installed and can still demonstrate real fine-tuned inference. Show the saved live screenshot and evaluation results if network access is unavailable.
5. If the frontend cannot reach the backend, check startup, API URL and CORS, then use Reconnect. `/ready` reports model loading. Missing required classifier files intentionally stop the strict presentation backend; install the package before restarting.

## How to describe the evidence

- Classifier: selected using validation, then tested once on 40 synthetic examples. It can make errors; confidence is not certainty.
- Town comparison: one seed, three modes and two scenario labels, with one planning window per live episode. All twenty proposals were valid, but most later actions were cached or baseline fallback. Three talks and two offers occurred; no autonomous trade completed.
- The tick-30 shortage did not reduce stock further because the starter farm was already empty. These runs do not establish a distinct shortage effect. The early sample shortage does demonstrate the control changing stock.
- RAG prompts contained actual private source events. No causal improvement or statistical significance is claimed.
- Local RAM and startup passed. No hosted URL, production durability or Linux deployment is claimed. A local presentation is sufficient.

## Submission handoff

- [ ] Source at the final `main` commit and the new root README.
- [ ] Classifier ZIP, model card and validation/test reports.
- [ ] Notebooks with offline-safe defaults and the frozen dataset manifest.
- [ ] Comparison, source-isolation, state-safety and browser evidence in `results/presentation/`.
- [ ] Live and sample screenshots in `docs/assets/`; a team-recorded video if the submission requires one.
- [ ] Hosting status stated honestly: local demo, no public deployment.
