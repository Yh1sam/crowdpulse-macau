# Model card — CrowdPulse congestion forecaster (crowdpulse-clf-0.1)

## Model type

Per forecast horizon (+5, +10, +15 min) one classifier chosen among logistic regression, random forest and histogram gradient boosting by validation macro-F1 (random forest won all three in the last run), plus a gradient-boosting regressor for the future density index. Isotonic calibration is applied only if it lowers ECE on a held-out half of the validation set (it did not in the last run; raw ECE was already ≤ 0.01). An isolation forest + feature-range checks detect out-of-distribution inputs.

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
| +5 | 0.969 | 0.88 | 0.90 | 0.887 | 0.99 | 0.004 | 0.849 | 0.974 | 0.017 | ≈0.62 |
| +10 | 0.966 | 0.87 | 0.89 | 0.876 | 0.99 | 0.007 | 0.827 | 0.972 | 0.019 | ≈0.64 |
| +15 | 0.964 | 0.86 | 0.88 | 0.865 | 0.99 | 0.009 | 0.795 | 0.972 | 0.020 | ≈0.61 |

Per class (+15 min): SAFE F1 0.99, WARNING F1 ≈0.73, CRITICAL F1 ≈0.90. Confusion matrices and figures: `experiments/results/latest/`. Exact values for the current artefacts are always in `metrics.json`; the table above is copied from it.

Confidence gating (threshold 0.60 on effective confidence = model probability × reliability factor × OOD factor): ≈2% of predictions are flagged for human review; their accuracy is ≈0.55 versus ≈0.97 for the rest.

## Known limitations and failure cases

| case | cause | impact | detection | mitigation |
|---|---|---|---|---|
| Dense-crowd under-count | occlusion: detector misses people behind others | observed density saturates ≈0.8 when truth is 1.0; CRITICAL recognised late | ground-truth counts in controlled experiments; timeline figure | per-sensor calibration of visible capacity; thresholds defined on the observed index; multiple viewpoints per zone |
| Rain / umbrellas | umbrellas hide bodies; lens droplets | counts noisier, vision confidence drops; stress-day F1 ≈0.6 | rain indicator, vision confidence, OOD detector (flag rate 14% vs 1.6%) | confidence reduced; operator warning "conditions differ from training data" |
| Camera obstruction not flagged | someone stands in front of the phone; the app fails to notice | near-zero counts look like an empty zone | disagreement between sensors in the same zone; sudden drop vs neighbours | reliability weight from vision confidence; alerts for low reliability; human review |
| Device moved / knocked | motion stability < 0.75 | garbage counts and flow | accelerometer/gyro stability score | observation weight → 0; sensor issue alert |
| Single-sensor dropout | phone battery / network | zone becomes stale; no prediction | staleness, "INSUFFICIENT DATA — HUMAN REVIEW" | buffer + retry on phone; ≥2 phones per critical zone |
| Unusual day (parade, closure) | patterns absent from training | accuracy falls | OOD flag, low confidence | human review; retrain with new data |
| Synthetic-to-real gap | training data is simulated | real accuracy unknown | controlled experiments (protocol in docs) | collect real data, retrain, report honestly |

## Fairness considerations

- *Elderly / reduced-mobility pedestrians*: interventions are scored with an accessibility penalty (stairs, steep sections, detour length); the chosen route in the demo avoids the St. Paul's steps, and every recommendation keeps the main route open with staff assistance.
- *Non-Chinese-speaking visitors*: public notices are generated in Chinese, English and Portuguese.
- The model itself does not use any attribute of individuals (it cannot: it never sees them).

## Ethical considerations

The system reduces surveillance compared with CCTV analytics, but it still counts people in public space; deployment should be signposted and limited to safety needs. Confidence values are model estimates from synthetic data and must not be presented to the public as guarantees.
