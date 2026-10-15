# Melbourne pedestrian counts (real data for the forecasting check)

City of Melbourne, **Pedestrian Counting System – Past Hour (counts per minute)** and **Pedestrian Counting System – Sensor Locations**, from the City of Melbourne open data platform (<https://data.melbourne.vic.gov.au>). Licence: **CC BY** (attribution: City of Melbourne). Retrieved with `experiments/melbourne_archive.py`.

Why: CrowdPulse's forecasting accuracy so far comes only from our own simulator. These are real minute-level pedestrian counts from 99 sensors, so the same forecasting approach (+5 / +10 / +15 min, compared with a persistence baseline) can be checked on real crowd dynamics. They are not from Macau and they count people passing a sensor line rather than estimating density from a phone camera, so a result here supports the *method*, not CrowdPulse's accuracy in Macau.

## How it is collected

The API keeps only a short window of minute counts, refreshed about every 15 minutes. On 2026-10-12 the window started at 2026-10-11 13:55 UTC in every check from 10:26 to 14:18 UTC; at 14:18 it held 24 hours, and it did not empty at Melbourne midnight. `experiments/melbourne_archive.py` downloads the whole window and merges it into one gzipped CSV per UTC day, de-duplicated on `(location_id, sensing_datetime)`. Collection started on 2026-10-12; the first run was on a team Mac (`archive_log.mac.jsonl`), and since 2026-10-12 14:18 UTC it runs on the team's Linux server, which is the source of truth (`archive_log.jsonl`).

On the server (Ubuntu 24.04, Python 3.12): the script is at `/opt/crowdpulse-melbourne/melbourne_archive.py`, run by `crowdpulse-melbourne-archive.service` (a systemd one-shot service with a throw-away sandboxed user, `DynamicUser=yes`, writing only to `/var/lib/crowdpulse-melbourne`) from `crowdpulse-melbourne-archive.timer` (every hour at minute 50 UTC; missed runs are caught up after downtime). Replace `<server>` with the team's SSH login:

```bash
rsync -a --exclude .archive.lock <server>:/var/lib/crowdpulse-melbourne/ experiments/datasets/melbourne/
```

```bash
ssh <server> 'systemctl list-timers crowdpulse-melbourne-archive.timer; tail -3 /var/lib/crowdpulse-melbourne/archive_log.jsonl'
```

To stop collecting: `ssh <server> 'systemctl disable --now crowdpulse-melbourne-archive.timer'`. To run it by hand anywhere instead:

```bash
python3 experiments/melbourne_archive.py --out experiments/datasets/melbourne
```

## Files

| file | content |
|---|---|
| `minute/YYYY-MM-DD.csv.gz` | one row per sensor and minute with at least one pedestrian (UTC day of `sensing_datetime`): `location_id`, `sensing_datetime` (UTC), `sensing_date` / `sensing_time` (Melbourne local), `direction_1`, `direction_2`, `total_of_directions` |
| `sensors.csv` | sensor id, description, coordinates, direction names, status; refreshed daily |
| `archive_log.jsonl` | one line per server run: rows downloaded, new rows, the window's first and last minute, or the error. Gaps between one run's `last` and the next run's `first` are gaps in the archive. `archive_log.mac.jsonl` holds the first runs on a team Mac. |

In git: `sensors.csv` and the `minute/` files of 11-12 Oct 2026 (UTC) are committed, so the video's S16 renders from a fresh clone. They are a snapshot; the server keeps archiving. The analysis will commit the full archive it uses, with its date, so the result can be reproduced. The archive logs stay out of git.

## Things to know before analysing

- A sensor writes a record only for minutes in which someone passed it. A missing minute for a working sensor means **zero**, not missing data; a sensor with no rows for hours may be offline (check `sensors.csv` status and neighbouring hours).
- The city notes duplicate records for sensors 67, 68 and 69; the archive keeps one row per sensor and minute (7 duplicates removed in the first download).
- Counts are people crossing a line per minute, in two directions. CrowdPulse's zones use a density index; the check needs a stated mapping (e.g. counts per minute relative to each sensor's own busy-hour level), defined before looking at the results.
