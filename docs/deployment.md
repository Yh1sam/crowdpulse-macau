# Deployment and business model

## Prototype deployment

| piece | option | notes |
|---|---|---|
| backend | Render / Railway / Fly.io (Docker or `uvicorn backend.app.main:app`) | set `CROWDPULSE_DATABASE_URL=postgresql+psycopg://…` (Supabase), `CROWDPULSE_CORS_ORIGINS=https://<dashboard>`, `CROWDPULSE_LIVE_SIM=false` for real sensing; install `.[postgres]` extra |
| database | Supabase Postgres | tables are created automatically on start (`Base.metadata.create_all`) |
| dashboard | Vercel | `NEXT_PUBLIC_API_URL=https://<backend>` |
| iOS | Xcode local install / TestFlight | App Store submission is not on the critical path |
| local demo | SQLite + built-in live simulation | zero infrastructure |

Zone placement: inside the district a phone is placed by GPS; elsewhere the zone chosen in the app is used, at any distance. For a live deployment in Macau set `sensor.zone_hint_max_distance_m` in `shared/config.json` (for example 360), so a phone carried away from its post stops feeding its zone; the Reliability page shows each phone's placement and its distance from the zone.

Security for the prototype: HTTPS at the platform edge, secrets only in environment variables, closed input schema with bounds, per-IP rate limiting on ingestion, no file uploads or code execution paths. Not in scope: authentication (add a simple bearer token per sensor kit before any real deployment).

## Operational model

Temporary "smartphone sensing kits" (phone + tripod/clamp + battery pack + laminated instructions) are deployed by Macau tourism authorities, police, event staff or crowd-management contractors for peak periods (Golden Week, Chinese New Year, Grand Prix, festivals). Staff place phones at agreed points around each hotspot in the morning, register them in the app, and collect them in the evening. The dashboard runs in the operations room.

## One-year cost

See [cost-estimate.md](cost-estimate.md) for the one-year build and running estimate. It is labelled **TEAM ESTIMATE — draft, inputs to be confirmed by the team; not a quote.** No published price for a fixed counting camera was found ([research/brief-evidence.md](research/brief-evidence.md), section 8), so no comparison is made.
