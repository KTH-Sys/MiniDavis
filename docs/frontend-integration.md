# Frontend integration

PR #1 (`saurya/frontend`) originally introduced a standalone React application under `minidavis-frontend/`. Main subsequently gained the shared TypeScript frontend, safe backend controls, memory inspector, animated town and black terminal theme under `frontend/`.

The PR is reconciled into that shared application. Its original commits remain in the merge history. Use `frontend/` for all new frontend work; `minidavis-frontend/README.md` points existing checkouts to the current commands.

| Original contribution | Shared implementation |
| --- | --- |
| React + Vite starter | `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx` |
| 12×12 map with five named residents and movement | `frontend/src/components/TownMap.tsx`, `PixelResident.tsx` |
| Play, Pause, Next Turn, Reset | `frontend/src/components/Controls.tsx`, `frontend/src/hooks/useTown.ts` |
| Backend `/state`, `/step`, `/reset` calls | `frontend/src/api.ts` |
| Configurable API URL | `VITE_API_BASE_URL`, with `VITE_API_URL` accepted as a compatibility alias |
| Connection/error status | Town connection indicator, error banner and Reconnect button |

The shared controls already protect against overlapping requests and responses arriving after Reset. Offline mock positions from the earlier starter are replaced by an explicit connection state; the shared UI displays actual simulation data. Generic React/Vite template assets, a second dependency lockfile and tracked `.DS_Store` are removed from the final tree.

Local verification: 32 backend tests and 19 frontend tests pass; the production build succeeds. Seeds 11, 22 and 33 each complete 100 baseline ticks with zero invariant failures and zero provider calls. Browser verification covers controls, real memory sources and responsive terminal layout. GitHub checks must pass on the reconciled PR head before merge.
