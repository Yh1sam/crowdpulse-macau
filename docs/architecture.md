# Architecture

## System diagram

```
┌──────────────────────────── iOS sensor node (per phone) ────────────────────────────┐
│ camera / video ─► on-device person detector (YOLO11n CoreML) ─► anonymous boxes      │
│                                   │  count · box-area density proxy · centroid flow  │
│ CoreMotion (accel/gyro) ─► stability score        CoreLocation ─► GPS + heading      │
│                                   ▼                                                  │
│                    SensorObservation (numbers only)  ─► buffer ─► POST /sensor/...   │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                          │  (or: synthetic generator / replay, SAME schema)
                                          ▼
┌───────────────────────────────── backend (FastAPI) ──────────────────────────────────┐
│ ingestion: schema validation (extra fields forbidden) · GPS→zone assignment ·         │
│            per-observation quality weight · SQLite/Postgres                           │
│ engine.refresh() every 2 s:                                                           │
│   ml.pipeline.aggregation  → zone state per 1-min bin (density, flow, reliability,    │
│                              disagreement, inflow/outflow proxies via zone graph)    │
│   ml.pipeline.features     → lag features, neighbour context, time, operator context │
│   prediction service       → class + probability per horizon, density regressor,     │
│                              reliability factor, OOD check, effective confidence,    │
│                              rule-based reasons + sensitivity contributions          │
│   alerts · intervention engine (rules + accessibility-scored routes + zh/en/pt text) │
│   audit log · retention                                                               │
│ live simulation (optional): CrowdSimulator on an accelerated clock feeding ingestion │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                          │ REST (OpenAPI at /docs), polled every 2–3 s
                                          ▼
┌───────────────────────────── dashboard (Next.js + MapLibre) ─────────────────────────┐
│ Overview · Live map · Zone detail · Alerts · Interventions (APPROVE/REJECT/EVIDENCE) │
│ AI explanation · Reliability · Evaluation (real metrics + figures) · Privacy         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## Components

| component | stack | key modules |
|---|---|---|
| iOS sensor node | Swift, SwiftUI, AVFoundation, Vision, CoreMotion, CoreLocation | `ios/CrowdPulseSensor/` — `PersonDetector` (YOLO11n CoreML, Apple fallback), `VisionProcessor`, `MotionMonitor`, `LocationMonitor`, `Uploader`; `Tools/videoeval` runs the same code over video on a Mac |
| backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2, SQLite (Postgres/Supabase via `DATABASE_URL`) | `backend/app/services/engine.py`, `prediction.py`, `intervention.py`, `live_sim.py` |
| ML | pandas, numpy, scikit-learn | `ml/pipeline/{aggregation,features,ood,explain}.py`, `ml/training/train.py`, `ml/evaluation/evaluate.py` |
| synthetic data | pure Python | `ml/synthetic/{simulator,scenarios,generate}.py` |
| dashboard | Next.js 16, React 19, TypeScript, Tailwind 4, MapLibre GL, Recharts, SWR | `dashboard/src/app/*`, `dashboard/src/components/*` |
| shared | JSON | `shared/config.json` (one central config), `shared/zones.json` (graph), `shared/schemas/` |

## Key design decisions

1. **One schema, one pipeline.** Synthetic observations, replayed observations and real phone observations are validated by the same Pydantic model and aggregated by the same code (`ml.pipeline.aggregation`) both offline (training) and online (backend). The backend imports the ML package; there is no duplicated feature logic.
2. **Zone graph, not a grid.** Seven zones (nodes) and seven corridors (edges, with length, capacity, stairs/steepness) drive neighbour features, the inflow/outflow proxies and the alternate-route search for interventions.
3. **Observable proxies only.** Inflow/outflow are proxies computed from anonymous flow vectors projected onto edge bearings, weighted by density, speed and flow coherence — nothing needs per-person tracking.
4. **Reliability is first-class.** Every observation gets a quality weight (stability, obstruction, GPS accuracy, vision confidence); zone reliability combines sensor availability, quality and inter-sensor disagreement; prediction confidence is scaled by it and low values trigger human review.
5. **Simulated clock.** With the built-in live simulation the backend runs on the simulation's accelerated clock so that horizons, staleness and bins stay consistent; with real phones it uses wall-clock time. A run stops at the end of its scenario (the demo is 120 simulated minutes) and the backend returns to wall-clock time, so a run left going cannot drift days ahead.
6. **Human in the loop.** Interventions are records with `pending/approved/rejected/expired/superseded` status; approval is an explicit API call recorded in `audit_log`. A stronger recommendation (monitoring → staff → redirect / inflow control) supersedes a weaker pending one; an approved one stays approved and the stronger one is added alongside. In simulation, approval feeds an assumed inflow reduction back into the crowd model.
7. **Graceful degradation.** Missing models → persistence fallback flagged as such; missing sensors → stale zone + "insufficient data — human review"; backend down → phone buffers numbers and retries.
8. **Hybrid mode.** While the live simulation runs, real sensors can join it: their wall-clock readings are re-timed onto the simulated clock (their real age is scaled by the simulation speed). Stopping or restarting the simulation closes that run's recommendations and hides its future-dated readings and alerts.

## Data model

`sensors`, `observations`, `zone_states` (unique per zone/minute), `predictions`, `alerts`, `interventions`, `audit_log`, `ground_truth` (controlled experiments). All numeric/categorical; no blobs.

## API (minimum set + extras)

`POST /sensor/observation` (single or batch) · `GET /sensors` · `GET /zones` · `GET /zones/{id}` · `GET /zones/{id}/history` · `GET /zones/{id}/prediction` · `GET /zones/{id}/prediction/history` · `POST /zones/{id}/context` · `GET /alerts` · `POST /alerts/{id}/ack` · `GET /interventions` · `POST /interventions/{id}/approve|reject` · `GET /audit` · `GET /model/metrics` · `GET /model/status` · `GET /health` · `GET /config` · `GET|POST /sim/*` · `GET /export/{table}.csv` · `POST /experiments/ground-truth` · `GET /experiments/results[.csv]` · static `/evidence/*.png`.

## Performance (measured locally, Apple Silicon)

- Aggregation of 312k observations → 81k zone-minute states: ≈1.3 s (vectorised pandas).
- Backend refresh (aggregate recent window + 21 predictions + explanations): ≈100–250 ms; API reads < 50 ms.
- Training all models for three horizons: ≈70 s.
- On-device detection, measured on a Mac with the app's own code: YOLO11n ≈6 ms per 640×360 frame, Apple's built-in detector ≈5 ms. Phone frame rate has not been measured yet; the app throttles to 10 FPS.
