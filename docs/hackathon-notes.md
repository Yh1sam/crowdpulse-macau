# Hackathon notes

## Milestones

| phase | status | evidence |
|---|---|---|
| 1 end-to-end skeleton (synthetic → backend → ML → dashboard) | done | `python -m pytest` (49 tests as of 2026-10-11), dashboard pages |
| 2 ML baseline | done | `ml/models/metrics.json`: +15 min accuracy 0.964, macro-F1 0.865 vs persistence 0.795 |
| 3 dashboard | done | 9 pages, live map, approve/reject flow |
| 4 iOS sensor app | done (camera, GPS, heading, motion, upload, buffer) | `ios/CrowdPulseSensor` |
| 5 vision | done (YOLO11n CoreML person detector with Apple fallback, count, density proxy, centroid flow; live / video / simulated modes) | `PersonDetector.swift`, `VisionProcessor.swift` |
| 6 real experiments | video benchmark done (CC0 crossing clip, 11 hand-counted frames); detector swapped to YOLO11n on that evidence; school experiment not yet run | `experiments/results/video/summary.md`, `docs/experiment-protocol.md`, `/experiments/*` endpoints |
| 7 responsible AI | done | confidence gating, OOD, explanations, accessibility penalty, zh/en/pt notices, audit log |
| 8 polish | partial | evaluation figures, README, demo scenario |

## Things we deliberately did not do

Deep learning, microservices, Kubernetes, blockchain, an LLM "for the sake of AI", custom authentication, App Store submission.

## Honest caveats for the pitch

- Forecasting accuracy (F1, confusion matrices) is on synthetic data from our own simulator. Say so on the slide. Person-count accuracy is on one real CC0 video with 11 hand-counted frames: indicative, not a benchmark.
- The first video evaluation had a frame-timing bug (hand counts attached to times 2.4 s early). It was found and fixed; the pitch uses only the corrected numbers.
- The demo runs at 6× speed on a simulated clock: the Senado redirect appears about 3 real minutes after (re)starting the run, and the run ends by itself after about 19 minutes. Start it about 3 minutes before showing Interventions (timing table in the README's Demo section).
- **No early warning in the live demo.** The scripted crowd builds in about 3 minutes, faster than the forecast horizons, so the confident CRITICAL forecast arrives with the crowd, not before it. Say so. The evidence for 5–15 minute forecasting skill is offline: +15 min macro-F1 0.865 vs 0.795 for persistence and CRITICAL recall 0.908 vs 0.792 on synthetic held-out days. That is forecasting skill, not a measured warning time.
- Recommendations score routes by length, stairs and capacity, not by the destination's own state, so a neighbouring zone's card can route people towards a busy zone. That is a reason the operator decides; prepare the one-sentence answer.
- The intervention's "forecast recalculated" uses an assumed 30% inflow diversion.
- Camera under-counting in dense crowds is real and visible in our own timeline figure — present it as a known limitation with a mitigation plan.

## Scientific sub-questions and what the prototype says

1. *How accurately can phones estimate crowd state?* Simulated sensing error gives density MAE ≈0.03 and 96.8% state agreement with truth. On real video (CC0 crossing clip, 11 hand-counted frames) Apple's built-in detector found only ≈55% of people within ~20 m; swapping to an on-device YOLO11n model raised that to ≈97% (error ≈1.5 people per frame), but dense groups still hide people (≈82% found at the peak) and people ~50 m away are mostly missed. On 2,000 annotated frames of a crowded shopping-mall walkway (Mall dataset) YOLO11n counted only 59% of people (78% in the near third of the image, 42% in the far third), although 93% of its boxes were real people and its count tracked the true count (r = 0.80); a per-camera calibration from 20 labelled frames cut the held-out error from 13.4 to 3.3 people per frame (post-hoc, one camera). The sensing layer, not the forecasting layer, is the bottleneck; say so plainly, show the before/after overlay figure, and present calibration at installation as the mitigation.
2. *How early can congestion be predicted?* +15 min macro-F1 0.865 vs 0.795 for persistence (synthetic held-out days); CRITICAL recall 0.908 vs 0.792. This is forecasting skill on held-out days, not a measured warning time: in the live demo scenario the crowd builds in about 3 minutes, so the confident CRITICAL forecast arrives with the crowd, not before it.
3. *How does sensor failure affect reliability?* Reliability score drops with dropout/obstruction/movement; unreliable zones lose confidence and fall back to human review (tested).
4. *Can confidence estimation prevent unsafe AI recommendations?* Flagged predictions (1.4–1.7% of all) are right 56–57% of the time vs 97–98% for confident ones; low-confidence CRITICAL forecasts produce "increase monitoring" recommendations instead of redirects.
5. *Privacy–performance trade-off:* the pipeline uses only anonymous aggregates and still beats the persistence baseline by 4–7 macro-F1 points (3.7 / 4.9 / 7.0 at +5 / +10 / +15 min); the price is the occlusion under-count and single-view calibration.

## Presentation evidence checklist

`experiments/results/latest/`: confusion_matrix.png, model_comparison.png, prediction_timeline.png, density_timeline.png, sensor_reliability.png, calibration_and_gating.png, stress_scenario.png, metrics_table.md. `experiments/results/video/`: video_count_accuracy.png, detector_overlay.png (before/after on the same frame), summary.md. `experiments/results/mall/`: mall_count_timeline.png, mall_count_scatter.png, summary.md (2,000-frame benchmark; the annotated example frame is local only, see `experiments/datasets/mall/README.md`). Dashboard screenshots: overview, zone detail, interventions, reliability, evaluation. CSV exports from `/export/*.csv`.
