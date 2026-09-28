# Controlled experiment protocol (school environment)

Goal: measure how well phone sensors estimate crowd state against manually recorded ground truth, and how well the pipeline classifies congestion, under repeatable conditions.

## Setup

- 3 iPhones (no LiDAR needed) with the CrowdPulseSensor app, each on a tripod/shelf 1.5–2.5 m high, tilted ~20° down, facing the test area. Assign each a zone via the app's *Sensor Setup* page (the backend also assigns by GPS; indoors, GPS may be poor — use the zone hint and expect the "weak GPS" reliability penalty, which is itself part of the evaluation).
- Backend running on a laptop on the same Wi-Fi with `CROWDPULSE_LIVE_SIM=false`; phones point at `http://<laptop-ip>:8000`.
- 20–30 volunteers, one "counter" per phone with a clicker, one timekeeper.
- Calibrate each phone's *visible capacity* (the number of people that would fill its view) in the Setup page; this defines the relative density index for that node.

## Conditions (5 minutes each, 2 minutes rest)

| code | condition | instructions |
|---|---|---|
| A | low-density normal walking | 6–8 volunteers wander across the area |
| B | higher-density flow | all volunteers walk in the same direction, loop around |
| C | narrow doorway bottleneck | everyone passes through a 1 m gap |
| D | opposing flows | two groups cross in opposite directions |
| E | crossing flows | two groups cross at 90° |
| F | sudden surge | everyone waits outside, then enters together on a signal |

Optional stress conditions: umbrella (open umbrellas), obstruction (someone stands in front of a phone), knock (tap the phone), low light.

## Ground truth recording

Every 30 s the counter records the number of people visible to their phone and the timekeeper records the condition. Submit rows with `POST /experiments/ground-truth` (or the CSV template below and a small script), fields: `zone_id, timestamp, actual_count, actual_class, condition, notes`. `actual_class` is derived from the agreed density thresholds for the room (state them in the notes).

## Analysis

- `GET /experiments/results` (and `.csv`) joins each ground-truth row to the zone state of the same minute and to the prediction made 5 minutes earlier: person-count MAE, class agreement, and 5-minute-ahead predicted vs actual class.
- Export `GET /export/observations.csv` and `GET /export/zone_states.csv` for flow-direction error (compare the app's flow direction with the instructed walking direction in B/D/E) and reliability-vs-error plots.
- Report per condition: count MAE, density MAE (relative), class agreement, prediction accuracy, and the fraction of observations flagged low-reliability.

## Expected failure modes to look for

Under-counting in C/F (occlusion), scattered flow direction in D/E (opposing flows cancel in the mean vector — flow coherence should drop), false "empty" readings during obstruction if the obstruction detector misses it.

## Ethics

Volunteers consent to being counted; no images are stored; the preview is only on the phone screen. Post a sign "crowd counting experiment in progress".
