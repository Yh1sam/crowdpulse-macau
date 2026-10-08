# SketchFuture — 澳門街道實驗室

A local, responsive web app for comparing hypothetical pedestrian-network changes in the real Senado Square → St. Dominic's → Ruins of St. Paul's district. Street geometry and stairs come from an attributed OpenStreetMap snapshot. Walking conditions, demand and proposed construction are model assumptions.

## Start

```sh
cd sketchfuture
npm install --cache /tmp/sketchfuture-npm-cache
npm run dev
```

Open <http://localhost:4173>. This app has its own package and does not require the CrowdPulse backend, ML models, iOS app, map tiles or API credentials. All simulation and saved plans stay in the browser. Local storage is specific to this browser/device; export a plan to move it elsewhere.

For a production build:

```sh
npm run build
npm run preview
```

Stop the dev server before starting preview because both use port 4173. The generated `dist/` directory can be served by a static web server. No hosted deployment is created by these commands.

## Use

1. Try one of the three example questions, or choose a tool: inspect, draw a link, propose a step-free conversion, or toggle a closure.
2. A link can be dragged between blue connection points or created by selecting two points with Enter. A dropdown below the map also selects an existing edge; **Apply current tool** supports keyboard-only ramp/closure edits.
3. Configure proposed width/slope, population, departure window and capacity. **Compare** runs baseline and proposal on exactly the same generated people.
4. Click a profile to highlight its sample Senado-to-Ruins route. Switch to side-by-side maps, play the computed journeys or scrub the timeline. The result cards show the **whole simulation**, not playback progress.
5. Check nine demand/speed conditions. A negative paired time difference means faster for people who arrive in both plans. Reachability changes are reported separately.
6. Export the plan, full JSON report, or CSV metrics. Importing a plan revalidates it and recomputes results. Invalid files do not replace the current plan. Reset is confirmed and undoable within the current session.

Changes and parameters are automatically saved. Undo/redo history and simulation outputs are session-local; reopening reloads the plan and recomputes outputs. Corrupt saved data is preserved and blocks automatic overwriting until the user explicitly backs it up and starts again. Storage failures are shown with an export instruction.

## Checks

```sh
npm test
npm run build
npm run benchmark
python3 scripts/rebuild_map.py
```

Tests check hand-calculated routing/queues, access restrictions, conservation, identical unmodified scenarios, paired statistics, sensitivity, import validation and storage recovery. The benchmark writes `artifacts/benchmark.json`; map rebuilding uses the included compressed source extract without network access.

See [MODEL.md](MODEL.md) for equations, interpretation and limits, [DATA_NOTICE.md](DATA_NOTICE.md) for map provenance/licensing, and [VERIFICATION.md](VERIFICATION.md) for the validation record.

## Scope

This is a hypothesis-comparison prototype. It does **not** establish measured pedestrian behaviour, actual wheelchair accessibility, construction feasibility, route safety, real-world congestion reduction, or regulatory compliance. It is not a navigation service. In particular, roads may be represented by their centreline, and missing elevators, indoor routes, kerbs, slope and width data can change reachability conclusions.
