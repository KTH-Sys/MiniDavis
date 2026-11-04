# MiniDavis CPU preview deployment

Prepared November 3, 2026. **No hosted service has been created.** Eric's current hosting decision is a free Render static frontend plus an optional free **baseline-only** CPU API preview. The full ML preview is blocked by the missing trained classifier, unmeasured combined RAM, and an unconfigured persistent budget store. No paid budget is approved.

## Local integrated mode

Use the existing startup commands in [README](../README.md). Add these server-only settings to ignored `backend/.env` as needed:

```dotenv
MINIDAVIS_MODE=llm
MEMORY_RETRIEVAL_MODE=semantic
CLASSIFIER_MODEL_PATH=ml/artifacts/classifier
CLASSIFIER_REQUIRED=false
```

The classifier path must contain Gayatri's actual exported model, tokenizer and four-label config. Until it is supplied, events display **unclassified**; no heuristic is presented as a trained model. `/ready` reports whether loading succeeded. Set `CLASSIFIER_REQUIRED=true` for a full-ML readiness gate: missing/invalid exports then prevent startup. The label mapping must match cooperation=0, conflict=1, trade=2, neutral=3.

## Optional free baseline preview

The root [render.yaml](../render.yaml) packages a static React site and a one-worker FastAPI service. Its defaults use baseline/keyword modes, no model weights and no Groq key. This is a baseline preview, not the completed ML demo. Render documents the [FastAPI deployment commands](https://render.com/docs/deploy-fastapi) and [free-service limitations](https://render.com/docs/free).

1. After the branch is merged, connect the repository to an authorized Render account and review the blueprint. Do not change to a paid plan without an agreed budget.
2. Set `VITE_API_BASE_URL` to the API's actual HTTPS URL. Set server `FRONTEND_ORIGINS` to the static site's actual HTTPS origin. Rebuild the static frontend after changing its API URL.
3. Keep `REQUIRE_OPERATOR_TOKEN=true`. Render generates a server `OPERATOR_TOKEN`; Eric uses that operator key in the town's **Operator access** form. It is kept only in that browser tab. Give ordinary viewers just the site URL.
4. Never place Groq credentials or the operator key in `VITE_*`, the JavaScript bundle or Git. They are different keys with different purposes.
5. Check `/health` and `/ready`. Verify viewers can read the town and export traces, but an unauthenticated POST to `/step`, `/reset`, `/scenario/shortage` or `/replay` returns 401.
6. Have one operator advance the town while another viewer watches. Paused tabs poll the same `/state`; reads do not create model calls or advance time.
7. Use **Save run** before a restart. **Replay saved run** re-executes the recorded actions with checksum/outcome validation and no provider calls. Replay cannot advance until Reset starts a fresh run.

Free services sleep after inactivity and discard local filesystem changes on restart/redeploy. The town always starts a new run after restart; SQLite retains history only where the disk itself persists. Do not describe the free preview as durable or always available. [Render's storage/restart behavior](https://render.com/docs/free).

## Full ML preview: finish these gates first

- Obtain the actual classifier export and its validation report/frozen dataset manifest from Gayatri. Keep large weights outside Git.
- Install the optional embedding/classifier dependencies on the chosen Linux CPU host. The supplied Python pins are not a claim that Linux installation or a Docker image has been tested; this work was verified on the local Mac.
- Run `python scripts/measure_deployment.py` with both models loaded. Choose a host using its actual measured RAM needs, not the baseline process size. The current report records the missing classifier as a blocker.
- Configure durable SQLite storage (including `llm-budget.sqlite`) or a shared persistent budget service before enabling a live public preview. Free ephemeral storage resets application counters; it cannot preserve account-wide daily budget enforcement after restart.
- Use one backend worker/town scheduler. Multiple independent machines or Colab clones do not share the local SQLite budget; Groq limits apply across the organization. Check the account's actual limits and reserve the demo allowance privately. [Groq limits](https://console.groq.com/docs/rate-limits).
- Set server Groq secrets and `MINIDAVIS_MODE=llm`, enable semantic retrieval, set `CLASSIFIER_REQUIRED=true`, and verify real CPU inference plus the interaction label in the UI.
- Repeat operator/viewer, CORS, reset, shortage, trade, source-isolation and replay checks against the actual deployed URLs. Record the hosting account, URLs, measured RAM and budget before claiming deployment complete.

The local implementation and free-preview blueprint are ready for review. Trained-model loading, combined-RAM sizing and actual hosted deployment remain unverified.
