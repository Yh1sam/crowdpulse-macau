# OpenStreetMap data notice

Map data © OpenStreetMap contributors, licensed under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See [OpenStreetMap copyright and licence](https://www.openstreetmap.org/copyright).

- Source query: <https://api.openstreetmap.org/api/0.6/map?bbox=113.5372,22.1923,113.5426,22.1984>
- Retrieved: 2026-10-08. This is the retrieval date, not a guarantee that every OSM feature was surveyed recently.
- Raw, compressed extract: `data/macau-osm.json.gz`.
- Derived map/graph: `src/data/macau.json`, also supplied under ODbL 1.0.
- Reproduction: `python3 scripts/rebuild_map.py` (offline).

The derived graph retains source way IDs and original coordinates/polylines, selects a connected local network, and adds **prototype model assumptions** for unknown widths/slopes, service capacities and landmark anchors. The application displays attribution and separates proposed links from baseline geometry. App code is distinct from the OSM-derived database; this notice describes the database licence.

OSM is community-maintained data. The extraction is not a verified mobility survey. Rendered context includes buildings and road outlines that may not participate in the modeled walking graph. A baseline road or path in this snapshot does not establish current public access or actual wheelchair accessibility.
