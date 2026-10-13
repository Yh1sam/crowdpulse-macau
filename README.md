# CrowdPulse Macau

**Privacy-preserving smartphone crowd intelligence for Macau's tourist district.**
Hackathon prototype for the Imperial College London Global Hackathon 2026 — High School Track, Challenge 2(c): Responsible AI.

> Research question: *How accurately can a distributed network of commodity smartphones predict short-term pedestrian congestion while minimising identifiable data collection?*

## Problem

In Golden Week 2026, police briefly imposed crowd control at the Ruins of St. Paul's on three afternoons ([Public Security Police Force, 8 Oct 2026](https://www.gcs.gov.mo/news/detail/zh-hant/N26JHjeU3y)), and 4 October set a National Day holiday record of 210,000 visitor arrivals to Macau, a preliminary figure ([MGTO, 8 Oct 2026](https://www.gov.mo/en/news/410737/)). The police already run a "crowd forecast and early-warning system" from the Ruins to Senado Square, officially described as real-time monitoring with alerts, and plan to expand it. CrowdPulse explores what movable phones that send only numbers could add, with 5-15 minute forecasts that carry a confidence score and need a person's approval. Every figure here is sourced in [docs/research/brief-evidence.md](docs/research/brief-evidence.md).

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
dashboard/               Next.js + MapLibre operator console (9 pages)
sketchfuture/            SketchFuture: offline route + queue model on Macau's OSM streets, opened from intervention cards
shared/                  ONE config file (thresholds, confidence, reliability), zone graph, observation schema, SketchFuture crosswalk
docs/                    architecture, privacy, model card, experiment protocol, deployment, notes
experiments/results/latest   evaluation figures + metrics table produced by the last evaluation run
```

See [docs/architecture.md](docs/architecture.md) for the system diagram and data flow.

## Setup

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/) (or pip), Node 20+, pnpm 10+ (tested with 11.21) and npm, Xcode 16+ for the iOS app.

The trained models (`ml/models/`) and evaluation figures (`experiments/results/latest/`) are committed, so the backend and dashboard run straight after installing; steps 1–2 are only needed to regenerate them, and they overwrite the committed files.

```bash
# Python (backend + ML): creates .venv with the versions pinned in uv.lock
uv sync --python 3.12 --extra dev
# or, without uv: python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"

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

## Demo (about 3 minutes on stage)

**Timing.** The scenario is a Golden-Week afternoon from 13:45 to 15:45. The backend fast-forwards its first 8 simulated minutes so the forecasts have history, so the SIM CLOCK shows about 13:53 when the dashboard opens. At the default 6× speed one real minute is six simulated minutes:

| real time after (re)start | SIM CLOCK | what happens |
|---|---|---|
| 0 min | ≈13:53 | Senado Square WARNING; *Deploy staff* cards pending |
| ≈2 min | ≈14:04 | a performance at St. Dominic's ends; tour groups surge in |
| ≈3 min | ≈14:09–14:11 | Senado forecasts turn CRITICAL; the Senado redirect card appears |
| ≈7 min | ≈14:35–14:40 | after an approval, Senado's density eases |
| ≈19 min | 15:45 | the run ends by itself; every zone shows UNKNOWN until the next start |

So start or restart the run (*start demo sim* in the status bar) about 3 minutes before you open Interventions. For rehearsals, `CROWDPULSE_SIM_ACCELERATION=10` shortens every step ([docs/testing.md §4](docs/testing.md)). The Live map loads OpenStreetMap tiles over the internet; open it once before the pitch.

1. Start the backend, the dashboard and, for step 5, SketchFuture (commands in [Setup](#setup)).
2. **Overview / Live map**: Senado Square is WARNING; flows are southbound from the Ruins.
3. ~14:04 a performance at St. Dominic's Square ends and tour groups surge in from Almeida Ribeiro. Density and inflow rise; walking speed falls.
4. **Zone detail → Senado Square**: the +5/+10/+15 min forecasts turn CRITICAL, the first ones flagged *LOW CONFIDENCE — HUMAN REVIEW REQUIRED*, then confident ones, each with "why" reasons (density change, inflow > outflow, adjacent zone filling, speed falling). **Say it plainly:** this scripted crowd builds in about 3 minutes, so the confident CRITICAL forecast arrives *with* the crowd, not before it. The 5–15 minute forecasting skill is shown offline on held-out days: on the **Evaluation** page, +15 min CRITICAL recall is 0.908 against 0.792 for persistence.
5. **Interventions**: two or three cards are pending, because neighbouring zones raise their own (St. Dominic's, Rua de S. Paulo). Open the *Redirect part of … flow around Senado Square* card; the Overview's "Highest risk" line names its number. It shows the route, the accessibility check and the zh/en/pt public notice. Click **VIEW EVIDENCE**, then **APPROVE**. The decision is written to the audit log, the assumed inflow reduction is applied to the simulation and the forecast is recalculated. **TEST IN SKETCHFUTURE** opens the same recommendation as a street-level plan (next section). Two things to expect: a card that has just been superseded by a stronger one, or has expired, answers APPROVE with "409: intervention N already superseded" (or "expired"), so act on the newest card; and a neighbouring zone's card may route people towards a zone that is itself busy, because routes are scored by length, stairs and capacity, not by the destination's state. The operator, not the system, makes that call.
6. **Reliability**: sensor health; predictions from unreliable zones show *LOW CONFIDENCE — HUMAN REVIEW REQUIRED*. **Evaluation**: real accuracy / F1 / confusion matrices from the last training run.
7. Optional: the status bar has *inject surge (Senado)* to trigger a sudden surge; use the iOS app on a phone pointed at a group of people to see a real node appear on the map.

A complete recorded run of this story, with the iOS app joining from the iPhone Simulator as a live sensor node and a no-action comparison run, is in [experiments/results/simulation_run](experiments/results/simulation_run/README.md). Approving the redirect lowered Senado's simulated density to 0.73–0.75 by 14:40 in two recorded pairs of runs, against 0.82–0.87 with no action; Senado stayed above CRITICAL in both, and its time above CRITICAL was not shortened (32 vs 31 minutes). The simulated effect is an assumption (see Limitations). The crowd builds in about 3 minutes, so the first CRITICAL forecast arrived within about a minute of the true crossing rather than well ahead of it.

## SketchFuture route check (integration)

[sketchfuture/](sketchfuture/README.md) is a separate, offline route + queue model on Macau's OSM pedestrian streets (575 nodes, 692 segments) with walker, wheelchair-user and stroller profiles. Every redirect recommendation carries a **TEST IN SKETCHFUTURE** button that opens SketchFuture with a plan closing the zone-graph corridor the recommendation diverts people away from (for the demo: the Largo de S. Domingos → Senado Square entrance, three footway segments). SketchFuture then compares the same cohort with and without the closure: per-profile travel time, distance, queues and reachability.

The two graphs are linked by `shared/sketchfuture_crosswalk.json`: for each of the seven zone-graph corridors, the SketchFuture street segments whose closure forces a detour. `sketchfuture/scripts/crosswalk.mjs` generates it with SketchFuture's own router (a hand-picked boundary junction per corridor; segments closed one at a time until the walking route is at least 30% longer), `GET /config` serves it, and SketchFuture's tests check it against the map (closures are valid plans, the recorded direct/detour distances are the model's, at least one cohort route changes, no walker is stranded). The two corridors to Avenida de Almeida Ribeiro are outside SketchFuture's map; their cards say so instead of offering a test.

What it shows and what it does not: a full closure is the extreme case of CrowdPulse's assumed partial redirect, and SketchFuture's cohort is its own (Senado / St. Dominic's / Rua da Tercena ↔ Ruins / Museum) under its own assumptions (`sketchfuture/MODEL.md`). It is a consistency check on real street geometry — e.g. the detour around Senado's north entrance is 216 m instead of 125 m in that map — not evidence of real pedestrian behaviour. Reduced-mobility visitors keep the main route with staff assistance, as the recommendation states.

## Results (synthetic held-out test days, from `ml/models/metrics.json`)

| horizon | model | accuracy | F1 (macro) | persistence-baseline F1 | accuracy vs simulation ground truth | density MAE |
|---|---|---|---|---|---|---|
| +5 min | random forest | 0.969 | 0.887 | 0.849 | 0.974 | 0.017 |
| +10 min | random forest | 0.966 | 0.876 | 0.827 | 0.972 | 0.019 |
| +15 min | random forest | 0.964 | 0.865 | 0.795 | 0.972 | 0.020 |

The forecast beats the persistence baseline ("the class stays as it is now") by 3.7 / 4.9 / 7.0 macro-F1 points at +5 / +10 / +15 min; the gain grows with the horizon. At +15 min the model recognises 91% of CRITICAL bins (recall 0.908) against 79% for persistence (0.792). Low-confidence gating: the predictions flagged for human review (1.4–1.7% of all) are right only 56–57% of the time, versus 97–98% for the rest. On the rain + closure + surge stress day, macro-F1 falls to 0.86 / 0.83 / 0.81 (WARNING F1 to 0.61–0.70) and the OOD detector flags 11–12% of inputs, against 0.6–0.7% on the normal test days. Full tables and figures: `experiments/results/latest/metrics_table.md` (generated from `ml/models/metrics.json`, the single source for every number here), and the dashboard's Evaluation page. These are **synthetic** results; see the model card for what they do and do not show.

## Real-video result (not synthetic)

`experiments/video_eval.py` runs the app's own detection code (`PersonDetector` + `VisionProcessor`, compiled into a Mac harness) over a CC0 street-crossing clip (Yonge & Dundas, Toronto; 640×360, 10 fps) and compares it with 11 hand-counted frames. The app now uses a **YOLO11n CoreML person detector** (5 MB, on-device) instead of Apple's built-in human detector:

| detector | near field (within ~20 m): error per frame | near field: count as a share of the hand count | dense frames: count ÷ hand count | whole street scene: count ÷ hand count |
|---|---|---|---|---|
| Apple built-in (previous) | 3.0 people | 55% | 61% | 9% |
| YOLO11n CoreML (new default) | 1.5 people | 97% | 82% | 27% |

YOLO11s (18 MB) was no better than YOLO11n, so the smaller model ships. Inference is about 6 ms per frame on a Mac; phone speed is not yet measured. Remaining limits: dense crowds still hide people from a single low camera (the count is 82% of the hand count at the scramble peak), and people ~50 m away are mostly missed (27%). These are count ratios (detector total ÷ hand total), not the share of individual people detected; the Mall benchmark below measures that directly, so phones must be placed close to and above the crowd they measure. With one clip and 11 labelled frames these numbers are indicative, not a benchmark. Figures: `experiments/results/video/`, table: `experiments/results/video/summary.md`.

**A larger, harder test (Mall dataset).** Eleven frames of one street clip is a small sample, so the same detector code was also run on all 2,000 frames of the Mall dataset (a public research benchmark: a shopping-mall webcam looking down a busy walkway, 13–53 annotated people per frame, 62,315 in total; research use only, so the data is not redistributed here). Results from `experiments/results/mall/summary.md`:

| detector | share of people counted | count error per frame | people with a box (recall): near / middle / far third of image | boxes that are a person (precision) |
|---|---|---|---|---|
| YOLO11n CoreML (app default) | 59% | 12.9 people (mean crowd 31) | 78% / 64% / 42% | 93% |
| Apple built-in (fallback) | 29% | 22.0 people | 52% / 38% / 18% | 99% |

From a high indoor camera, with people seated, behind a kiosk or far down the walkway, YOLO11n misses about 4 in 10 people, so the 97% near-field figure above is optimistic for crowded scenes. Its boxes are almost always real people, and its count tracks the true count (correlation 0.80), so the under-count is systematic. In a follow-up added after seeing this, a per-camera linear calibration fitted on 20 labelled frames (from the first 800) brought the error on the held-out frames 801–2000 down from 13.4 to 3.3 people per frame. That makes "label about 20 snapshots when installing a phone" a concrete deployment step; it is tested on one camera only.

**Correction:** the first version of this evaluation reported 34% / 8% for Apple's detector. Those hand counts were attached to the wrong video times (ffmpeg's sampler takes the last frame of each 5 s interval, 2.4 s after the label), and the near-field definition was not one the detectors could be scored against. The script now verifies frame alignment pixel-for-pixel and uses a stated geometric near-field rule; the table above is the corrected result.

**Licence:** YOLO11 weights are AGPL-3.0 (Ultralytics), so this repository is released under AGPL-3.0 as a whole (see [Licence](#licence)); a closed-source or App Store deployment needs an Ultralytics licence or a permissively licensed detector. Apple's built-in detector remains selectable in the app's Setup page and is the automatic fallback.

## Limitations (honest summary)

- All accuracy numbers come from a simulator that we wrote; real-world accuracy is unknown until the controlled experiments in `docs/experiment-protocol.md` are run.
- The density index is relative (0–1), not persons per m². Thresholds are experimental.
- Camera person detection undercounts. Measured on real footage: YOLO11n's count is about 82% of the hand count in the densest frames of a street clip and 59% of the annotated count in 2,000 frames of a crowded shopping-mall walkway, where it put a box on 55% of the people (42% in the far third of the image). The simulator models a milder under-count (observed density saturates near 0.8 while simulated truth reaches 1.0). Each phone needs a per-camera calibration; with 20 labelled frames this reduced the mall error from 13.4 to 3.3 people per frame on held-out frames (one camera).
- The WARNING class (transitional) is the hardest: F1 0.74–0.79 vs 0.86–0.88 for CRITICAL (test days, observed labels).
- Intervention effects are assumptions, not validated causal estimates: in the live simulation, routes into the zone are made 30% less attractive for 20 minutes (people re-choose among the other routes, so inflow falls by less than 30%), and the forecast what-if scales the zone's inflow by 0.7.
- One phone sees one part of a zone; the zone estimate depends on calibration of each phone's visible capacity.

Documented failure cases: `docs/model-card.md` (occlusion, rain/umbrellas, obstruction not flagged, device movement, unusual days, single-sensor dropout).

## Licence

Copyright (C) 2026 the CrowdPulse Macau team.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License, version 3, as published by the Free Software Foundation ([LICENSE](LICENSE)). It is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. Under AGPL-3.0, anyone who runs a modified version as a network service (the backend or dashboard) must offer its users the corresponding source.

Third-party material keeps its own licence: the YOLO11n weights (AGPL-3.0, Ultralytics), the CC0 Yonge & Dundas video and the OpenStreetMap data used by SketchFuture (ODbL 1.0). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
