# Deployment and business model

## Prototype deployment

| piece | option | notes |
|---|---|---|
| backend | Render / Railway / Fly.io (Docker or `uvicorn backend.app.main:app`) | set `CROWDPULSE_DATABASE_URL=postgresql+psycopg://…` (Supabase), `CROWDPULSE_CORS_ORIGINS=https://<dashboard>`, `CROWDPULSE_LIVE_SIM=false` for real sensing; install `.[postgres]` extra |
| database | Supabase Postgres | tables are created automatically on start (`Base.metadata.create_all`) |
| dashboard | Vercel | `NEXT_PUBLIC_API_URL=https://<backend>` |
| iOS | Xcode local install / TestFlight | App Store submission is not on the critical path |
| local demo | SQLite + built-in live simulation | zero infrastructure |

Security for the prototype: HTTPS at the platform edge, secrets only in environment variables, closed input schema with bounds, per-IP rate limiting on ingestion, no file uploads or code execution paths. Not in scope: authentication (add a simple bearer token per sensor kit before any real deployment).

## Operational model

Temporary "smartphone sensing kits" (phone + tripod/clamp + battery pack + laminated instructions) are deployed by Macau tourism authorities, police, event staff or crowd-management contractors for peak periods (Golden Week, Chinese New Year, Grand Prix, festivals). Staff place phones at agreed points around each hotspot in the morning, register them in the app, and collect them in the evening. The dashboard runs in the operations room.

## One-year cost model (assumptions stated; illustrative, not quoted prices)

| item | assumption | cost (MOP, approx.) |
|---|---|---|
| 20 refurbished/loan smartphones + mounts + power banks | MOP 2,500 per kit, 3-year life | 50,000 / 3 ≈ 17,000 per year |
| cloud backend + database | small managed instance + Postgres | ≈ 6,000 per year |
| staff time for placement/collection | 2 staff × 4 h × 40 peak days × MOP 100/h | ≈ 32,000 per year |
| maintenance / retraining / support | 0.2 FTE engineer | ≈ 60,000 per year |
| **total** | | **≈ MOP 115,000 per year** |

For comparison, a permanent smart-CCTV analytics point is commonly quoted in the tens of thousands of MOP each for hardware, cabling and installation, plus licences — 20 such points would exceed this budget several times over and would still not be movable. The smartphone approach reuses commodity hardware, can be repositioned daily, and collects far less sensitive data. All figures are assumptions for discussion, not supplier quotes.
