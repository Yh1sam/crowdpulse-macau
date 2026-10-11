# Third-party notices

CrowdPulse Macau's own code, documentation, synthetic data, trained models and figures are licensed under the GNU Affero General Public License v3.0 only (`LICENSE`). The items below come from third parties and keep their own licences.

## Bundled in this repository

| item | where | source | licence |
|---|---|---|---|
| YOLO11n person-detection weights, converted to CoreML | `ios/CrowdPulseSensor/Resources/yolo11n.mlpackage` (conversion: `ios/CrowdPulseSensor/Tools/export_yolo.py`) | Ultralytics YOLO11, <https://github.com/ultralytics/ultralytics> | AGPL-3.0 (<https://ultralytics.com/license>); the licence is also recorded in the model's own metadata. AGPL-3.0 is why this whole repository is AGPL-3.0. A closed-source or App Store build needs an Ultralytics Enterprise licence or a different detector (Apple's built-in detector is the in-app fallback). |
| "Diagonal crosswalk at Yonge & Dundas in Toronto" video, by Raysonho @ Open Grid Scheduler / Grid Engine | `ios/CrowdPulseSensor/Resources/sample_crowd.mp4` (640×360, 10 fps transcode), `ios/CrowdPulseSensor/Tests/Resources/crossing_t32.png` (frame 324), the hand counts in `experiments/datasets/video/` and the frames shown in `experiments/results/video/` and `experiments/results/simulation_run/` | Wikimedia Commons, <https://commons.wikimedia.org/wiki/File:DiagonalCrosswalkYongeDundas.webm> | CC0 1.0 (public-domain dedication); see `experiments/datasets/video/README.md` |
| OpenStreetMap extract and the street graph derived from it | `sketchfuture/data/macau-osm.json.gz`, `sketchfuture/src/data/macau.json`, and the street-segment ids and names in `shared/sketchfuture_crosswalk.json` | © OpenStreetMap contributors, <https://www.openstreetmap.org/copyright> | Open Database License 1.0; see `sketchfuture/DATA_NOTICE.md` |
| Template icons | `dashboard/public/*.svg` | create-next-app (Next.js) | MIT |

## Used at run time, not bundled

- **Map tiles** on the dashboard's Live map are loaded from `tile.openstreetmap.org`: map data © OpenStreetMap contributors (ODbL), shown in the map's attribution control. The OpenStreetMap Foundation tile usage policy applies; it does not allow heavy or production traffic, so a deployment needs its own tile source.
- **Package dependencies** are installed by uv/pip, pnpm and npm and are not part of this repository. Main direct dependencies and their declared licences, read from the installed package metadata on 2026-10-11:
  - Python: FastAPI (MIT), Uvicorn (BSD-3-Clause), SQLAlchemy (MIT), Pydantic and pydantic-settings (MIT), pandas (BSD-3-Clause), NumPy (BSD-3-Clause and others), scikit-learn (BSD-3-Clause), joblib (BSD-3-Clause), Matplotlib (Matplotlib licence, PSF-based), HTTPX (BSD-3-Clause).
  - Dashboard: Next.js, React, Recharts, SWR and Tailwind CSS (MIT); MapLibre GL JS (BSD-3-Clause).
  - SketchFuture: React and Vite (MIT).
