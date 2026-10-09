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
sketchfuture/            SketchFuture: offline route + queue model on Macau's OSM streets, opened from intervention cards
shared/                  ONE config file (thresholds, confidence, reliability), zone graph, observation schema, SketchFuture crosswalk
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

# 5. optional: SketchFuture, the route check opened from intervention cards
cd sketchfuture && npm install && npm run dev            # http://localhost:4173

# tests
.venv/bin/python -m pytest -q          # backend API + ML pipeline
cd dashboard && pnpm test              # component tests
```

Environment variables (all optional, prefix `CROWDPULSE_`): `DATABASE_URL` (default SQLite; use a Postgres/Supabase URL for deployment), `LIVE_SIM` (default true), `SIM_ACCELERATION`, `CORS_ORIGINS`, `PRIVACY_MODE` (default true; the only supported setting). Domain thresholds live in `shared/config.json`. The dashboard reads `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_SKETCHFUTURE_URL` (default `http://localhost:4173`).

## Demo (under 3 minutes)

1. Start backend + dashboard. The simulated clock starts at 13:45 on a Golden-Week afternoon; sensors report every 5 s at 6× speed. The run stops by itself at 15:45, the end of the scenario (about 19 minutes of real time); press *start demo sim* to run it again.
2. **Overview / Live map**: Senado Square is WARNING; flows are southbound from the Ruins.
3. ~14:04 a performance at St. Dominic's Square ends and tour groups surge in from Almeida Ribeiro. Density and inflow rise; walking speed falls.
4. **Zone detail → Senado Square**: the +10/+15 min forecast turns CRITICAL with its confidence, and "why" reasons (density change, inflow > outflow, adjacent zone filling, speed falling).
5. **Interventions**: the recommendation ("redirect part of the southbound flow via the Rua da Tercena corridor", accessibility check, zh/en/pt notices). Click **VIEW EVIDENCE**, then **APPROVE**. The decision is written to the audit log, the assumed inflow reduction is applied to the simulation and the forecast is recalculated. **TEST IN SKETCHFUTURE** opens the same recommendation as a street-level plan (next section).
6. **Reliability**: sensor health; predictions from unreliable zones show *LOW CONFIDENCE — HUMAN REVIEW REQUIRED*. **Evaluation**: real accuracy / F1 / confusion matrices from the last training run.
7. Optional: the status bar has *inject surge (Senado)* to trigger a sudden surge; use the iOS app on a phone pointed at a group of people to see a real node appear on the map.

A complete recorded run of this story, with the iOS app joining from the iPhone Simulator as a live sensor node and a no-action comparison run, is in [experiments/results/simulation_run](experiments/results/simulation_run/README.md). Approving the redirect lowered Senado's simulated density to 0.73–0.75 by 14:40 in two recorded pairs of runs, against 0.82–0.87 with no action; Senado stayed above CRITICAL in both. The crowd builds in about 3 minutes, so the first CRITICAL forecast arrived within about a minute of the true crossing rather than well ahead of it.

## SketchFuture route check (integration)

[sketchfuture/](sketchfuture/README.md) is a separate, offline route + queue model on Macau's OSM pedestrian streets (575 nodes, 692 segments) with walker, wheelchair-user and stroller profiles. Every redirect recommendation carries a **TEST IN SKETCHFUTURE** button that opens SketchFuture with a plan closing the zone-graph corridor the recommendation diverts people away from (for the demo: the Largo de S. Domingos → Senado Square entrance, three footway segments). SketchFuture then compares the same cohort with and without the closure: per-profile travel time, distance, queues and reachability.

The two graphs are linked by `shared/sketchfuture_crosswalk.json`: for each of the seven zone-graph corridors, the SketchFuture street segments whose closure forces a detour. `sketchfuture/scripts/crosswalk.mjs` generates it with SketchFuture's own router (a hand-picked boundary junction per corridor; segments closed one at a time until the walking route is at least 30% longer), `GET /config` serves it, and SketchFuture's tests check it against the map (closures are valid plans, the recorded direct/detour distances are the model's, at least one cohort route changes, no walker is stranded). The two corridors to Avenida de Almeida Ribeiro are outside SketchFuture's map; their cards say so instead of offering a test.

What it shows and what it does not: a full closure is the extreme case of CrowdPulse's assumed 30% diversion, and SketchFuture's cohort is its own (Senado / St. Dominic's / Rua da Tercena ↔ Ruins / Museum) under its own assumptions (`sketchfuture/MODEL.md`). It is a consistency check on real street geometry — e.g. the detour around Senado's north entrance is 216 m instead of 125 m in that map — not evidence of real pedestrian behaviour. Reduced-mobility visitors keep the main route with staff assistance, as the recommendation states.

## Results (synthetic held-out test days, from `ml/models/metrics.json`)

| horizon | model | accuracy | F1 (macro) | persistence-baseline F1 | accuracy vs simulation ground truth | density MAE |
|---|---|---|---|---|---|---|
| +5 min | random forest | 0.969 | 0.887 | 0.849 | 0.974 | 0.017 |
| +10 min | random forest | 0.966 | 0.876 | 0.827 | 0.972 | 0.019 |
| +15 min | random forest | 0.964 | 0.865 | 0.795 | 0.972 | 0.020 |

Low-confidence gating: predictions flagged for human review (≈2% of all) are right only ~55% of the time versus ~97% for the rest. On the rain + closure + surge stress day, macro-F1 drops to ≈0.61–0.64 and the OOD detector flags ≈14% of inputs (vs ≈1–2% on normal days). Full tables and figures: `experiments/results/latest/`, and the dashboard's Evaluation page. These are **synthetic** results; see the model card for what they do and do not show.

## Real-video result (not synthetic)

`experiments/video_eval.py` runs the app's own detection code (`PersonDetector` + `VisionProcessor`, compiled into a Mac harness) over a CC0 street-crossing clip (Yonge & Dundas, Toronto; 640×360, 10 fps) and compares it with 11 hand-counted frames. The app now uses a **YOLO11n CoreML person detector** (5 MB, on-device) instead of Apple's built-in human detector:

| detector | near field (within ~20 m): error per frame | near field: share of people found | dense frames: share found | whole street scene: share found |
|---|---|---|---|---|
| Apple built-in (previous) | 3.0 people | 55% | 61% | 9% |
| YOLO11n CoreML (new default) | 1.5 people | 97% | 82% | 27% |

YOLO11s (18 MB) was no better than YOLO11n, so the smaller model ships. Inference is about 6 ms per frame on a Mac; phone speed is not yet measured. Remaining limits: dense crowds still hide people from a single low camera (82% found at the scramble peak), and people ~50 m away are mostly missed (27%), so phones must be placed close to and above the crowd they measure. With one clip and 11 labelled frames these numbers are indicative, not a benchmark. Figures: `experiments/results/video/`, table: `experiments/results/video/summary.md`.

**Correction:** the first version of this evaluation reported 34% / 8% for Apple's detector. Those hand counts were attached to the wrong video times (ffmpeg's sampler takes the last frame of each 5 s interval, 2.4 s after the label), and the near-field definition was not one the detectors could be scored against. The script now verifies frame alignment pixel-for-pixel and uses a stated geometric near-field rule; the table above is the corrected result.

**Licence:** YOLO11 weights are AGPL-3.0 (Ultralytics). That is fine for this open-source prototype; a closed-source or App Store deployment needs an Ultralytics licence or a permissively licensed detector. Apple's built-in detector remains selectable in the app's Setup page and is the automatic fallback.

## Limitations (honest summary)

- All accuracy numbers come from a simulator that we wrote; real-world accuracy is unknown until the controlled experiments in `docs/experiment-protocol.md` are run.
- The density index is relative (0–1), not persons per m². Thresholds are experimental.
- Camera person detection undercounts in dense crowds (occlusion). This is measured on real video (YOLO11n finds about 82% of people in the densest frames) and modelled in the simulator (observed density saturates near 0.8 while simulated truth reaches 1.0).
- The WARNING class (transitional) is the hardest: F1 ≈ 0.73–0.77 vs ≈0.90 for CRITICAL.
- Intervention effects are assumptions (30% inflow diversion), not validated causal estimates.
- One phone sees one part of a zone; the zone estimate depends on calibration of each phone's visible capacity.

Documented failure cases: `docs/model-card.md` (occlusion, rain/umbrellas, obstruction not flagged, device movement, unusual days, single-sensor dropout).
