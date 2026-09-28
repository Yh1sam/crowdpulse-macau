# CrowdPulse Macau

**Privacy-preserving smartphone crowd intelligence for Macau's tourist district.**
Hackathon prototype for the Imperial College London Global Hackathon 2026 — High School Track, Challenge 2(c): Responsible AI.

> Research question: *How accurately can a distributed network of commodity smartphones predict short-term pedestrian congestion while minimising identifiable data collection?*

## Problem

During Golden Week, hotspots such as the Ruins of St. Paul's and Senado Square become dangerously crowded, and operators struggle to see where crowds will move *next*. Permanent CCTV/LiDAR networks are expensive and raise surveillance concerns.

## Solution

CrowdPulse turns ordinary smartphones, temporarily placed by authorised staff, into anonymous crowd sensors:

```
phone camera → on-device person detection (anonymous boxes) → numerical metadata only
      → backend aggregation per zone → congestion forecast (+5 / +10 / +15 min) with confidence
      → reliability / OOD checks → explanation → operator dashboard → human-approved intervention
```

Only numbers leave the phone (count, density index, flow direction/speed, GPS, heading, stability, confidence). **No facial recognition, no identifiable video, no persistent pedestrian identity.** The AI recommends; a human operator decides; every decision is audited.

## Architecture

```
ios/CrowdPulseSensor     Swift/SwiftUI sensor node (AVFoundation + Vision + CoreMotion + CoreLocation)
backend/app              FastAPI: ingestion, zone aggregation, prediction, alerts, interventions, audit, exports
ml/synthetic             mesoscopic crowd-flow simulator with sensor failure modes (same schema as real phones)
ml/pipeline              observation → zone-state aggregation, lag features, OOD detector, explanations
ml/training, ml/evaluation   model comparison, metrics, presentation figures (all from real runs)
dashboard/               Next.js + MapLibre operator console (8 pages)
shared/                  ONE config file (thresholds, confidence, reliability), zone graph, observation schema
docs/                    architecture, privacy, model card, experiment protocol, deployment, notes
experiments/results/latest   evaluation figures + metrics table produced by the last evaluation run
```

See [docs/architecture.md](docs/architecture.md) for the system diagram and data flow.

## Setup

Requirements: Python 3.12, Node 20+, pnpm (or npm), Xcode 16+ for the iOS app.

```bash
# Python (backend + ML)
uv venv --python 3.12 && uv pip install --python .venv/bin/python -e ".[dev]"
# or: python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# 1. synthetic data (14 simulated days + a rain/closure stress day)
.venv/bin/python -m ml.synthetic.generate --days 14 --interval 20 --out ml/data
.venv/bin/python -m ml.synthetic.generate --scenario stress_rain_closure --out ml/data --prefix stress

# 2. train + evaluate (writes ml/models/*.joblib, metrics.json, experiments/results/latest/*.png)
.venv/bin/python -m ml.training.train
.venv/bin/python -m ml.evaluation.evaluate

# 3. backend (starts the accelerated Golden-Week demo simulation by default)
.venv/bin/uvicorn backend.app.main:app --port 8000      # OpenAPI docs: http://localhost:8000/docs

# 4. dashboard
cd dashboard && pnpm install && pnpm dev                 # http://localhost:3000

# tests
.venv/bin/python -m pytest -q          # backend API + ML pipeline
cd dashboard && pnpm test              # component tests
```

Environment variables (all optional, prefix `CROWDPULSE_`): `DATABASE_URL` (default SQLite; use a Postgres/Supabase URL for deployment), `LIVE_SIM` (default true), `SIM_ACCELERATION`, `CORS_ORIGINS`, `PRIVACY_MODE` (default true; the only supported setting). Domain thresholds live in `shared/config.json`.

## Demo (under 3 minutes)

1. Start backend + dashboard. The simulated clock starts at 13:45 on a Golden-Week afternoon; sensors report every 5 s at 6× speed.
2. **Overview / Live map**: Senado Square is WARNING; flows are southbound from the Ruins.
3. ~14:04 a performance at St. Dominic's Square ends and tour groups surge in from Almeida Ribeiro. Density and inflow rise; walking speed falls.
4. **Zone detail → Senado Square**: the +10/+15 min forecast turns CRITICAL with its confidence, and "why" reasons (density change, inflow > outflow, adjacent zone filling, speed falling).
5. **Interventions**: the recommendation ("redirect part of the southbound flow via the Rua da Tercena corridor", accessibility check, zh/en/pt notices). Click **VIEW EVIDENCE**, then **APPROVE**. The decision is written to the audit log, the assumed inflow reduction is applied to the simulation and the forecast is recalculated.
6. **Reliability**: sensor health; predictions from unreliable zones show *LOW CONFIDENCE — HUMAN REVIEW REQUIRED*. **Evaluation**: real accuracy / F1 / confusion matrices from the last training run.
7. Optional: the status bar has *inject surge (Senado)* to trigger a sudden surge; use the iOS app on a phone pointed at a group of people to see a real node appear on the map.

## Results (synthetic held-out test days, from `ml/models/metrics.json`)

| horizon | model | accuracy | F1 (macro) | persistence-baseline F1 | accuracy vs simulation ground truth | density MAE |
|---|---|---|---|---|---|---|
| +5 min | random forest | 0.969 | 0.887 | 0.849 | 0.974 | 0.017 |
| +10 min | random forest | 0.966 | 0.876 | 0.827 | 0.972 | 0.019 |
| +15 min | random forest | 0.964 | 0.865 | 0.795 | 0.972 | 0.020 |

Low-confidence gating: predictions flagged for human review (≈2% of all) are right only ~55% of the time versus ~97% for the rest. On the rain + closure + surge stress day, macro-F1 drops to ≈0.61–0.64 and the OOD detector flags ≈14% of inputs (vs ≈1–2% on normal days). Full tables and figures: `experiments/results/latest/`, and the dashboard's Evaluation page. These are **synthetic** results; see the model card for what they do and do not show.

## Limitations (honest summary)

- All accuracy numbers come from a simulator that we wrote; real-world accuracy is unknown until the controlled experiments in `docs/experiment-protocol.md` are run.
- The density index is relative (0–1), not persons per m². Thresholds are experimental.
- Camera person detection undercounts in dense crowds (occlusion); the timeline figure shows observed density saturating near 0.8 while the simulated truth reaches 1.0.
- The WARNING class (transitional) is the hardest: F1 ≈ 0.73–0.77 vs ≈0.90 for CRITICAL.
- Intervention effects are assumptions (30% inflow diversion), not validated causal estimates.
- One phone sees one part of a zone; the zone estimate depends on calibration of each phone's visible capacity.

Documented failure cases: `docs/model-card.md` (occlusion, rain/umbrellas, obstruction not flagged, device movement, unusual days, single-sensor dropout).
