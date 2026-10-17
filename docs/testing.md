# Testing CrowdPulse

The Python, dashboard and SketchFuture test suites in section 1 were last re-run on 2026-10-17 (54, 24 and 33 passed). The iOS tests, the two production builds and the Python install in section 0 (on a fresh `git archive` export) were last run on 2026-10-11; the iOS test files have not changed since 2026-09-30. The other sections were run when they were written, between 2026-09-29 and 2026-10-09, except the "Deciding as" step in section 4 and the unnamed-decision check in section 5, both added on 2026-10-17 for the change of 2026-10-16. Expected results are what those runs produced.
Run commands from the repository root unless a step says otherwise.

## 0. Prerequisites

- macOS with Xcode 16+ (iOS tests and the phone app), Python 3.12, `uv`, `pnpm`, `ffmpeg` and Node 24.15.0 or later in the Node 24 line (the repository's `.nvmrc` selects 24.16.0, the only version tested), or 22.22.2 or later on Node 22, or Node 26 or later. That Node minimum is set by the tests: the dashboard's tests and SketchFuture's `tests/app-errors.test.ts` run under jsdom 30.1.1, whose `engines` field is `^22.22.2 || ^24.15.0 || >=26.0.0` (Node 25 is outside it). SketchFuture's dev server and build alone run from Node 22.12 or 24.0.
- Optional: `xcodegen` (`brew install xcodegen`) if you change `ios/CrowdPulseSensor/project.yml`.

Python environment (versions pinned in `uv.lock`; scikit-learn is pinned to 1.9.1 because the committed models were pickled with it):

```bash
uv sync --python 3.12 --extra dev
```

Without uv, or if PyPI returns HTTP 503 (then add `--index-url https://mirrors.aliyun.com/pypi/simple`):

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

Dashboard and SketchFuture dependencies:

```bash
cd dashboard && pnpm install
```

```bash
cd sketchfuture && npm install
```

## 1. Automated tests

| suite | command | expected |
|---|---|---|
| backend API + ML pipeline | `.venv/bin/python -m pytest` (`pyproject.toml` already adds `-q`) | 54 passed |
| dashboard components | `cd dashboard && pnpm test` | 24 passed |
| dashboard production build | `cd dashboard && node node_modules/next/dist/bin/next build` | "Compiled successfully", 10 routes |
| SketchFuture model + CrowdPulse hand-over | `cd sketchfuture && npm test` | 33 passed |
| SketchFuture production build | `cd sketchfuture && npm run build` | succeeds; Vite prints a chunk-size advisory for the bundled offline map |
| iOS logic + detector | see below | 13 tests, 0 failures |
| **total** | | **124 automated tests** (54 + 24 + 33 + 13) |

```bash
cd ios/CrowdPulseSensor && xcodebuild test -project CrowdPulseSensor.xcodeproj -scheme CrowdPulseSensor -destination 'platform=iOS Simulator,name=iPhone 17 Pro'
```

Use any installed simulator name (`xcrun simctl list devices available`). The iOS tests include YOLO11n finding at least 10 people on a real crossing frame.

## 2. Reproduce the forecasting results (synthetic data)

```bash
.venv/bin/python -m ml.synthetic.generate --days 14 --interval 20 --out ml/data
```

```bash
.venv/bin/python -m ml.synthetic.generate --scenario stress_rain_closure --out ml/data --prefix stress
```

```bash
.venv/bin/python -m ml.training.train
```

```bash
.venv/bin/python -m ml.evaluation.evaluate
```

Expected (identical on a fresh clone, the pipeline is seeded): +5 min accuracy 0.969 / macro-F1 0.887, +10 min 0.966 / 0.876, +15 min 0.964 / 0.865. Training takes about 70 s. Figures land in `experiments/results/<timestamp>/` and `experiments/results/latest/`.

## 3. Reproduce the real-video person-count result

The evaluation clip is the same file the app bundles, so no download is needed.

```bash
cp ios/CrowdPulseSensor/Resources/sample_crowd.mp4 experiments/datasets/video/yonge_dundas_640_10fps.mp4
```

```bash
xcrun coremlcompiler compile ios/CrowdPulseSensor/Resources/yolo11n.mlpackage /tmp/cp_models
```

```bash
cd ios/CrowdPulseSensor && swiftc -O -o /tmp/videoeval Tools/videoeval/main.swift Sources/Services/PersonDetector.swift Sources/Services/VisionProcessor.swift Sources/Services/FlowEstimator.swift Sources/Models/SensorObservation.swift Tools/videoeval/Shims.swift
```

Then, from the repository root, run each detector over the clip:

```bash
/tmp/videoeval experiments/datasets/video/yonge_dundas_640_10fps.mp4 --out experiments/datasets/video/counts_640_upper.csv --boxes-out experiments/datasets/video/boxes_640_upper.json
```

```bash
/tmp/videoeval experiments/datasets/video/yonge_dundas_640_10fps.mp4 --out experiments/datasets/video/counts_640_full.csv --boxes-out experiments/datasets/video/boxes_640_full.json --full-body
```

```bash
/tmp/videoeval experiments/datasets/video/yonge_dundas_640_10fps.mp4 --out experiments/datasets/video/counts_yolo11n.csv --boxes-out experiments/datasets/video/boxes_yolo11n.json --detector coreml --model /tmp/cp_models/yolo11n.mlmodelc
```

```bash
.venv/bin/python experiments/video_eval.py
```

Expected: YOLO11n near-field MAE 1.5, found 97%; Apple built-in MAE 3.0, found 55% ("found" = detector count ÷ hand count, not per-person recall). Note: when `frames/` is absent the script prints "alignment ok" without checking anything; the pixel check only runs if the frame images exist.

> **Warning: this step overwrites committed, published files.** `experiments/video_eval.py` writes into `experiments/results/video/` by default (`--out`): `detector_overlay.png`, `video_count_accuracy.png`, `summary.md` and `summary.json` (`video_eval_rows.csv` there is not rewritten). `detector_overlay.png` shows real passers-by from the CC0 clip. The script mosaics their faces before plotting (`mask_overlay_frame` from `experiments/mask_faces.py`, head boxes in `experiments/mask_faces_boxes.json`) and stops if the plotted frame has no head boxes. Before committing a re-run, open the new `detector_overlay.png` and check that every face is pixelated; if the plotted frame changed, mark its faces in `mask_faces_boxes.json` first. To experiment without touching the published figures, pass `--out` with a scratch folder.

### 3b. The 2,000-frame Mall benchmark

Download and unpack the dataset as described in `experiments/datasets/mall/README.md` (research use only; 92 MB). Wrap the frames into a video without re-encoding (every frame stays byte-identical to the dataset JPEG):

```bash
ffmpeg -framerate 10 -i experiments/datasets/mall/mall_dataset/frames/seq_%06d.jpg -c:v copy -f mov experiments/datasets/mall/mall_frames_mjpeg.mov
```

Run both detectors with the `videoeval` tool built above:

```bash
mkdir -p experiments/datasets/mall/runs
```

```bash
/tmp/videoeval experiments/datasets/mall/mall_frames_mjpeg.mov --fps 10 --detector coreml --model /tmp/cp_models/yolo11n.mlmodelc --out experiments/datasets/mall/runs/counts_yolo11n.csv --boxes-out experiments/datasets/mall/runs/boxes_yolo11n.json
```

```bash
/tmp/videoeval experiments/datasets/mall/mall_frames_mjpeg.mov --fps 10 --out experiments/datasets/mall/runs/counts_apple_upper.csv --boxes-out experiments/datasets/mall/runs/boxes_apple_upper.json
```

```bash
.venv/bin/python -I experiments/mall_eval.py --mall experiments/datasets/mall --out experiments/results/mall
```

Expected (run on 2026-10-12): YOLO11n counts 59% of annotated people, MAE 12.9, precision 93%, recall 55%; Apple upper-body 29%, MAE 22.0; per-camera calibration on 20 frames gives held-out MAE 3.33 (YOLO11n).

## 4. Rehearse the demo (simulated Golden Week, no phone)

Restarting the simulation on the same database is supported (the top bar's "start demo sim" or `POST /sim/start`): the previous run's recommendations are closed and its alerts hidden. For a clean recording, start from an empty database anyway, since the database grows with every run.

1. Stop any running backend, then delete the database:

```bash
rm -f crowdpulse.db crowdpulse.db-wal crowdpulse.db-shm
```

2. Start the backend at 10× speed (6× is the default; at 10× the story from 13:53 to 14:40 takes under 5 minutes):

```bash
CROWDPULSE_SIM_ACCELERATION=10 .venv/bin/uvicorn backend.app.main:app --port 8000
```

3. In a second terminal start the dashboard, then open http://localhost:3000:

```bash
cd dashboard && pnpm dev
```

What you should see, by the SIM CLOCK in the dashboard's top bar (Macau time; timings vary by a minute between runs):

| sim time | where | what |
|---|---|---|
| 13:53 | Overview | Senado Square WARNING (density ≈ 0.45–0.50); some "Deploy staff" recommendations pending |
| 14:04–14:07 | Live map / Zone detail | event ends at St. Dominic's, tour groups arrive; Senado density rises |
| 14:08–14:09 | Zone detail → Senado Square | forecasts turn CRITICAL, the first ones flagged LOW CONFIDENCE — HUMAN REVIEW REQUIRED; alert appears |
| 14:09–14:11 | Interventions | once a CRITICAL forecast reaches 60% confidence, the pending "Deploy staff" is superseded by "Redirect part of … flow around Senado Square" (southbound or north-eastbound, whichever inflow dominates) with route, accessibility note and zh/en/pt notice; each notice ends with the AI clause ("Advice from an AI crowd forecast, approved by staff."). Enter a name in the **Deciding as** field at the top of the page (APPROVE, REJECT and the Alerts page's ack stay disabled until a name is set; for rehearsals and recordings use a fictional name such as `demo-operator-1`). Click VIEW EVIDENCE, then APPROVE |
| 14:20–14:40 | Zone detail | density eases (simulated truth ≈ 0.90 → 0.73–0.75 by 14:40, still above CRITICAL); forecasts move back towards WARNING. Without approval it ends ≈ 0.82–0.87 |

Also check: Alerts (chronological list, ack button, enabled once a name is set), Interventions → audit log shows `intervention_recommended` (actor `system`) and `intervention_approved` with the name you entered as the actor, Reliability (sensor table), Evaluation (metrics on simulated test days, and figures), Privacy. The name is self-declared (there is no login): the log records the name typed, not a checked identity.

Optional: the top bar's "inject surge (Senado)" button adds 300 people instantly.

Note: this scenario gives no early warning. The crowd builds in about 3 minutes, and the first CRITICAL forecast arrives with, not before, the CRITICAL reading. Say so if asked; the 5–15 minute lead is shown by the offline evaluation.

## 4b. Full simulation including the phone app (no field test)

The iOS app can join the running simulation from the iPhone Simulator in video mode, as an extra sensor node. Its wall-clock readings are re-timed onto the simulated clock. The full procedure, a recorded run with and without operator approval, and all screenshots are in `experiments/results/simulation_run/README.md`.

## 4c. SketchFuture route check (no phone)

Start SketchFuture next to the backend and dashboard (`cd sketchfuture && npm install && npm run dev`, http://localhost:4173; set `NEXT_PUBLIC_SKETCHFUTURE_URL` for the dashboard if it runs elsewhere). Only redirect cards whose corridor is on SketchFuture's map have the button. The "Redirect part of … flow around Senado Square" card (table above) has it only when it targets the southbound flow from St. Dominic's: its **Route check in SketchFuture** section then names the corridor that will be closed (Largo de S. Domingos link: three 議事亭前地 footway segments) and the model's direct/detour walking distances (125 m → 216 m), and the plan is "CrowdPulse #N：封閉板樟堂前地↔議事亭前地通道". When it targets the north-eastbound flow from Avenida de Almeida Ribeiro, as in both final recorded runs (`experiments/results/simulation_run/README.md`) and the 17 Oct S04 capture, it reads "SketchFuture route check unavailable: Avenida de Almeida Ribeiro is outside SketchFuture's pedestrian map (no crossing of the avenue is mapped)." Then use the pending "Redirect part of southbound flow around St. Dominic's Square" card (flow from Rua de S. Paulo), as the video's S15 does: its plan is "CrowdPulse #N：封閉大三巴街↔板樟堂前地通道" (three 板樟堂街 / 板樟堂前地 segments; recommendation #721 in `sketchfuture/VERIFICATION.md`). Click **TEST IN SKETCHFUTURE**: a new tab opens SketchFuture with that plan, a notice naming the recommendation it came from, and the comparison of the same 120 people with and without the closure (per-profile travel time, distance, queues, reachability). 撤銷 (undo) restores the plan that was saved in that browser before. After APPROVE the card moves to "Decided / expired" with a smaller *test in SketchFuture* link.

Automated checks: `cd sketchfuture && npm test` (URL plan round-trip and validation; crosswalk consistent with the map: valid closures, recorded distances reproduced by the model's router, at least one cohort route changes, no walker stranded), `cd dashboard && pnpm test` (plan built from a recommendation, card rendering, unsupported corridors), and `backend` tests (`/config` serves the crosswalk for every zone-graph corridor). `cd sketchfuture && npm run crosswalk` regenerates `shared/sketchfuture_crosswalk.json`; commit it together with any map change.

## 5. Privacy checks (backend running)

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/sensor/frame
```

Expected `403`. Media uploads are refused:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/sensor/observation -F "file=@README.md"
```

Expected `403`. An identifying field is refused:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/sensor/observation -H 'content-type: application/json' -d '{"sensor_id":"node-test1","timestamp":"2026-10-03T06:00:00Z","latitude":22.1934,"longitude":113.5397,"location_accuracy_m":5,"heading_deg":10,"device_motion_stability":0.95,"person_count":10,"estimated_density":0.2,"flow_direction_deg":90,"flow_speed_mps":1.0,"vision_confidence":0.9,"camera_obstructed":false,"model_version":"t","face_id":"abc"}'
```

Expected `422`. A decision without a person's name is refused (an empty name, `operator` and `system` are all refused; the request body is checked before the intervention is looked up, so any id works):

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/interventions/1/approve -H 'content-type: application/json' -d '{"operator":"operator"}'
```

Expected `422`.

## 6. iPhone on-device test

What this verifies: on-device detection, frame rate, upload, zone placement, offline buffering, the motion and obstruction checks, and privacy. Away from Macau the phone joins the zone you choose in the app's Setup page.

### 6.1 Install the app

1. Open `ios/CrowdPulseSensor/CrowdPulseSensor.xcodeproj` in Xcode.
2. Xcode → Settings → Accounts: add your Apple ID (a free account works).
3. Select the CrowdPulseSensor target → Signing & Capabilities: choose your team. If Xcode says the bundle identifier is unavailable, change it (for example `org.crowdpulse.sensor.yourname`).
4. Connect the iPhone by cable, choose it as the run destination and press Run. On the phone, enable Settings → Privacy & Security → Developer Mode if asked, and trust the developer under Settings → General → VPN & Device Management.
5. Do not run `xcodegen generate` after setting the team: it rewrites the project and clears the team.

### 6.2 Start a backend the phone can reach

Use a separate database and no simulation, so the phone's own data is not mixed with simulated crowds. (A phone can also join the running demo simulation: its readings are re-timed onto the simulated clock. It only lands in a zone if its GPS is inside the Macau district, so this is for the Simulator or an on-site demo, not the school test.)

```bash
CROWDPULSE_LIVE_SIM=false CROWDPULSE_DATABASE_URL=sqlite:///phone_test.db .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Find the Mac's address (Mac and iPhone on the same Wi-Fi; allow the incoming connection if macOS asks):

```bash
ipconfig getifaddr en0
```

### 6.3 Run the checks

In the app's Setup page: Backend URL `http://<Mac address>:8000` (then tap *Reload zones from backend*), Mode Live, Detector YOLO11n (CoreML), and under *Placement* choose a zone (for example St. Dominic's Square). Set Visible capacity to roughly how many people would fill the view. Tap Start sensing and allow camera, location, motion and local-network access.

| check | how | pass if |
|---|---|---|
| detection | point at people | green boxes on people; "people in view" matches roughly |
| speed | Debug page | frame rate ≥ 5 FPS (target in the brief); note the inference latency |
| upload | Live page | "sent … (HTTP 202)" |
| backend receives | `curl localhost:8000/sensors` on the Mac | your `node-…` with `"mode":"live"` and `"model_version":"ios-yolo11n-0.2"` |
| offline buffer | stop the backend for 30 s, then restart it | "offline — buffering", buffered count rises, then drains to 0 |
| device movement | pick the phone up and move it | stability < 0.75; sensor issue "device moving" in `/sensors` |
| obstruction | cover the lens | "CAMERA OBSTRUCTED / DARK" on screen; `camera_obstructed: true` |
| privacy | Debug page → "Last observation" | payload contains numbers only, no image data |
| count accuracy | point at a group of known size (5, 10, 20 people) | write down app count vs actual; this is your first real phone measurement |

Expected: `/sensors` lists the phone with `"zone_id"` set to the zone you chose, `"placement":"zone_hint"` and its distance from the zone. The Reliability page shows "zone chosen in app · GPS … km away", and the map draws the phone next to that zone. With *By GPS only* chosen, it shows "outside any zone: choose a zone in the app's Setup page".

## Known gaps

| gap | effect on testing | status |
|---|---|---|
| In hybrid mode a phone reports every 1–5 real seconds, which is every 10–50 simulated seconds at 10× | the phone carries fewer readings per minute than a simulated node, so less weight in its zone | by design; document when presenting |
| Zones planned with two sensors (Senado Square, Ruins of St. Paul's) show "1/2 sensors" with one phone | zone reliability ≈ 0.82, confidence ≈ 10% lower | open: in the school test use single-sensor zones (see `docs/experiment-protocol.md`) |
| A phone with no compass (the iOS Simulator reports heading 0°) turns image directions into wrong compass directions | a wrong direction is averaged into its zone's flow | open: check the heading on placement |
| README `uv pip install -e ".[dev]"` failed on a fresh clone | first setup step errored | fixed 2026-10-11 (`uv sync` with a committed `uv.lock`; `pip install -e ".[dev]"` also works now) |
| `pnpm install` exited with code 1 | looked like a failure | fixed 2026-10-11 (placeholder removed from `dashboard/pnpm-workspace.yaml`) |
| Live simulation ignored real-phone data (different clocks) | — | fixed 2026-09-29 (re-timing onto the simulated clock) |
| A pending "deploy staff" blocked the CRITICAL redirect for up to 20 min | — | fixed 2026-09-29 (stronger recommendations supersede weaker pending ones) |
| `GET /zones` took ≈ 3 s | — | fixed 2026-09-29 (single-threaded inference, reads never wait for a refresh): refresh ≈ 0.8 s, reads < 50 ms |
| Stored zone history held partial minutes | history chart and experiment joins used incomplete data | fixed 2026-09-29 (window aligned to minute boundaries) |
| Sensors showed "stale" while the simulation caught up | — | fixed 2026-09-29 (simulated time published after its readings are stored) |
| Phones outside the Macau district were never placed in a zone | — | fixed 2026-09-30 (the zone chosen in the app's Setup page places them; GPS still wins inside the district) |
| Restarting or stopping the sim on an old database showed the previous run's state and blocked recommendations | — | fixed 2026-09-29 (a run's recommendations are closed when it ends; future-dated readings and alerts are hidden) |
