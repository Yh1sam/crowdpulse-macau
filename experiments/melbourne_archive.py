"""Archive the City of Melbourne's per-minute pedestrian counts for the real-data forecasting check.

The open-data API keeps only a short window of minute counts (observed on 2026-10-12: about the last
24 hours), so this script is run every hour (a systemd timer on the team's server; see
experiments/datasets/melbourne/README.md) and merges each download into one
gzipped CSV per UTC day, de-duplicated on (location_id, sensing_datetime). Every run appends a line to
archive_log.jsonl with the window it saw, so gaps in the archive can be found and reported later.

Data: City of Melbourne, "Pedestrian Counting System - Past Hour (counts per minute)" and
"Pedestrian Counting System - Sensor Locations", CC BY. Standard library only, so the scheduled job
does not depend on the project's virtual environment.

    python3 experiments/melbourne_archive.py --out experiments/datasets/melbourne
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import gzip
import io
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets"
COUNTS = f"{API}/pedestrian-counting-system-past-hour-counts-per-minute/exports/csv?delimiter=%2C"
SENSORS = f"{API}/pedestrian-counting-system-sensor-locations/exports/csv?delimiter=%2C"
COLUMNS = ["location_id", "sensing_datetime", "sensing_date", "sensing_time", "direction_1", "direction_2", "total_of_directions"]
USER_AGENT = "CrowdPulse-Macau-hackathon-archiver/1.0 (research use; hourly)"


def download(url: str, attempts: int = 3) -> list[dict[str, str]]:
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                text = r.read().decode("utf-8-sig")
            return list(csv.DictReader(io.StringIO(text)))
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(30 * attempt)
    return []


def read_day(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    if not path.exists():
        return {}
    with gzip.open(path, "rt", newline="") as f:
        return {(r["location_id"], r["sensing_datetime"]): r for r in csv.DictReader(f)}


def write_atomic(path: Path, rows: list[dict[str, str]], columns: list[str], gz: bool) -> None:
    tmp = path.with_name(path.name + ".tmp")
    opener = (lambda p: gzip.open(p, "wt", newline="")) if gz else (lambda p: open(p, "w", newline=""))
    with opener(tmp) as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def archive(out: Path) -> dict:
    rows = download(COUNTS)
    if not rows or set(COLUMNS) - set(rows[0]):
        raise RuntimeError(f"unexpected export: {len(rows)} rows, columns {list(rows[0]) if rows else []}")
    by_day: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        day = datetime.fromisoformat(r["sensing_datetime"]).astimezone(timezone.utc).date().isoformat()
        by_day.setdefault(day, []).append(r)
    minute_dir = out / "minute"
    minute_dir.mkdir(parents=True, exist_ok=True)
    new_rows = 0
    for day, day_rows in sorted(by_day.items()):
        path = minute_dir / f"{day}.csv.gz"
        merged = read_day(path)
        before = len(merged)
        for r in day_rows:  # a later download wins if the city revised a count
            merged[(r["location_id"], r["sensing_datetime"])] = {c: r[c] for c in COLUMNS}
        new_rows += len(merged) - before
        ordered = sorted(merged.values(), key=lambda r: (r["sensing_datetime"], int(r["location_id"])))
        write_atomic(path, ordered, COLUMNS, gz=True)
    sensors_path = out / "sensors.csv"
    if not sensors_path.exists() or time.time() - sensors_path.stat().st_mtime > 86400:
        sensors = download(SENSORS)
        if sensors:
            write_atomic(sensors_path, sensors, list(sensors[0]), gz=False)
    stamps = sorted(r["sensing_datetime"] for r in rows)
    return {"rows": len(rows), "new_rows": new_rows, "first": stamps[0], "last": stamps[-1],
            "sensors": len({r["location_id"] for r in rows}), "days": sorted(by_day)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "datasets" / "melbourne")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    log = args.out / "archive_log.jsonl"
    with open(args.out / ".archive.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("another archive run is in progress", file=sys.stderr)
            return 0
        entry = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        try:
            entry.update(archive(args.out))
            status = 0
        except Exception as e:  # recorded, so a failed hour shows up in the log rather than as a silent gap
            entry["error"] = f"{type(e).__name__}: {e}"
            status = 1
        with open(log, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(json.dumps(entry))
        return status


if __name__ == "__main__":
    sys.exit(main())
