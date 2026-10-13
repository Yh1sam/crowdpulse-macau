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

## Apple-style interface refactor — 2026-10-09

Replaced the long document-style page with a full-height map workspace, floating toolbars, collapsible planning/results panels, and a mobile sheet layout. The planning panel groups existing controls under Plan, Conditions, and Checks. Results retain reached-count changes, paired cohorts, repeat ranges and model boundaries; wait/distance details use native disclosures. The panel spring preserves its current height and velocity when interrupted. Reduced motion, reduced transparency and increased contrast preferences have dedicated handling.

Verified the final production build in the in-app browser, using same-origin iframes with actual 1440 × 900 and 390 × 844 CSS-pixel viewports:

- Both viewport sizes have no horizontal document overflow. On mobile, the map opens first with collapsed panel headers; only one sheet expands at a time.
- Adjusted population via the keyboard, recomputed results, and undid the parameter change to restore the original 180-person plan.
- Created a link through two keyboard endpoint activations; edit count changed from 3 to 4 and returned to 3 on undo. Selection now falls back to the main stairs after a selected proposed link is undone.
- Selected a traveller profile and verified its selected state. Computed and inspected all nine sensitivity rows and four table columns.
- Opened the assumptions dialog and used Escape to close it; focus returned to its trigger.
- Triggered comparison from the mobile planning sheet; after results appeared, focus was on the visible results-panel toggle instead of the hidden planning panel.
- Enlarged the map, dragged it with native pointer input and observed the SVG viewBox change. Reset the view, displayed both comparison maps, and returned to proposal view.
- Reopened the saved plan after reload: its title and three existing edits remained. Browser warnings/errors were empty in the inspected log.
- `npm test`: all 19 existing model/storage tests passed. TypeScript/production build passed; the existing offline-map chunk-size advisory remains.

Final UI screenshots are ignored local artifacts: `artifacts/browser/apple-desktop.png` and `artifacts/browser/apple-mobile.png`. These are browser viewport checks, not physical-device or user-study validation. A download-event capture in the iframe harness was unavailable; export/import semantics remain covered by the existing storage tests and the earlier browser pass above, rather than claimed as newly verified file delivery.

## CrowdPulse hand-over (URL plans) — 2026-10-09

Added `src/core/plan.ts`: a plan can arrive in the URL fragment as `#plan=<base64url JSON>` of `{ workspace, source }`. It is validated with the same `parseWorkspace` as a file import, becomes the current plan with the previously saved plan kept in undo history, shows its `source` in the status notice, and the fragment is removed from the address bar. `scripts/crosswalk.mjs` derives `../shared/sketchfuture_crosswalk.json` for CrowdPulse's intervention cards: for each of CrowdPulse's seven zone-graph corridors, the street segments whose closure makes the model's walking route between the two zones at least 30% longer (segments are closed one at a time, nearest a hand-picked boundary junction). Results on this map: St. Paul's steps 59 → 86 m (1 segment), upper Rua de S. Paulo 117 → 347 m (1), lower Rua de S. Paulo / Largo de S. Domingos 247 → 335 m (3), Largo de S. Domingos → Senado 125 → 216 m (3), Rua da Tercena link 370 → 570 m (1); the two corridors to Avenida de Almeida Ribeiro are outside the map and marked unsupported.

- `npm test`: 27 tests (19 existing + 8 new in `tests/plan.test.ts`: fragment round-trip with Chinese text, missing/garbled/foreign-map/unknown-segment/oversized plans rejected without replacing the plan, source label trimmed to 120 characters; crosswalk generated for this map and model version, every closure is a valid plan whose street names match, the recorded direct/detour distances are reproduced by `findRoute`, and for every corridor at least one cohort route changes while no walker is stranded). `tsc -b` passes.
- In-app browser (Vite dev server, 800 CSS-pixel pane) with CrowdPulse's backend and dashboard running: clicking **TEST IN SKETCHFUTURE** on recommendation #721 ("Redirect part of southbound flow around St. Dominic's Square", flow from Rua de S. Paulo) opened SketchFuture with the plan "CrowdPulse #721：封閉大三巴街↔板樟堂前地通道", three closed 板樟堂街 / 板樟堂前地 segments drawn on the map, the first one selected, the notice naming the recommendation, and the URL fragment removed. The comparison ran by itself: walkers 6.9 → 7.2 min (+17 s, 40/40 arrive in both plans), wheelchair users 6.7 → 7.2 min (+30 s; 16/40 arrive in both plans, 24 have no step-free route to their destination in either), stroller users 7.4 → 7.7 min (+21 s; 28/40 in both). No console errors.
- 撤銷 restored the plan saved earlier in that browser (我的街區方案, 0 edits) and 重做 brought the CrowdPulse plan back; after the redo the browser's saved copy held the CrowdPulse title and its three closures. Note for operators: a second SketchFuture tab that is navigated away saves *its* plan on `pagehide`, so with two tabs open the last one to leave wins — unchanged behaviour.

These are software and model-consistency checks under the model's assumptions (`MODEL.md`), not evidence about real pedestrian behaviour; a full closure is the extreme case of CrowdPulse's assumed partial diversion.

## Rejected-input recovery — 2026-10-13

Loading/import errors now have independent state from editing and worker errors. Initial comparison and later retries keep a rejected URL/file warning visible; a valid import or explicit dismissal/reset resolves it. Empty `#plan=` is rejected explicitly. A corrupt saved copy remains untouched until the backup/reset flow completes.

- `npm test`: 33 tests passed, including six mounted-App regression cases covering malformed/empty/foreign-map URL plans, retry, dismissal, file replacement, corrupt-storage backup/reset and independent worker failures.
- `npm run build`: TypeScript and production build passed; the existing offline-map bundle advisory remains.
- Fresh browser check on isolated `127.0.0.1:4175/#plan=not-json`: the URL fragment was removed, the original workspace completed comparison, and the rejection alert remained visible after both initial computation and a manual recompute. Screenshot: ignored local `artifacts/browser/invalid-plan-warning.png`.

The broader closure-versus-partial-diversion model and result-return changes are not included in this fix; their scope affects the existing S15 video scenario.
