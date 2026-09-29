# Testing CrowdPulse

Every command below was run on 2026-09-29, either on a fresh clone or on the working copy. Expected results are what those runs produced.
Run commands from the repository root unless a step says otherwise.

## 0. Prerequisites

- macOS with Xcode 16+ (iOS tests and the phone app), Python 3.12, `uv`, Node 20+, `pnpm`, `ffmpeg`.
- Optional: `xcodegen` (`brew install xcodegen`) if you change `ios/CrowdPulseSensor/project.yml`.

Python environment (the `-e ".[dev]"` command in the README currently fails, see "Known gaps"; use this instead):

```bash
uv venv --python 3.12
```

```bash
uv pip install --python .venv/bin/python fastapi "uvicorn[standard]" sqlalchemy pydantic pydantic-settings pandas numpy scikit-learn joblib matplotlib httpx pytest pytest-asyncio
```

If PyPI returns HTTP 503, add `--index-url https://mirrors.aliyun.com/pypi/simple` to the install command.

Dashboard dependencies (`pnpm install` prints `ERR_PNPM_IGNORED_BUILDS` and exits with code 1, but the install is complete):

```bash
cd dashboard && pnpm install
```

## 1. Automated tests

| suite | command | expected |
|---|---|---|
| backend API + ML pipeline | `.venv/bin/python -m pytest -q` | 40 passed |
| dashboard components | `cd dashboard && pnpm test` | 7 passed |
| dashboard production build | `cd dashboard && node node_modules/next/dist/bin/next build` | "Compiled successfully", 10 routes |
| iOS logic + detector | see below | 11 tests, 0 failures |

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

Expected: YOLO11n near-field MAE 1.5, found 97%; Apple built-in MAE 3.0, found 55%. Note: when `frames/` is absent the script prints "alignment ok" without checking anything; the pixel check only runs if the frame images exist.

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
| 14:09–14:11 | Interventions | once a CRITICAL forecast reaches 60% confidence, the pending "Deploy staff" is superseded by "Redirect part of … flow around Senado Square" (southbound or north-eastbound, whichever inflow dominates) with route, accessibility note and zh/en/pt notice. Click VIEW EVIDENCE, then APPROVE |
| 14:20–14:40 | Zone detail | density eases (simulated truth ≈ 0.90 → 0.73–0.75 by 14:40, still above CRITICAL); forecasts move back towards WARNING. Without approval it ends ≈ 0.82–0.87 |

Also check: Alerts (chronological list, ack button), Interventions → audit log shows `intervention_recommended` and `intervention_approved`, Reliability (sensor table), Evaluation (metrics and figures), Privacy.

Optional: the top bar's "inject surge (Senado)" button adds 300 people instantly.

Note: this scenario gives no early warning. The crowd builds in about 3 minutes, and the first CRITICAL forecast arrives with, not before, the CRITICAL reading. Say so if asked; the 5–15 minute lead is shown by the offline evaluation.

## 4b. Full simulation including the phone app (no field test)

The iOS app can join the running simulation from the iPhone Simulator in video mode, as an extra sensor node. Its wall-clock readings are re-timed onto the simulated clock. The full procedure, a recorded run with and without operator approval, and all screenshots are in `experiments/results/simulation_run/README.md`.

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

Expected `422`.

## 6. iPhone on-device test

What this can verify today: on-device detection, frame rate, upload, offline buffering, the motion and obstruction checks, and privacy. It cannot yet put the phone's data into a zone on the map unless the phone is physically in the Macau district (see "Known gaps").

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

In the app's Setup page: Backend URL `http://<Mac address>:8000`, Mode Live, Detector YOLO11n (CoreML). Set Visible capacity to roughly how many people would fill the view. Tap Start sensing and allow camera, location, motion and local-network access.

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

Expected today: `/sensors` lists the phone with the issue "outside any zone" unless you are in the district.

## Known gaps

| gap | effect on testing | status |
|---|---|---|
| Zone assignment is GPS-only for the Macau zones (zone hint honoured only within ~360 m) | a phone elsewhere never appears in a zone, so no forecast and no controlled experiment | open |
| In hybrid mode a phone reports every 1–5 real seconds, which is every 10–50 simulated seconds at 10× | the phone carries fewer readings per minute than a simulated node, so less weight in its zone | by design; document when presenting |
| A phone with no compass (the iOS Simulator reports heading 0°) turns image directions into wrong compass directions | a wrong direction is averaged into its zone's flow | open: check the heading on placement |
| README `uv pip install -e ".[dev]"` fails on a fresh clone | first setup step errors | open: use the command in section 0 |
| `pnpm install` exits with code 1 | looks like a failure | open: install is complete; placeholder in `dashboard/pnpm-workspace.yaml` |
| Live simulation ignored real-phone data (different clocks) | — | fixed 2026-09-29 (re-timing onto the simulated clock) |
| A pending "deploy staff" blocked the CRITICAL redirect for up to 20 min | — | fixed 2026-09-29 (stronger recommendations supersede weaker pending ones) |
| `GET /zones` took ≈ 3 s | — | fixed 2026-09-29 (single-threaded inference, reads never wait for a refresh): refresh ≈ 0.8 s, reads < 50 ms |
| Stored zone history held partial minutes | history chart and experiment joins used incomplete data | fixed 2026-09-29 (window aligned to minute boundaries) |
| Sensors showed "stale" while the simulation caught up | — | fixed 2026-09-29 (simulated time published after its readings are stored) |
| Restarting or stopping the sim on an old database showed the previous run's state and blocked recommendations | — | fixed 2026-09-29 (a run's recommendations are closed when it ends; future-dated readings and alerts are hidden) |
