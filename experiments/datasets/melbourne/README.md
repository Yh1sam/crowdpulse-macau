# Melbourne pedestrian counts (real data for the forecasting check)

City of Melbourne, **Pedestrian Counting System – Past Hour (counts per minute)** and **Pedestrian Counting System – Sensor Locations**, from the City of Melbourne open data platform (<https://data.melbourne.vic.gov.au>). Licence: **CC BY** (attribution: City of Melbourne). Retrieved with `experiments/melbourne_archive.py`.

Why: CrowdPulse's forecasting accuracy so far comes only from our own simulator. These are real minute-level pedestrian counts from 99 sensors, so the same forecasting approach (+5 / +10 / +15 min, compared with a persistence baseline) can be checked on real crowd dynamics. They are not from Macau and they count people passing a sensor line rather than estimating density from a phone camera, so a result here supports the *method*, not CrowdPulse's accuracy in Macau.

## How it is collected

The API keeps only the most recent ~20 hours of minute counts. `experiments/melbourne_archive.py` downloads the whole window and merges it into one gzipped CSV per UTC day, de-duplicated on `(location_id, sensing_datetime)`. It must run at least every ~12 hours to avoid gaps; the team runs it hourly with a scheduler on one Mac. Collection started on 2026-10-12 (first window: 2026-10-11 13:55 UTC).

```bash
python3 experiments/melbourne_archive.py --out experiments/datasets/melbourne
```

## Files

| file | content |
|---|---|
| `minute/YYYY-MM-DD.csv.gz` | one row per sensor and minute with at least one pedestrian (UTC day of `sensing_datetime`): `location_id`, `sensing_datetime` (UTC), `sensing_date` / `sensing_time` (Melbourne local), `direction_1`, `direction_2`, `total_of_directions` |
| `sensors.csv` | sensor id, description, coordinates, direction names, status; refreshed daily |
| `archive_log.jsonl` | one line per run: rows downloaded, new rows, the window's first and last minute, or the error. Gaps between one run's `last` and the next run's `first` are gaps in the archive. |

## Things to know before analysing

- A sensor writes a record only for minutes in which someone passed it. A missing minute for a working sensor means **zero**, not missing data; a sensor with no rows for hours may be offline (check `sensors.csv` status and neighbouring hours).
- The city notes duplicate records for sensors 67, 68 and 69; the archive keeps one row per sensor and minute (7 duplicates removed in the first download).
- Counts are people crossing a line per minute, in two directions. CrowdPulse's zones use a density index; the check needs a stated mapping (e.g. counts per minute relative to each sensor's own busy-hour level), defined before looking at the results.
