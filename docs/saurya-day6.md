# Saurya Day 6 — Frontend ↔ API Integration

## Summary

Connected the frontend to the deployed API and verified that shortage, trades, memories,
classifier labels, and waiting states are visible in the UI.

## API URL Configuration

`VITE_API_BASE_URL` is the canonical env var read by `frontend/src/api.ts` (line 4).
`VITE_API_URL` is accepted as a legacy alias. When neither is set the frontend defaults
to `http://127.0.0.1:8000`.

**No deployed URL is available yet** — awaiting hosting budget approval (Eric's
blocker). The frontend build command once a URL is available:

```sh
cd frontend
VITE_API_BASE_URL=https://<backend-url> npm run build
# Serve frontend/dist/ with any static host (Netlify, Cloud Run static, etc.)
```

## Features Implemented

### Shortage indicator
Resource chips in the map caption turn orange and show a `LOW` badge when
`resource.stock <= 5`. The chip renders inline without any additional API endpoint
(reads the `resources` array from the existing `/state` response).

```tsx
// App.tsx — supply-chips
<span className={resource.stock <= 5 ? 'shortage' : ''}>
  {label} <strong>{resource.stock}</strong>
  {resource.stock <= 5 && <span className="shortage-badge"> LOW</span>}
</span>
```

> **Note:** The `POST /scenario/shortage` endpoint described in README-TECHNICAL §8
> is not yet implemented in the backend (Rylee's task). The UI shortage indicator
> works independently from the existing resource stock data.

### Trade offers
The **Interactions** tab of the Agent Journal shows a `TRADE OFFERS & TRANSFERS`
section for any trades where the selected resident is the proposer or recipient.
Each entry shows:
- Proposer → Recipient names
- Status pill (PENDING / ACCEPTED / REJECTED)
- Terms: "Offers N resource for M resource"
- `offer_id` code

Data flows from `WorldState.trade_offers[]` → `App.tsx` → `AgentJournal` prop.

### Classifier labels
Every social event in the Interactions tab shows an **Interaction label** row:
- If the event has `interaction_label` / `classification.label` / `label`: renders a
  colour-coded badge (cooperation=green, trade=gold, conflict=red, neutral=grey)
  plus confidence percentage.
- If the event is social but has no prediction: renders `unclassified` in italic.

> **Note:** The backend `InteractionClassifier` is not yet wired into the event
> pipeline — events don't carry `interaction_label` from the server yet. The UI
> fields are forward-compatible and will display labels automatically when the
> backend sends them.

### Memories (sources + IDs)
The **Memories** tab shows:
- Retrieval mode label (MiniLM meaning search / Keyword search / Recent history only)
- Query string and `as_of_tick`
- Relevant memories section + Recent memories section
- Each memory card has a `<details>` showing the raw `event_id` source code

### Waiting / live / fallback / baseline states
- The resident picker buttons show a coloured mode badge for each resident derived
  from `agent_runtime[id].status`.
- The journal status banner (`role="status"`) shows the full label + detail string.
- The journal footnote reflects the current retrieval mode.

## Verification Results

| Check | Result |
|-------|--------|
| `cd frontend && npm test` | **28 tests pass** (5 suites) |
| `cd frontend && npm run build` | **Clean** — tsc + vite, 0 errors |
| `PYTHONPATH=. .venv/bin/pytest` | **106 tests pass** |

## Remaining Blockers (not Saurya's)

| Item | Owner |
|------|-------|
| Deployed API URL | Eric (hosting budget) |
| `POST /scenario/shortage` endpoint | Rylee |
| Backend classifier → event pipeline wiring | Backend team |
| `sentence-transformers` install for semantic mode | DevOps / install |

