# Frontend moved to `frontend/`

MiniDavis uses one frontend in [`../frontend/`](../frontend/). Saurya's Day 1–2 React setup, 12×12 resident map and backend playback controls are consolidated there with the current animated town and terminal feed. The original work remains in Git history in commits `03356da` and `80e7caa`.

From this directory:

```bash
cd ../frontend
npm ci
npm run dev
```

Use `VITE_API_BASE_URL` to change the backend URL. The earlier `VITE_API_URL` setting is also accepted when `VITE_API_BASE_URL` is unset. The shared app uses actual backend state and provides a reconnect action if the backend is unavailable.

Run tests and build from `frontend/` with `npm test` and `npm run build`. See the [project startup instructions](../README.md#run-minidavis).
