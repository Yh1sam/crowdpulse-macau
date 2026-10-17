# CrowdPulse operator dashboard

Next.js 16 + React 19 + MapLibre console for the CrowdPulse backend: Overview, Live map, Zone detail, Alerts, Interventions, AI explanation, Reliability, Evaluation and Privacy (9 pages, `src/app/`).

- Run: start the backend first (`.venv/bin/uvicorn backend.app.main:app --port 8000` from the repository root), then `pnpm install && pnpm dev` here and open http://localhost:3000. Node version: see `engines` in `package.json` and the repository's `.nvmrc`.
- Settings: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) and `NEXT_PUBLIC_SKETCHFUTURE_URL` (default `http://localhost:4173`, the route check opened by TEST IN SKETCHFUTURE).
- Decisions: type a name under "Deciding as" (Alerts and Interventions pages) before APPROVE, REJECT or ack (the buttons stay disabled until a name is set). The name is self-declared (no login), kept in this browser's localStorage and written to the audit log as the actor; the backend refuses an empty name, "operator" and "system".
- Tests: `pnpm test` (vitest + jsdom, 24 tests in `src/__tests__/`). Production build: `node node_modules/next/dist/bin/next build`.
- The Evaluation page shows results on **synthetic** held-out days from `ml/models/metrics.json`, not field accuracy.
- The Live map loads OpenStreetMap tiles over the internet. `maplibre-gl` stays on 4.x: 5.x and 6.x load a separate worker module that Turbopack does not emit.
- Full demo walkthrough and timings: the repository [README](../README.md#demo-about-3-minutes-on-stage); test procedures: [docs/testing.md](../docs/testing.md).
