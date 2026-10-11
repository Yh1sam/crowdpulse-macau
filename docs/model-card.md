# Model card — CrowdPulse congestion forecaster (crowdpulse-clf-0.1)

## Model type

Per forecast horizon (+5, +10, +15 min) one classifier chosen among logistic regression, random forest and histogram gradient boosting by validation macro-F1 (random forest won all three in the last run), plus a gradient-boosting regressor for the future density index. Isotonic calibration is applied only if it lowers ECE by more than 0.005 on a held-out half of the validation set: in the last run it was applied at +10 min (held-out ECE 0.012 → 0.007) and +15 min (0.017 → 0.009), and not at +5 min (0.009 → 0.005, below the required improvement). An isolation forest + feature-range checks detect out-of-distribution inputs.

## Intended use

Decision support for crowd-management operators in the Macau historic district: short-term congestion risk (SAFE / WARNING / CRITICAL) per zone, with confidence and reasons, feeding *recommendations* that a human approves or rejects. Not for automatic control of infrastructure, enforcement, or any per-person decision.

## Prohibited use

Identifying, tracking or profiling individuals; surveillance of private spaces; automatic road closures or public commands without human approval; use of the confidence score as a safety guarantee.

## Data

- **Training data is synthetic**: `ml/synthetic/simulator.py`, a mesoscopic crowd-flow model over a 7-zone graph of the district, with time-of-day and day-type arrival profiles, scripted surges, event endings, rain and route closures, and an explicit sensor-error model (Poisson-like count noise, occlusion under-count ∝ density², dropout, obstruction with 25% *silent* obstruction, device disturbance, weak GPS, low light).
- 14 simulated days (Sep 21 – Oct 4 2026, 08:00–22:00 local; 9 sensors; 20 s reporting), split **by day**: 9 train, 2 validation, 3 test (a weekend, a weekday and a Golden-Week day). A separate stress day (heavy rain + closure + surge) is used only for evaluation.
- Labels are the *observed* zone density class h minutes ahead (what a deployed system can learn from); ground-truth labels from the simulator are used additionally for evaluation.

## Features (27)

density and 3 lags, 1- and 3-min density change; inflow/outflow/net-flow proxies (from anonymous flow vectors projected on the zone graph), inflow lag; walking speed and 3-min change; flow coherence; neighbour density mean/max/change and neighbour inflow; hour (sin/cos), day type, operator-provided event and rain indicators; sensor reliability, sensor count, disagreement, obstruction fraction, staleness.

## Metrics (last run, synthetic held-out test days; `ml/models/metrics.json`)

| horizon | accuracy | precision (macro) | recall (macro) | F1 (macro) | ROC-AUC (ovr) | ECE | persistence F1 | acc. vs ground truth | density MAE | stress-day F1 |
|---|---|---|---|---|---|---|---|---|---|---|
| +5 | 0.969 | 0.877 | 0.897 | 0.887 | 0.993 | 0.001 | 0.849 | 0.974 | 0.017 | 0.857 |
| +10 | 0.966 | 0.871 | 0.882 | 0.876 | 0.991 | 0.007 | 0.827 | 0.972 | 0.019 | 0.832 |
| +15 | 0.964 | 0.863 | 0.869 | 0.865 | 0.991 | 0.007 | 0.795 | 0.972 | 0.020 | 0.814 |

The table is the one `ml/evaluation/evaluate.py` writes to `experiments/results/latest/metrics_table.md` from `ml/models/metrics.json` (training run 2026-09-28T11:12Z); an earlier run that day is kept in `experiments/results/20260928T105934Z/` and is superseded.

Per class (+15 min, test days): against the *observed* labels the model is trained on, SAFE F1 0.99, WARNING F1 0.74, CRITICAL F1 0.86 (recall 0.91; persistence baseline 0.79). Against the simulator's *ground truth*, CRITICAL F1 is 0.91 (precision 0.99, recall 0.84) and WARNING F1 0.77. Confusion matrices and figures: `experiments/results/latest/`.

Confidence gating (threshold 0.60 on effective confidence = model probability × reliability factor × OOD factor): 1.4–1.7% of predictions are flagged for human review; their accuracy is 0.56–0.57 versus 0.97–0.98 for the rest.

## Known limitations and failure cases

| case | cause | impact | detection | mitigation |
|---|---|---|---|---|
| Dense-crowd under-count | occlusion: detector misses people behind others | observed density saturates ≈0.8 when truth is 1.0; CRITICAL recognised late | ground-truth counts in controlled experiments; timeline figure | per-sensor calibration of visible capacity; thresholds defined on the observed index; multiple viewpoints per zone |
| Rain / umbrellas | umbrellas hide bodies; lens droplets | counts noisier, vision confidence drops; stress-day macro-F1 0.814–0.857 vs 0.865–0.887 on normal test days, WARNING F1 down to 0.61–0.70 | rain indicator, vision confidence, OOD detector (flags 11–12% of stress-day inputs vs 0.6–0.7% on normal days) | confidence reduced; operator warning "conditions differ from training data" |
| Camera obstruction not flagged | someone stands in front of the phone; the app fails to notice | near-zero counts look like an empty zone | disagreement between sensors in the same zone; sudden drop vs neighbours | reliability weight from vision confidence; alerts for low reliability; human review |
| Device moved / knocked | motion stability < 0.75 | garbage counts and flow | accelerometer/gyro stability score | observation weight → 0; sensor issue alert |
| Single-sensor dropout | phone battery / network | zone becomes stale; no prediction | staleness, "INSUFFICIENT DATA — HUMAN REVIEW" | buffer + retry on phone; ≥2 phones per critical zone |
| Unusual day (parade, closure) | patterns absent from training | accuracy falls | OOD flag, low confidence | human review; retrain with new data |
| Synthetic-to-real gap | training data is simulated | real accuracy unknown | controlled experiments (protocol in docs) | collect real data, retrain, report honestly |
| Person detector misses people (measured) | small far figures (5–15 px) and occlusion in dense groups | on a CC0 street-crossing clip, the shipped YOLO11n detector finds ≈97% of people within ~20 m overall but ≈82% in the densest frames, and ≈27% of a wide scene including a crowd ~50 m away (Apple's built-in detector: ≈55% / 61% / 9%) | `experiments/video_eval.py` against hand-counted frames | YOLO11n replaced Apple's detector; place phones 2–3 m high close to the crowd they measure; calibrate visible capacity per node; a density-map model for very dense scenes is future work |
| Detector licence | YOLO11 weights are AGPL-3.0 | closed-source or App Store distribution not covered | licence review | Ultralytics licence or a permissively licensed detector; Apple's detector stays selectable as a fallback |

## Fairness considerations

- *Elderly / reduced-mobility pedestrians*: interventions are scored with an accessibility penalty (stairs, steep sections, detour length); the chosen route in the demo avoids the St. Paul's steps, and every recommendation keeps the main route open with staff assistance.
- *Non-Chinese-speaking visitors*: public notices are generated in Chinese, English and Portuguese, with zone and street names in each language (`name_zh` / `name_pt` in `shared/zones.json`).
- The model itself does not use any attribute of individuals (it cannot: it never sees them).

## Ethical considerations

The system reduces surveillance compared with CCTV analytics, but it still counts people in public space; deployment should be signposted and limited to safety needs. Confidence values are model estimates from synthetic data and must not be presented to the public as guarantees.
