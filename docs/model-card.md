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

### Accuracy against "no change" and "always SAFE", and why F1 leads

| horizon | model accuracy | persistence ("no change") accuracy | always-SAFE accuracy | model macro-F1 | persistence macro-F1 | always-SAFE macro-F1 | macro-F1 gain over persistence (95% interval) |
|---|---|---|---|---|---|---|---|
| +5 | 0.969 | 0.960 | 0.847 | 0.887 | 0.849 | 0.306 | +0.037 (+0.024 to +0.050) |
| +10 | 0.966 | 0.952 | 0.846 | 0.876 | 0.827 | 0.306 | +0.049 (+0.031 to +0.064) |
| +15 | 0.964 | 0.943 | 0.846 | 0.865 | 0.795 | 0.305 | +0.070 (+0.049 to +0.089) |

Model and persistence accuracy and macro-F1 come from `ml/models/metrics.json`; always-SAFE and the intervals from `experiments/results/uncertainty/summary.md` (block bootstrap over one zone on one test day, 21 blocks, 10,000 resamples; the gain interval is paired, so model and persistence are scored on the same resampled minutes). Most zone-minutes are calm: at +15 min, 14,505 of the 17,152 test targets are SAFE, so a forecast that never warns anyone is already 84.6% accurate. Accuracy therefore hides most of the difference between a useful forecast and a useless one. Macro-F1 weighs SAFE, WARNING and CRITICAL equally, so always-SAFE scores only 0.305 on it, and it is the headline metric; accuracy is reported next to it (proposal: "F1 0.865 vs 0.795; accuracy 96.4% vs 94.3%"). The intervals describe resampling inside three simulated days only; they say nothing about how the simulator differs from a real street.

Per class (+15 min, test days): against the *observed* labels the model is trained on, SAFE F1 0.99, WARNING F1 0.74, CRITICAL F1 0.86 (recall 0.91; persistence baseline 0.79). Against the simulator's *ground truth*, CRITICAL F1 is 0.91 (precision 0.99, recall 0.84) and WARNING F1 0.77. Confusion matrices and figures: `experiments/results/latest/`.

Confidence gating, offline (`confidence_gating` in `ml/models/metrics.json`): a test forecast is flagged as uncertain when the model's own confidence, its largest class probability, is below 0.60. 1.4–1.7% of test forecasts are flagged; their accuracy is 0.56–0.57 versus 0.97–0.98 for the rest. The live dashboard's LOW CONFIDENCE — HUMAN REVIEW REQUIRED flag uses effective confidence instead (model probability × sensor-reliability factor × OOD factor, flagged below 0.60; `backend/app/services/prediction.py`), so it flags more: at least 2.3% of +15 min test forecasts (403 of 17,152; `experiments/results/uncertainty/summary.md`, section 4).

## Known limitations and failure cases

| case | cause | impact | detection | mitigation |
|---|---|---|---|---|
| **Fast surge: no early warning (our named failure case)** | in the recorded end-to-end simulation (`golden_week_demo` scenario) an event ending plus tour-group surges fill Senado Square in about 3 minutes, faster than the 5–15 min horizons can add value | the first confident (≥ 60%) CRITICAL forecast came after the true density crossed CRITICAL: 14:09:08 vs 14:08:09 in run A, 14:13:14 vs 14:09:20 in run B. The first CRITICAL forecast at any confidence came within about a minute of the crossing (21 s after it in run A; 74 s before it in run B, at 48% confidence and flagged for review). The 5–15 min skill in the metrics above is measured offline on simulated days and is not a measured warning time | recorded runs compared with the simulator's true density (`experiments/results/simulation_run/README.md`, times accurate to about ±30 s) | say it plainly in the demo and the pitch; uncertain forecasts stay flagged for human review; operator-entered event context (an event ending) is a model feature; test the method on real counts (Melbourne, pre-registered) before any claim of lead time |
| Dense-crowd under-count | occlusion: detector misses people behind others | observed density saturates ≈0.8 when truth is 1.0; CRITICAL recognised late | ground-truth counts in controlled experiments; timeline figure | per-sensor calibration of visible capacity; thresholds defined on the observed index; multiple viewpoints per zone |
| Rain / umbrellas | umbrellas hide bodies; lens droplets | counts noisier, vision confidence drops; stress-day macro-F1 0.814–0.857 vs 0.865–0.887 on normal test days, WARNING F1 down to 0.61–0.70 | rain indicator, vision confidence, OOD detector (flags 11–12% of stress-day inputs vs 0.6–0.7% on normal days) | confidence reduced; operator warning "conditions differ from training data" |
| Camera obstruction not flagged | someone stands in front of the phone; the app fails to notice | near-zero counts look like an empty zone | disagreement between sensors in the same zone; sudden drop vs neighbours | reliability weight from vision confidence; alerts for low reliability; human review |
| Device moved / knocked | motion stability < 0.75 | garbage counts and flow | accelerometer/gyro stability score | observation weight → 0; sensor issue alert |
| Single-sensor dropout | phone battery / network | zone becomes stale; no prediction | staleness, "INSUFFICIENT DATA — HUMAN REVIEW" | buffer + retry on phone; ≥2 phones per critical zone |
| Unusual day (parade, closure) | patterns absent from training | accuracy falls | OOD flag, low confidence | human review; retrain with new data |
| Synthetic-to-real gap | training data is simulated | real accuracy unknown | controlled experiments (protocol in `docs/experiment-protocol.md`); the same method on real Melbourne pedestrian counts, pre-registered in `experiments/datasets/melbourne/README.md` before its test days (18–22 Oct 2026, Melbourne time), result pending | collect real data, retrain, report honestly whatever the result |
| Person detector misses people (measured) | small far figures (5–15 px) and occlusion in dense groups | on a CC0 street-crossing clip, the shipped YOLO11n detector's count is ≈97% of the hand count within ~20 m overall but ≈82% in the densest frames, and ≈27% of a wide scene including a crowd ~50 m away (Apple's built-in detector: ≈55% / 61% / 9%); these are count ratios over 11 frames, not per-person recall | `experiments/video_eval.py` against hand-counted frames | YOLO11n replaced Apple's detector; place phones 2–3 m high close to the crowd they measure; calibrate visible capacity per node; a density-map model for very dense scenes is future work |
| Person detector under-counts a real crowd (measured on 2,000 frames) | high viewpoint, occlusion by people and furniture, seated people, small far figures | on the Mall dataset (shopping-mall webcam, 13–53 people per frame) YOLO11n counts 59% of annotated people (recall 78% near, 42% far; 93% of boxes are people), count error 12.9 per frame; the simulator's under-count model is milder than this | `experiments/mall_eval.py` against per-frame head annotations | per-camera linear calibration: fitted on 20 labelled frames it cut the held-out error to 3.3 people per frame (post-hoc analysis, one camera). Because labels and thresholds are defined on the observed index, a roughly constant under-count mainly rescales it; not yet tested end to end through the forecaster |
| Detector licence | YOLO11 weights are AGPL-3.0 | closed-source or App Store distribution not covered | licence review | Ultralytics licence or a permissively licensed detector; Apple's detector stays selectable as a fallback |

## Who may be more at risk (fairness considerations)

The evidence is hedged and the hedge stays: dense crowds can kill anyone, and older, smaller or less mobile people *may* be more vulnerable (`docs/research/brief-evidence.md`, section 5, "At-risk groups": Motomura 2019 says children and older adults "may" fail sooner, an inference with no older adults tested; a 2026 review says children, older persons and people with disabilities "face heightened risks", without data; no evidence specific to wheelchair users was found, section 8). Two groups the design plans for:

- *Older or less mobile visitors* (including wheelchair users): route ranking uses map flags for stairs, steep sections and distance, which do not establish real accessibility. **Unverified diversions cannot be approved through the UI or API.** Operators may request an on-site check or reject the suggestion. A request is logged but does not verify the route or unlock approval; the prototype has no field-evidence acceptance workflow. CrowdPulse's scenario-simulation feature compares full-closure stress tests on its street map. In one paired cohort, 24 of 40 simulated wheelchair journeys had no mapped step-free route both before and after closure; this was not 24 newly excluded journeys. A street survey is needed to distinguish missing map detail from physical barriers (`sketchfuture/VERIFICATION.md`).
- *Visitors who cannot read Chinese*: public notices are generated in Chinese, English and Portuguese, with zone and street names in each language (`name_zh` / `name_pt` in `shared/zones.json`). This group is the team's design reasoning, not a cited finding.

The model itself does not use any attribute of individuals (it cannot: it never sees them). The person detector's accuracy has not been measured separately for wheelchair users, children or people carrying umbrellas.

## Responsibility when it fails

For discussion, not settled (`docs/research/brief-evidence.md`, section 6, "Responsibility"):

- **The approving operator.** No action happens without a person's approval. The dashboard's "Deciding as" field sends the name of the person deciding; the backend refuses an empty name, "operator" and "system" and writes the name to the audit log as the actor of approvals, rejections, field-check requests and alert acknowledgements (`backend/app/schemas.py`, `backend/app/services/engine.py`, `backend/app/api/alerts.py`; tests `test_decisions_must_name_the_person_deciding` and `test_named_approval_is_recorded_with_the_name`). The name is self-declared: the prototype has no login.
- **The department running it.** The intended user is the Public Security Police Force, which holds the legal duty to control pedestrian movement (Law 14/2018, Art. 3); there is no partner yet. Under the Personal Data Protection Act (Law 8/2005) the department that operates CrowdPulse would be the data controller; this is to be confirmed with the Personal Data Protection Bureau.
- **The public is told AI is involved.** Every public notice the system drafts ends with "Advice from an AI crowd forecast, approved by staff." (and its Chinese and Portuguese versions; `AI_NOTICE` in `backend/app/services/intervention.py`), and a sign at each phone is planned (draft in brief-evidence.md, section 6).

## Ethical considerations

The system reduces surveillance compared with CCTV analytics, but it still counts people in public space; deployment should be signposted and limited to safety needs. Confidence values are model estimates from synthetic data and must not be presented to the public as guarantees.
