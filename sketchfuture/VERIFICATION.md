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
