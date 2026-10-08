# Local verification — 2026-10-08

## Passed

- `npm test`: 19 model/storage tests. Covers hand-calculated queues, route access restrictions, positive traversal times, population conservation, unreachable/unfinished handling, unchanged-plan equivalence, paired-cohort statistics, nine sensitivity conditions, export/import validation and corrupt/unavailable storage handling.
- `npm run build`: TypeScript checks and production build passed. The bundle includes the offline OSM-derived map; Vite reports a size advisory for the map-containing chunk, not a build error.
- `npm run benchmark`: 12 cases, populations 30/120/300 across unchanged, ramp, link and closure proposals, with five repeats. Also computed nine sensitivity conditions. See `artifacts/benchmark.json` for measured times and actual outputs; times depend on this Mac and are not a phone benchmark.
- `scripts/rebuild_map.py`: recreated a JSON-equivalent map from the included compressed OSM source, without network access.

## Browser acceptance checks

Checked in the Codex in-app browser using actual UI actions. The final pass used the production preview at `http://localhost:4173`:

- Normal initial load and recomputation of a saved plan after reload.
- Keyboard two-endpoint link creation, mouse dragging, and mouse two-click link creation.
- Selecting a stairs edge from the dropdown and applying a 3 m-wide, 4%-slope conversion; inspected updated modeled width/length.
- Applying closures, undoing and redoing the change, then recomputing.
- Starting and pausing journey playback; observed the playback clock advancing.
- Computing the nine-condition matrix and checking its nine data rows.
- Exporting a plan, resetting, then restoring that plan through the file chooser.
- Importing a wrong-map JSON; observed an error without replacing the plan.
- Exporting JSON/CSV; inspected five repeat summaries, all three paired profile results, six CSV rows and paired denominator columns. The final full-report exporter also includes the computed nine-condition sensitivity matrix.
- Inspected attribution, data assumptions, baseline/proposal differences and selected-edge information.

Responsive layout was checked at an actual 390 CSS-pixel width inside a same-origin browser iframe. Measured document and viewport widths were both 390: no horizontal page overflow. This harness was used because the in-app browser's native viewport override produced a minimum effective width of 650 CSS pixels. It is a browser layout check, **not a physical iPhone test**. The final desktop preview measured 800 CSS pixels with no page overflow.

Local browser evidence is saved under ignored `artifacts/browser/desktop.jpg` and `artifacts/browser/mobile.jpg`. Those screenshots and synthetic cohorts are engineering QA, not user-study evidence.

## Interpretation limits

No actual street/accessibility survey, measured pedestrian demand, city deployment, user study or causal intervention evaluation has been performed. The tests establish software behaviour and model consistency. They do not establish real-world navigation, accessibility or construction validity; see `MODEL.md`.
