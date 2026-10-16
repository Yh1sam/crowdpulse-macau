"""Pre-registered real-data test: forecast SAFE / WARNING / CRITICAL levels on City of Melbourne pedestrian counts.

Implements the analysis fixed in experiments/datasets/melbourne/README.md, section "Pre-registered
analysis". Read that section first: every rule here comes from it. The real run refuses to start
  - before the test window (Melbourne days 18-22 Oct 2026) is over,
  - if the archive holds no data up to the window's end (unless --allow-short-window REASON is given because
    those data are permanently lost; the run then records a deviation with that reason),
  - if the README section's text differs from PREREG_SHA256 below, has uncommitted edits, or was last
    changed by a commit dated after the window opened,
  - if this script has uncommitted changes.

    .venv/bin/python experiments/melbourne_eval.py --dry-run            # plumbing check on 11-12 Oct (UTC): NOT A RESULT
    .venv/bin/python experiments/melbourne_eval.py --print-prereg-hash  # after a dated amendment of the README section
    .venv/bin/python experiments/melbourne_eval.py                      # the real test (from 23 Oct 2026 00:00 AEDT)
    .venv/bin/python experiments/melbourne_eval.py --allow-short-window "server down 22 Oct 09:00-23 Oct 12:00 UTC; API no longer holds it"

The dry run uses only the committed minute files minute/2026-10-11.csv.gz and minute/2026-10-12.csv.gz (with
the archive logs and sensors.csv), trains and scores on the same bins (in-sample) and lowers the minimum number
of training bins, because those files hold one Melbourne day. Its numbers say nothing about forecasting skill;
it only shows that the code runs end to end and writes experiments/results/melbourne_dryrun/. It does not
evaluate the verdict.

Data: City of Melbourne, Pedestrian Counting System, CC BY (see the README).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ml.pipeline.metrics import classification_metrics  # noqa: E402
from shared.config import CLASSES  # noqa: E402

DATA_DIR = REPO / "experiments" / "datasets" / "melbourne"
README = DATA_DIR / "README.md"
README_REL = "experiments/datasets/melbourne/README.md"
SCRIPT_REL = "experiments/melbourne_eval.py"
OUT_REAL = REPO / "experiments" / "results" / "melbourne"
OUT_DRY = REPO / "experiments" / "results" / "melbourne_dryrun"

# SHA-256 of the README's "## Pre-registered analysis" section (heading to next "## " heading, trailing
# spaces and trailing blank lines removed). Update only together with a dated amendment of that section.
PREREG_HEADING = "## Pre-registered analysis"
PREREG_SHA256 = "36f6ff9f99ecdd610f5b74ca433d9bea8317b2f4360cdaf9436fb33b7664f66e"

# ---- fixed by the pre-registration -------------------------------------------------------------------
TZ = "Australia/Melbourne"
TEST_START = pd.Timestamp("2026-10-18 00:00", tz=TZ).tz_convert("UTC")  # 17 Oct 13:00 UTC
TEST_END = pd.Timestamp("2026-10-23 00:00", tz=TZ).tz_convert("UTC")    # 22 Oct 13:00 UTC
TEST_DATES = ["2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22"]
LAST_DATA_DAY_UTC = "2026-10-22"
BIN = pd.Timedelta(minutes=5)
HORIZONS = {5: 1, 10: 2, 15: 3}          # minutes -> bins ahead
PRIMARY_H = 15
N_LAGS = 3
MA_BINS = 3                              # moving-average persistence: mean of the last 15 minutes
SIM_TEST_SUPPORT_H15 = {"SAFE": 14505, "WARNING": 1220, "CRITICAL": 1427}  # ml/models/metrics.json
_N_SIM = sum(SIM_TEST_SUPPORT_H15.values())
P_WARNING = SIM_TEST_SUPPORT_H15["SAFE"] / _N_SIM            # ~0.8457
P_CRITICAL = 1 - SIM_TEST_SUPPORT_H15["CRITICAL"] / _N_SIM   # ~0.9168
MIN_TRAIN_BINS = 576                     # two full days of 5-minute bins
MIN_WARNING_THRESHOLD = 5                # people per 5 minutes
OUTAGE_HOURS = (8, 20)                   # Melbourne time, [08:00, 20:00)
OUTAGE_RUN_BINS = 24                     # 2 hours of covered, empty bins
FIVE_MIN_SHARE = 0.99                    # a sensor is "5 min" if >= 99% of its rows are on 5-minute marks
BOOT_B = 2000
SEED = 0
RF_PARAMS = {"n_estimators": 300, "min_samples_leaf": 5, "class_weight": "balanced_subsample", "n_jobs": -1, "random_state": SEED}
FEATURES = ["level", "level_lag1", "level_lag2", "level_lag3", "level_change_1", "level_change_3"]

# ---- dry run only ------------------------------------------------------------------------------------
DRY_FILES = ("2026-10-11.csv.gz", "2026-10-12.csv.gz")
DRY_MIN_TRAIN_BINS = 200
DRY_LABEL = "DRY RUN — NOT A RESULT"
DRY_VERDICT = "not evaluated (dry run)"

assert TEST_START == pd.Timestamp("2026-10-17 13:00", tz="UTC"), "time-zone database disagrees with AEDT (UTC+11)"
assert TEST_END == pd.Timestamp("2026-10-22 13:00", tz="UTC"), "time-zone database disagrees with AEDT (UTC+11)"


# ---- pre-registration and git checks -----------------------------------------------------------------
def prereg_section(text: str | None) -> str | None:
    if text is None:
        return None
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(PREREG_HEADING)), None)
    if start is None:
        return None
    end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    body = [line.rstrip() for line in lines[start:end]]
    while body and not body[-1]:
        body.pop()
    return "\n".join(body) + "\n"


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def git(*args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def check_prereg() -> dict[str, Any]:
    """Is the README section the one this script was written against, committed, and committed in time?"""
    st: dict[str, Any] = {"expected_sha256": PREREG_SHA256, "problems": []}
    sec = prereg_section(README.read_text(encoding="utf-8")) if README.exists() else None
    if sec is None:
        st["problems"].append(f"{README_REL} has no '{PREREG_HEADING}' section")
        return st
    h = sha256_text(sec)
    st["sha256"] = h
    st["heading"] = sec.splitlines()[0]
    st["hash_matches"] = h == PREREG_SHA256
    if not st["hash_matches"]:
        st["problems"].append("the README section differs from PREREG_SHA256 in this script (amend both together, before the window opens)")
    head_sec = prereg_section(git("show", f"HEAD:{README_REL}"))
    st["committed_unchanged"] = head_sec is not None and sha256_text(head_sec) == h
    if not st["committed_unchanged"]:
        st["problems"].append("the README section has uncommitted edits (or git is unavailable)")
        return st
    log = git("log", "--format=%H %cI", "--", README_REL) or ""
    intro = None
    for line in log.splitlines():  # newest first; walk back while the section is unchanged
        commit, date = line.split(" ", 1)
        s = prereg_section(git("show", f"{commit}:{README_REL}"))
        if s is not None and sha256_text(s) == h:
            intro = (commit, date.strip())
        else:
            break
    if intro is None:
        st["problems"].append("could not find the commit that introduced the README section")
        return st
    st["commit"], st["commit_date"] = intro
    st["committed_before_window"] = pd.Timestamp(intro[1]).tz_convert("UTC") < TEST_START
    if not st["committed_before_window"]:
        st["problems"].append(f"the README section was last changed by commit {intro[0][:10]} dated {intro[1]}, after the test window opened ({TEST_START.isoformat()})")
    # Point 9: the external check is the push to the public repository. Record it; a local check cannot prove when it happened.
    remotes = git("branch", "-r", "--contains", intro[0]) or ""
    st["remote_branches"] = [b.strip() for b in remotes.splitlines() if b.strip() and "->" not in b]
    st["pushed_to_remote"] = bool(st["remote_branches"])
    # A committer date can be set by hand. Earlier commits dated after this one would suggest that (reported, not enforced,
    # because a teammate's clock can also be a little fast).
    intro_t = pd.Timestamp(intro[1]).tz_convert("UTC")
    later = []
    for line in (git("log", "--format=%H %cI", intro[0]) or "").splitlines()[1:]:
        commit, date = line.split(" ", 1)
        if pd.Timestamp(date.strip()).tz_convert("UTC") > intro_t:
            later.append({"commit": commit, "date": date.strip()})
    st["earlier_commits_dated_later"] = later
    return st


def check_script() -> dict[str, Any]:
    status = git("status", "--porcelain", "--", SCRIPT_REL)
    st: dict[str, Any] = {"uncommitted_changes": status is None or status.strip() != "", "problems": []}
    if st["uncommitted_changes"]:
        st["problems"].append(f"{SCRIPT_REL} has uncommitted changes (or is untracked, or git is unavailable)")
    after = []
    for line in (git("log", "--format=%H %cI %s", "--", SCRIPT_REL) or "").splitlines():
        commit, date, *subject = line.split(" ")
        if pd.Timestamp(date).tz_convert("UTC") >= TEST_START:
            after.append({"commit": commit, "date": date, "subject": " ".join(subject)})
    st["commits_after_window_opened"] = after
    return st


# ---- data ----------------------------------------------------------------------------------------------
def data_files(dry_run: bool) -> list[Path]:
    minute = DATA_DIR / "minute"
    if dry_run:
        files = [minute / name for name in DRY_FILES]
        missing = [str(f) for f in files if not f.exists()]
        if missing:
            raise SystemExit(f"dry run needs the committed files: missing {missing}")
        return files
    return sorted(f for f in minute.glob("*.csv.gz") if f.name[:10] <= LAST_DATA_DAY_UTC)


def load_minutes(files: list[Path]) -> pd.DataFrame:
    parts = [pd.read_csv(f, usecols=["location_id", "sensing_datetime", "total_of_directions"]) for f in files]
    d = pd.concat(parts, ignore_index=True)
    d["t"] = pd.to_datetime(d["sensing_datetime"], utc=True)
    d = d.drop_duplicates(["location_id", "t"], keep="last").reset_index(drop=True)
    d["location_id"] = d["location_id"].astype(int)
    d["total"] = d["total_of_directions"].astype(float)
    return d[["location_id", "t", "total"]]


def log_files() -> list[Path]:
    """The archive logs (committed with the results, point 1). Coverage is read from these whenever any exists."""
    return sorted(DATA_DIR.glob("archive_log*.jsonl"))


def read_log_windows(paths: list[Path]) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    windows = []
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "error" in e or not e.get("first") or not e.get("last"):
                continue
            windows.append((pd.Timestamp(e["first"]).tz_convert("UTC"), pd.Timestamp(e["last"]).tz_convert("UTC")))
    return windows


def coverage(files: list[Path], d: pd.DataFrame, logs: list[Path]) -> tuple[pd.DatetimeIndex, np.ndarray, str]:
    """5-minute bins over the loaded UTC days, and which of them the archive covered completely."""
    days = sorted(pd.Timestamp(f.name[:10], tz="UTC") for f in files)
    start, end = days[0], days[-1] + pd.Timedelta(days=1)
    bins = pd.date_range(start, end, freq="5min", inclusive="left")
    minutes = pd.date_range(start, end, freq="1min", inclusive="left")
    loaded_day = np.isin(minutes.normalize(), pd.DatetimeIndex(days))
    if logs:  # a log is present: it decides, even if it records no successful run (then nothing is covered)
        cov = np.zeros(len(minutes), bool)
        for first, last in read_log_windows(logs):
            i0 = minutes.searchsorted(first, side="left")
            i1 = minutes.searchsorted(last, side="right")  # last minute inclusive
            cov[i0:i1] = True
        cov &= loaded_day
        covered = cov.reshape(-1, 5).all(axis=1)
        source = f"archive download windows ({', '.join(p.name for p in logs)}): a bin is covered if all five of its minutes are"
    else:
        pos = ((d["t"] - start) // BIN).to_numpy()
        has = np.bincount(pos[(pos >= 0) & (pos < len(bins))], minlength=len(bins)) > 0
        covered = has & np.r_[has[1:], False]
        source = "no archive log present: a bin is covered if it and the next bin each hold a row from any sensor"
    return bins, covered, source


def day_coverage(covered: np.ndarray, local_date: np.ndarray, dates: list[str]) -> dict[str, float]:
    """Share of each Melbourne day's 5-minute bins that the archive covered. The denominator is the whole day, so bins past
    the last loaded file (data lost at the end of the window) count as uncovered."""
    out = {}
    for dt in dates:
        day_start = pd.Timestamp(dt, tz=TZ)
        n_bins = int((pd.Timestamp((day_start + pd.Timedelta(days=1)).date(), tz=TZ) - day_start) / BIN)
        out[dt] = float(covered[local_date == dt].sum()) / n_bins
    return out


def bin_matrix(d: pd.DataFrame, bins: pd.DatetimeIndex, covered: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sensors = np.array(sorted(d["location_id"].unique()))
    pos = ((d["t"] - bins[0]) // BIN).to_numpy()
    ok = (pos >= 0) & (pos < len(bins))
    M = np.zeros((len(sensors), len(bins)))
    np.add.at(M, (np.searchsorted(sensors, d["location_id"].to_numpy()[ok]), pos[ok]), d["total"].to_numpy()[ok])
    M[:, ~covered] = np.nan
    return sensors, M


def reporting_intervals(d: pd.DataFrame) -> pd.DataFrame:
    share = (d["t"].dt.minute % 5 == 0).groupby(d["location_id"]).mean()
    return pd.DataFrame({"share_rows_on_5min_marks": share, "reporting_interval": np.where(share >= FIVE_MIN_SHARE, "5 min", "1 min")})


def apply_outage_rule(M: np.ndarray, sensors: np.ndarray, local_date: np.ndarray, local_hour: np.ndarray, bins: pd.DatetimeIndex) -> pd.DataFrame:
    """Drop a sensor-day with >= OUTAGE_RUN_BINS covered empty bins in a row between 08:00 and 20:00 Melbourne time."""
    daytime = (local_hour >= OUTAGE_HOURS[0]) & (local_hour < OUTAGE_HOURS[1])
    by_date = {dt: np.nonzero((local_date == dt) & daytime)[0] for dt in np.unique(local_date)}
    local = bins.tz_convert(TZ)
    dropped = []
    for i, sid in enumerate(sensors):
        for dt, idx in by_date.items():
            run = best = 0
            run_start = best_start = best_end = None
            for j in idx:
                v = M[i, j]
                if np.isnan(v):          # uncovered: neither breaks nor extends a run
                    continue
                if v == 0:
                    if run == 0:
                        run_start = j
                    run += 1
                    if run > best:
                        best, best_start, best_end = run, run_start, j
                else:
                    run = 0
            if best >= OUTAGE_RUN_BINS:
                dropped.append({"location_id": int(sid), "local_date": dt, "reason": "outage rule", "empty_bins_in_a_row": best,
                                "first_empty_bin_local": local[best_start].strftime("%H:%M"), "last_empty_bin_local": local[best_end].strftime("%H:%M")})
    for r in dropped:
        M[int(np.nonzero(sensors == r["location_id"])[0][0]), local_date == r["local_date"]] = np.nan
    return pd.DataFrame(dropped, columns=["location_id", "local_date", "reason", "empty_bins_in_a_row", "first_empty_bin_local", "last_empty_bin_local"])


# ---- levels, rows, model ---------------------------------------------------------------------------------
def fit_levels(M: np.ndarray, sensors: np.ndarray, train_bins: np.ndarray, min_train_bins: int) -> tuple[pd.DataFrame, dict[int, np.ndarray]]:
    recs, sorted_train = [], {}
    for i, sid in enumerate(sensors):
        x = M[i, train_bins]
        x = x[~np.isnan(x)]
        rec: dict[str, Any] = {"location_id": int(sid), "n_train_bins": len(x), "T_W": np.nan, "T_C": np.nan, "included": False, "exclusion_reason": ""}
        if len(x) == 0:
            rec["exclusion_reason"] = "no training data"
        else:
            tw = float(np.quantile(x, P_WARNING, method="inverted_cdf"))
            tc = float(np.quantile(x, P_CRITICAL, method="inverted_cdf"))
            rec.update(T_W=tw, T_C=tc, train_share_safe=float((x < tw).mean()), train_share_warning=float(((x >= tw) & (x < tc)).mean()),
                       train_share_critical=float((x >= tc).mean()))
            if len(x) < min_train_bins:
                rec["exclusion_reason"] = f"{len(x)} training bins (< {min_train_bins})"
            elif tw < MIN_WARNING_THRESHOLD:
                rec["exclusion_reason"] = f"T_W = {tw:g} (< {MIN_WARNING_THRESHOLD} people per 5 min)"
            elif tc <= tw:
                rec["exclusion_reason"] = f"T_C = T_W = {tw:g} (no room for WARNING)"
            else:
                rec["included"] = True
                sorted_train[int(sid)] = np.sort(x)
        recs.append(rec)
    return pd.DataFrame(recs).set_index("location_id"), sorted_train


def to_level_code(c: np.ndarray, tw: float, tc: float) -> np.ndarray:
    return (c >= tw).astype(int) + (c >= tc).astype(int)  # 0 SAFE, 1 WARNING, 2 CRITICAL


def shift(a: np.ndarray, k: int) -> np.ndarray:
    """Value at t-k for every t (k < 0 looks ahead), NaN off the ends."""
    out = np.full_like(a, np.nan)
    if k > 0:
        out[k:] = a[:-k]
    elif k < 0:
        out[:k] = a[-k:]
    else:
        out[:] = a
    return out


def build_rows(M: np.ndarray, sensors: np.ndarray, levels: pd.DataFrame, sorted_train: dict[int, np.ndarray], steps: int) -> dict[str, np.ndarray]:
    parts: dict[str, list[np.ndarray]] = {k: [] for k in ["sensor", "origin", "X", "y", "persist", "ma"]}
    for i, sid in enumerate(sensors):
        sid = int(sid)
        if sid not in sorted_train:
            continue
        tw, tc = levels.at[sid, "T_W"], levels.at[sid, "T_C"]
        ref = sorted_train[sid]
        c = M[i]
        lags = [shift(c, k) for k in range(N_LAGS + 1)]
        target = shift(c, -steps)
        valid = ~np.isnan(target)
        for a in lags:
            valid &= ~np.isnan(a)
        idx = np.nonzero(valid)[0]
        if not len(idx):
            continue
        u = [np.searchsorted(ref, a[idx], side="right") / len(ref) for a in lags]
        parts["X"].append(np.column_stack([u[0], u[1], u[2], u[3], u[0] - u[1], u[0] - u[3]]))
        parts["y"].append(to_level_code(target[idx], tw, tc))
        parts["persist"].append(to_level_code(lags[0][idx], tw, tc))
        parts["ma"].append(to_level_code(np.mean(np.column_stack([lags[k][idx] for k in range(MA_BINS)]), axis=1), tw, tc))
        parts["sensor"].append(np.full(len(idx), sid))
        parts["origin"].append(idx)
    if not parts["X"]:
        return {"sensor": np.array([], int), "origin": np.array([], int), "X": np.zeros((0, len(FEATURES))), "y": np.array([], int), "persist": np.array([], int), "ma": np.array([], int)}
    return {k: np.concatenate(v) for k, v in parts.items()}


def subset(rows: dict[str, np.ndarray], mask: np.ndarray) -> dict[str, np.ndarray]:
    return {k: v[mask] for k, v in rows.items()}


def fit_forest(X: np.ndarray, y: np.ndarray):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    model = Pipeline([("imp", SimpleImputer(strategy="median")), ("clf", RandomForestClassifier(**RF_PARAMS))])
    model.fit(X, np.array(CLASSES)[y])
    return model


def predict(model, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = model.predict_proba(X)
    have = list(model.classes_)
    proba = np.zeros((len(X), len(CLASSES)))
    for j, c in enumerate(CLASSES):
        if c in have:
            proba[:, j] = p[:, have.index(c)]
    return proba.argmax(axis=1), proba


# ---- metrics and bootstrap ------------------------------------------------------------------------------
def _div(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return np.divide(a, b, out=np.zeros(np.broadcast(a, b).shape), where=b > 0)  # 0 where undefined (zero_division=0)


def per_class_cm(cm: np.ndarray) -> dict[str, np.ndarray]:
    """Per-class precision, recall and F1 from confusion matrices (..., true, pred), as scikit-learn with zero_division=0."""
    tp = np.diagonal(cm, axis1=-2, axis2=-1)
    n_pred, n_true = cm.sum(axis=-2), cm.sum(axis=-1)
    return {"precision": _div(tp, n_pred), "recall": _div(tp, n_true), "f1": _div(2 * tp, n_pred + n_true)}  # 2tp+fp+fn = n_pred+n_true


def macro_f1_cm(cm: np.ndarray) -> np.ndarray:
    """Macro-F1 from confusion matrices (..., true, pred); F1 = 0 for a class with no true and no predicted rows (zero_division=0)."""
    return per_class_cm(cm)["f1"].mean(axis=-1)


def accuracy_cm(cm: np.ndarray) -> np.ndarray:
    return _div(np.trace(cm, axis1=-2, axis2=-1), cm.sum(axis=(-2, -1)))


def row_shares_cm(cm: np.ndarray) -> np.ndarray:
    """Each true level's rows split by forecast level (rows of the confusion matrix sum to 1)."""
    return _div(cm, cm.sum(axis=-1, keepdims=True))


def block_cms(y: np.ndarray, pred: np.ndarray, block: np.ndarray, n_blocks: int) -> np.ndarray:
    return np.bincount(block * 9 + y * 3 + pred, minlength=n_blocks * 9).reshape(n_blocks, 3, 3).astype(float)


def bootstrap_weights(n_blocks: int) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    return np.stack([np.bincount(rng.integers(0, n_blocks, n_blocks), minlength=n_blocks) for _ in range(BOOT_B)]).astype(float)


def ci(a: np.ndarray) -> list[float]:
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]


def ci_cells(a: np.ndarray) -> list:
    """Percentile interval for every cell of a resampled array (resamples on axis 0): [..., [lo, hi]]."""
    return np.moveaxis(np.percentile(a, [2.5, 97.5], axis=0), 0, -1).tolist()


def verdict(lo: float, hi: float, base: str) -> str:
    """The pre-registered three-way rule on the 95% interval of (model - baseline) macro-F1."""
    if lo > 0:
        return f"the model beats {base}"
    if hi < 0:
        return f"the model is worse than {base}"
    return f"no clear difference between the model and {base}"


def evaluate_horizon(rows: dict[str, np.ndarray], pred_model: np.ndarray, proba: np.ndarray, local_date: np.ndarray, dry: bool) -> dict[str, Any]:
    keys = pd.Series([f"{s}|{local_date[o]}" for s, o in zip(rows["sensor"], rows["origin"])])
    block, uniques = pd.factorize(keys, sort=True)
    nb = len(uniques)
    # Secondary interval (point 7): sensors as blocks, i.e. all of a sensor's test days resampled together.
    sensor_of_block, sensor_ids = pd.factorize(np.array([int(k.split("|")[0]) for k in uniques]), sort=True)
    ns = len(sensor_ids)
    preds = {"model": pred_model, "persistence": rows["persist"], "moving_average": rows["ma"]}
    W, W_s = bootstrap_weights(nb), bootstrap_weights(ns)
    out: dict[str, Any] = {"n_rows": int(len(rows["y"])), "n_sensor_days": nb, "n_sensors": ns, "methods": {}, "differences": {}}
    boots, boots_s, cms = {}, {}, {}
    for name, p in preds.items():
        m = classification_metrics(np.array(CLASSES)[rows["y"]], np.array(CLASSES)[p], proba if name == "model" else None)
        cms[name] = block_cms(rows["y"], p, block, nb)
        total = cms[name].sum(axis=0)
        assert abs(macro_f1_cm(total) - m["f1_macro"]) < 1e-9, "bootstrap F1 disagrees with ml/pipeline/metrics.py"
        pc_total = per_class_cm(total)
        for j, c in enumerate(CLASSES):
            for k in ("precision", "recall", "f1"):
                assert abs(pc_total[k][j] - m["per_class"][c][k]) < 1e-9, f"bootstrap {k} ({c}) disagrees with ml/pipeline/metrics.py"
        agg = np.tensordot(W, cms[name], axes=(1, 0))            # (BOOT_B, 3, 3): one confusion matrix per resample
        cms_s = np.zeros((ns, 3, 3))
        np.add.at(cms_s, sensor_of_block, cms[name])
        agg_s = np.tensordot(W_s, cms_s, axes=(1, 0))
        boots[name], boots_s[name] = macro_f1_cm(agg), macro_f1_cm(agg_s)
        m["f1_macro_ci95"] = ci(boots[name])
        m["accuracy_ci95"] = ci(accuracy_cm(agg))
        pc = per_class_cm(agg)
        m["per_class_ci95"] = {c: {k: ci(pc[k][:, j]) for k in ("precision", "recall", "f1")} for j, c in enumerate(CLASSES)}
        m["confusion_matrix_row_shares"] = row_shares_cm(total).tolist()
        m["confusion_matrix_row_shares_ci95"] = ci_cells(row_shares_cm(agg))
        m["f1_macro_ci95_sensor_blocks"] = ci(boots_s[name])
        out["methods"][name] = m
    for base in ["persistence", "moving_average"]:
        diff = boots["model"] - boots[base]
        point = out["methods"]["model"]["f1_macro"] - out["methods"][base]["f1_macro"]
        lo, hi = ci(diff)
        out["differences"][f"model_minus_{base}"] = {
            "f1_macro": point, "ci95": [lo, hi], "ci95_sensor_blocks": ci(boots_s["model"] - boots_s[base]),
            "verdict": DRY_VERDICT if dry else verdict(lo, hi, "persistence" if base == "persistence" else "moving-average persistence")}
    out["_block_keys"] = list(uniques)
    out["_block_cms"] = cms
    return out


def grouped_f1(rows: dict[str, np.ndarray], pred_model: np.ndarray, groups: np.ndarray) -> list[dict[str, Any]]:
    res = []
    for g in sorted(np.unique(groups)):
        m = groups == g
        rec: dict[str, Any] = {"group": str(g), "n_rows": int(m.sum()), "n_sensors": int(len(np.unique(rows["sensor"][m])))}
        for name, p in {"model": pred_model, "persistence": rows["persist"], "moving_average": rows["ma"]}.items():
            cm = np.bincount(rows["y"][m] * 3 + p[m], minlength=9).reshape(3, 3).astype(float)
            rec[name] = float(macro_f1_cm(cm))
        res.append(rec)
    return res


def failure_case(ev: dict[str, Any], descriptions: dict[int, str]) -> dict[str, Any] | None:
    cm_m, cm_p = ev["_block_cms"]["model"], ev["_block_cms"]["persistence"]
    has_all = (cm_m.sum(axis=2) > 0).all(axis=1)
    if not has_all.any():
        return None
    diff = macro_f1_cm(cm_m) - macro_f1_cm(cm_p)
    cand = np.nonzero(has_all)[0]
    b = int(cand[np.argmin(diff[cand])])
    sid, date = ev["_block_keys"][b].split("|")
    return {"location_id": int(sid), "sensor_description": descriptions.get(int(sid), ""), "local_date": date, "n_rows": int(cm_m[b].sum()),
            "model_f1_macro": float(macro_f1_cm(cm_m[b])), "persistence_f1_macro": float(macro_f1_cm(cm_p[b])),
            "true_critical_predicted_safe": {"model": int(cm_m[b][2, 0]), "persistence": int(cm_p[b][2, 0])},
            "confusion_matrix_model": cm_m[b].astype(int).tolist(), "confusion_matrix_persistence": cm_p[b].astype(int).tolist(),
            "sensor_days_eligible": int(has_all.sum())}


def config_checks() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        from ml.training.train import make_models
        params = make_models(SEED)["random_forest"].named_steps["clf"].get_params()
        diffs = {k: (v, params.get(k)) for k, v in RF_PARAMS.items() if params.get(k) != v}
        out["rf_settings_match_ml_training"] = not diffs
        out["rf_settings_differences"] = {k: {"here": a, "ml/training/train.py": b} for k, (a, b) in diffs.items()}
    except Exception as e:  # report, do not change the pre-registered settings
        out["rf_settings_match_ml_training"] = None
        out["rf_settings_error"] = f"{type(e).__name__}: {e}"
    try:
        sup = json.loads((REPO / "ml" / "models" / "metrics.json").read_text())["per_horizon"]["h15"]["test"]["support"]
        out["simulator_support_matches"] = {k: int(v) for k, v in sup.items()} == SIM_TEST_SUPPORT_H15
    except Exception as e:
        out["simulator_support_matches"] = None
        out["simulator_support_error"] = f"{type(e).__name__}: {e}"
    return out


# ---- reporting -------------------------------------------------------------------------------------------
def fmt(x: float) -> str:
    return f"{x:.3f}"


def fmt_ci(m: dict[str, Any], key: str = "f1_macro") -> str:
    lo, hi = m[f"{key}_ci95"]
    return f"{m[key]:.3f} [{lo:.3f}, {hi:.3f}]"


def fmt_diff(dd: dict[str, Any]) -> str:
    lo, hi = dd["ci95"]
    return f"{dd['f1_macro']:+.3f} [{lo:+.3f}, {hi:+.3f}]"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def json_default(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def summary_md(res: dict[str, Any], dry: bool) -> str:
    L: list[str] = []
    title = DRY_LABEL if dry else "result"
    L.append(f"# Melbourne real-data test: {title}\n")
    if dry:
        L.append(f"> **{DRY_LABEL}.** Plumbing check only. The model was trained and scored on the same bins "
                 "(the committed files of 11-12 Oct UTC = 12 Oct 00:55 to 13 Oct 00:55 Melbourne time), and the level thresholds "
                 "were fitted on those same bins, so every score below is in-sample and says nothing about forecasting skill. "
                 "Do not quote any number from this file, in the video or anywhere else. The real test scores Melbourne days "
                 "18-22 Oct 2026 and has not run.\n")
    pr = res["prereg"]
    L.append(f"Generated by `experiments/melbourne_eval.py` ({res['mode']}) at {res['generated_at_utc']} UTC. "
             f"Implements `experiments/datasets/melbourne/README.md`, section \"{pr.get('heading', '?').lstrip('# ')}\" "
             f"(SHA-256 `{pr.get('sha256', '?')[:16]}…`; " + (f"committed in {pr['commit'][:10]} on {pr['commit_date']}" if pr.get("commit") else "not committed") + ").\n")
    if dry:
        L.append("Dry-run deviations from the pre-registration, all deliberate: data = the two committed minute files only (with the "
                 "archive logs and `sensors.csv`); training = test = all their bins; minimum training bins lowered from 576 to "
                 f"{DRY_MIN_TRAIN_BINS} (the files hold one Melbourne day); the verdict is not evaluated; the real-run guards are "
                 "reported, not enforced.\n")
    dt = res["data"]
    L.append("## Data\n")
    L.append(f"- Minute files: {', '.join(f['file'] for f in dt['files'] if f['file'].startswith('minute/'))} ({dt['rows']:,} rows, "
             f"{dt['sensors_in_data']} sensors: {dt['n_1min']} per-minute, {dt['n_5min']} 5-minute). Other data files: "
             + (", ".join(f"`{f['file']}`" for f in dt["files"] if not f["file"].startswith("minute/")) or "none")
             + ". SHA-256 of each: `manifest.json`.")
    L.append(f"- Coverage: {dt['coverage_source']}. Covered: {dt['covered_bins']:,} of {dt['bins']:,} bins "
             f"({dt['covered_first_utc']} to {dt['covered_last_end_utc']} UTC).")
    if not dry:
        L.append("- Test-day coverage: " + "; ".join(f"{k} {v:.1%}" for k, v in dt["test_day_coverage"].items()) + ".")
    with_rows = [r for r in dt["excluded_sensors"] if r["location_id"] not in set(dt["sensors_listed_without_rows"])]
    L.append(f"- Sensors included: {dt['sensors_included']} of the {dt['sensors_in_data']} with rows. Excluded: "
             + ("; ".join(f"{r['location_id']} ({r['exclusion_reason']})" for r in with_rows) or "none") + ".")
    absent = dt["sensors_listed_without_rows"]
    L.append(f"- Listed in `sensors.csv` but with no rows in the data files used, so excluded: {len(absent)} sensors"
             + (f" ({', '.join(str(s) for s in absent)})." if absent else "."))
    L.append(f"- Sensor-days dropped by the outage rule: " + ("; ".join(f"sensor {r['location_id']} on {r['local_date']} "
             f"({r['empty_bins_in_a_row']} empty bins, {r['first_empty_bin_local']}-{r['last_empty_bin_local']})" for r in dt["dropped_sensor_days"]) or "none") + ".")
    L.append(f"- Level thresholds: p_W = {P_WARNING:.4f}, p_C = {P_CRITICAL:.4f} of each sensor's training 5-minute totals; per-sensor "
             "T_W / T_C and realised training shares in `sensors.csv`.")
    cs = dt["class_shares_h15"]
    L.append(f"- Class shares at +15 min (SAFE / WARNING / CRITICAL): training rows {cs['train']}, test rows {cs['test']} "
             f"(simulator test set: {SIM_TEST_SUPPORT_H15['SAFE'] / _N_SIM:.1%} / {SIM_TEST_SUPPORT_H15['WARNING'] / _N_SIM:.1%} / "
             f"{SIM_TEST_SUPPORT_H15['CRITICAL'] / _N_SIM:.1%}).\n")

    ev = res["horizons"][f"h{PRIMARY_H}"]
    d = ev["differences"]["model_minus_persistence"]
    ls, hs = d["ci95_sensor_blocks"]
    L.append("## Primary outcome: +15 min macro-F1, model minus persistence\n")
    L.append(f"**{fmt_diff(d)}** (95% block-bootstrap interval over {ev['n_sensor_days']} sensor-days, {BOOT_B} resamples). "
             f"Secondary interval with sensor blocks ({ev['n_sensors']} sensors, all of a sensor's test days resampled together): "
             f"[{ls:+.3f}, {hs:+.3f}].\n")
    L.append(f"verdict: {DRY_VERDICT}\n" if dry else f"Verdict: **{d['verdict']}**.\n")
    L.append("| +15 min | macro-F1 [95% CI] | accuracy [95% CI] |")
    L.append("|---|---|---|")
    labels = [("model", "random forest (count-only)"), ("persistence", "persistence (no change)"), ("moving_average", "moving-average persistence")]
    for name, label in labels:
        m = ev["methods"][name]
        L.append(f"| {label} | {fmt_ci(m)} | {fmt_ci(m, 'accuracy')} |")
    d2 = ev["differences"]["model_minus_moving_average"]
    l2, h2 = d2["ci95_sensor_blocks"]
    L.append(f"\nSecondary comparison: model minus moving-average persistence {fmt_diff(d2)} (sensor blocks [{l2:+.3f}, {h2:+.3f}]): "
             f"{d2['verdict']}.\n")
    L.append("Per-class F1 at +15 min [95% CI, sensor-day blocks]:\n")
    L.append("| +15 min | " + " | ".join(CLASSES) + " |")
    L.append("|---|" + "---|" * len(CLASSES))
    for name, label in labels:
        m = ev["methods"][name]
        L.append(f"| {label} | " + " | ".join(f"{m['per_class'][c]['f1']:.3f} [{m['per_class_ci95'][c]['f1'][0]:.3f}, "
                                               f"{m['per_class_ci95'][c]['f1'][1]:.3f}]" for c in CLASSES) + " |")

    L.append("\n## All horizons\n")
    L.append("| horizon | test rows | model macro-F1 | persistence | moving average | model − persistence | model − moving average |")
    L.append("|---|---|---|---|---|---|---|")
    for h in HORIZONS:
        e = res["horizons"][f"h{h}"]
        L.append(f"| +{h} min | {e['n_rows']:,} | {fmt_ci(e['methods']['model'])} | {fmt_ci(e['methods']['persistence'])} | "
                 f"{fmt_ci(e['methods']['moving_average'])} | {fmt_diff(e['differences']['model_minus_persistence'])} | "
                 f"{fmt_diff(e['differences']['model_minus_moving_average'])} |")
    L.append("\nSecondary interval with sensor blocks for the same differences:\n")
    L.append("| horizon | model − persistence | model − moving average |")
    L.append("|---|---|---|")
    for h in HORIZONS:
        e = res["horizons"][f"h{h}"]["differences"]
        a, b = e["model_minus_persistence"], e["model_minus_moving_average"]
        L.append(f"| +{h} min | {a['f1_macro']:+.3f} [{a['ci95_sensor_blocks'][0]:+.3f}, {a['ci95_sensor_blocks'][1]:+.3f}] | "
                 f"{b['f1_macro']:+.3f} [{b['ci95_sensor_blocks'][0]:+.3f}, {b['ci95_sensor_blocks'][1]:+.3f}] |")
    L.append("\nPer-class precision / recall / F1 with intervals, and confusion matrices (counts, and each true level's shares with "
             "intervals), for every method and horizon: `metrics.json`.\n")

    L.append("## +15 min by test day (Melbourne date of the forecast origin)\n")
    L.append("| date | rows | sensors | model | persistence | moving average |")
    L.append("|---|---|---|---|---|---|")
    for r in res["by_day_h15"]:
        L.append(f"| {r['group']} | {r['n_rows']:,} | {r['n_sensors']} | {fmt(r['model'])} | {fmt(r['persistence'])} | {fmt(r['moving_average'])} |")
    L.append("\nMacro-F1 averages all three levels, so a group whose rows are all SAFE scores at most 0.333.")
    L.append("\n## +15 min by reporting interval\n")
    L.append("| sensors | rows | sensors | model | persistence | moving average |")
    L.append("|---|---|---|---|---|---|")
    for r in res["by_interval_h15"]:
        L.append(f"| {r['group']} | {r['n_rows']:,} | {r['n_sensors']} | {fmt(r['model'])} | {fmt(r['persistence'])} | {fmt(r['moving_average'])} |")

    L.append("\n## Failure case (+15 min)\n")
    fc = res["failure_case_h15"]
    if fc:
        where = ("the model fell furthest below persistence" if fc["model_f1_macro"] < fc["persistence_f1_macro"]
                 else "the model was ahead of persistence on every one; its smallest margin (or a tie) was")
        L.append(f"Among {fc['sensor_days_eligible']} test sensor-days whose true levels include all three classes, {where} "
                 f"on sensor {fc['location_id']} ({fc['sensor_description']}) on {fc['local_date']}: macro-F1 "
                 f"{fmt(fc['model_f1_macro'])} vs {fmt(fc['persistence_f1_macro'])} over {fc['n_rows']} rows; true CRITICAL forecast as SAFE: "
                 f"model {fc['true_critical_predicted_safe']['model']}, persistence {fc['true_critical_predicted_safe']['persistence']}.")
    else:
        L.append("No test sensor-day had all three true levels.")

    L.append("\n## Checks\n")
    ck = res["checks"]
    L.append(f"- Random-forest settings equal `make_models()` in `ml/training/train.py`: {ck.get('rf_settings_match_ml_training')}.")
    L.append(f"- Simulator class counts in `ml/models/metrics.json` still equal the pre-registered ones: {ck.get('simulator_support_matches')}.")
    L.append("- Bootstrap macro-F1 and per-class precision / recall / F1 on all rows equal `ml/pipeline/metrics.py`: True (asserted).")
    if pr.get("commit"):
        br = pr.get("remote_branches") or []
        L.append(f"- Pre-registration commit {pr['commit'][:10]} (committer date {pr['commit_date']}) is on a remote-tracking branch "
                 f"(pushed_to_remote): {pr.get('pushed_to_remote')}" + (f" ({', '.join(br)})" if br else "") + ". This shows where it is "
                 "now, not when it was pushed; the push time is checked on the public repository.")
        later = pr.get("earlier_commits_dated_later") or []
        L.append(f"- Earlier commits with a later committer date than the pre-registration commit (a sign of a hand-set date): {len(later)}"
                 + (" (" + "; ".join(f"{c['commit'][:10]} {c['date']}" for c in later[:5]) + (" …" if len(later) > 5 else "") + ")" if later else "") + ".")
    else:
        L.append("- Pre-registration commit (pushed_to_remote, remote branch): not committed, so not checked.")
    g = res["guards"]
    if dry:
        L.append(f"- Real run right now: {'allowed' if not g['problems'] else 'would refuse'}" + (": " + "; ".join(g["problems"]) if g["problems"] else "") + ".")
    L.append("\n## Deviations from the pre-registration\n")
    devs = res["deviations"]
    L.append("\n".join(f"- {x}" for x in devs) if devs else "- None recorded by the script. Add any others here, with the reason.")
    if dry:
        L.append(f"\n> **{DRY_LABEL}.**")
    return "\n".join(L) + "\n"


# ---- main ------------------------------------------------------------------------------------------------
def run(dry: bool, allow_short_window: str | None = None) -> int:
    prereg, script_st = check_prereg(), check_script()
    now = pd.Timestamp.now(tz="UTC")
    problems = list(prereg["problems"]) + list(script_st["problems"])
    if now < TEST_END:
        problems.append(f"the test window is not over (it ends {TEST_END.isoformat()}; now {now.isoformat(timespec='seconds')})")
    files = data_files(dry)
    logs = log_files()
    sensors_csv = DATA_DIR / "sensors.csv"
    if not dry:
        if problems:
            print("Refusing to run the real test:\n  - " + "\n  - ".join(problems), file=sys.stderr)
            return 2
        if not files:
            print("Refusing: no minute files found", file=sys.stderr)
            return 2
    d = load_minutes(files)
    bins, covered, cov_source = coverage(files, d, logs)
    short_window_devs: list[str] = []
    if not dry:
        reach = []
        if d["t"].max() < TEST_END:
            reach.append(f"the archive holds no row at or after {TEST_END.isoformat()}")
        if not covered.any() or bins[np.nonzero(covered)[0][-1]] < TEST_END - BIN:
            last = (bins[np.nonzero(covered)[0][-1]] + BIN).isoformat() if covered.any() else "nothing covered"
            reach.append(f"archive coverage does not reach the end of the test window (last covered bin ends {last})")
        if reach and allow_short_window:
            short_window_devs.append("Data at the end of the test window are missing (" + "; ".join(reach) + "). Run with "
                                     "--allow-short-window: the window was not moved or shortened, and the missing bins count as missing. "
                                     f"Reason given: {allow_short_window}")
        elif reach:
            problems += [r + " (rsync the minute files and archive_log.jsonl from the server; if those data are permanently lost, "
                         "see --allow-short-window)" for r in reach]
        elif allow_short_window:
            print("note: --allow-short-window was given but the archive reaches the end of the window; no deviation recorded", file=sys.stderr)
        if problems:
            print("Refusing to run the real test:\n  - " + "\n  - ".join(problems), file=sys.stderr)
            return 2
    sensors, M = bin_matrix(d, bins, covered)
    local = bins.tz_convert(TZ)
    local_date = np.array(local.strftime("%Y-%m-%d"))
    local_hour = np.asarray(local.hour)
    dropped = apply_outage_rule(M, sensors, local_date, local_hour, bins)
    train_bins = np.ones(len(bins), bool) if dry else np.asarray(bins < TEST_START)
    levels, sorted_train = fit_levels(M, sensors, train_bins, DRY_MIN_TRAIN_BINS if dry else MIN_TRAIN_BINS)
    intervals = reporting_intervals(d)
    levels = levels.join(intervals)
    sens_csv = pd.read_csv(sensors_csv) if sensors_csv.exists() else pd.DataFrame(columns=["location_id", "sensor_description"])
    descriptions = dict(zip(sens_csv["location_id"].astype(int), sens_csv["sensor_description"].astype(str)))
    levels.insert(0, "sensor_description", [descriptions.get(int(s), "") for s in levels.index])
    absent = sorted(set(int(s) for s in sens_csv["location_id"]) - set(int(s) for s in sensors))  # point 3: listed, but no rows

    res: dict[str, Any] = {"mode": DRY_LABEL if dry else "REAL TEST", "generated_at_utc": now.strftime("%Y-%m-%d %H:%M"), "prereg": prereg,
                           "script": script_st, "horizons": {}, "checks": config_checks()}
    print(f"[{'dry run' if dry else 'real'}] {len(d):,} rows, {len(sensors)} sensors, {int(covered.sum())} covered bins; "
          f"{int(levels['included'].sum())} sensors included, sensor-days dropped by the outage rule: {len(dropped)}")
    class_shares = {}
    for h, steps in HORIZONS.items():
        rows = build_rows(M, sensors, levels, sorted_train, steps)
        origin_t = bins[rows["origin"]]
        target_t = origin_t + steps * BIN
        if dry:
            tr = te = np.ones(len(rows["y"]), bool)
        else:
            tr = np.asarray(target_t < TEST_START)
            te = np.asarray((origin_t >= TEST_START) & (target_t < TEST_END))
        R_tr, R_te = subset(rows, tr), subset(rows, te)
        if len(R_tr["y"]) == 0 or len(R_te["y"]) == 0:
            print(f"no {'training' if len(R_tr['y']) == 0 else 'test'} rows at +{h} min", file=sys.stderr)
            return 3
        model = fit_forest(R_tr["X"], R_tr["y"])
        pred, proba = predict(model, R_te["X"])
        ev = evaluate_horizon(R_te, pred, proba, local_date, dry)
        ev["n_train_rows"] = int(len(R_tr["y"]))
        res["horizons"][f"h{h}"] = ev
        m = ev["methods"]
        print(f"[+{h:>2} min] train {len(R_tr['y']):,} / test {len(R_te['y']):,} rows | macro-F1 model {m['model']['f1_macro']:.3f}, "
              f"persistence {m['persistence']['f1_macro']:.3f}, moving average {m['moving_average']['f1_macro']:.3f} | "
              f"model - persistence {ev['differences']['model_minus_persistence']['f1_macro']:+.3f} {ev['differences']['model_minus_persistence']['ci95']}")
        if h == PRIMARY_H:
            share = lambda y: " / ".join(f"{(y == k).mean():.1%}" for k in range(3))  # noqa: E731
            class_shares = {"train": share(R_tr["y"]), "test": share(R_te["y"])}
            res["by_day_h15"] = grouped_f1(R_te, pred, local_date[R_te["origin"]])
            res["by_interval_h15"] = grouped_f1(R_te, pred, np.array([levels.at[int(s), "reporting_interval"] for s in R_te["sensor"]]))
            res["failure_case_h15"] = failure_case(ev, descriptions)
            levels["test_rows_h15"] = pd.Series(R_te["sensor"]).value_counts().reindex(levels.index).fillna(0).astype(int)
    if absent:
        levels = pd.concat([levels, pd.DataFrame(
            {"sensor_description": [descriptions.get(s, "") for s in absent], "n_train_bins": 0, "included": False,
             "exclusion_reason": "no rows in the data files used", "test_rows_h15": 0}, index=pd.Index(absent, name="location_id"))]).sort_index()
    excluded = levels[~levels["included"].astype(bool)].reset_index()[["location_id", "exclusion_reason"]].to_dict("records")
    cov_idx = np.nonzero(covered)[0]
    used = [(f"minute/{f.name}", f) for f in files] + [(p.name, p) for p in logs] + ([("sensors.csv", sensors_csv)] if sensors_csv.exists() else [])
    res["data"] = {
        "files": [{"file": name, "sha256": sha256_file(p)} for name, p in used], "rows": int(len(d)),
        "sensors_in_data": int(len(sensors)), "sensors_listed_without_rows": absent,
        "n_1min": int((intervals["reporting_interval"] == "1 min").sum()),
        "n_5min": int((intervals["reporting_interval"] == "5 min").sum()), "coverage_source": cov_source,
        "bins": int(len(bins)), "covered_bins": int(covered.sum()),
        "covered_first_utc": bins[cov_idx[0]].strftime("%Y-%m-%d %H:%M") if len(cov_idx) else None,
        "covered_last_end_utc": (bins[cov_idx[-1]] + BIN).strftime("%Y-%m-%d %H:%M") if len(cov_idx) else None,
        "test_day_coverage": day_coverage(covered, local_date, TEST_DATES),
        "sensors_included": int(levels["included"].sum()), "excluded_sensors": excluded,
        "dropped_sensor_days": dropped.to_dict("records"), "class_shares_h15": class_shares,
        "p_warning": P_WARNING, "p_critical": P_CRITICAL,
    }
    devs = short_window_devs + [f"Code change after the window opened: {c['commit'][:10]} {c['date']} \"{c['subject']}\"" for c in script_st["commits_after_window_opened"]]
    if res["checks"].get("rf_settings_match_ml_training") is False:
        devs.append(f"ml/training/train.py random-forest settings now differ from the pre-registered ones (used here: the pre-registered ones): {res['checks']['rf_settings_differences']}")
    res["deviations"] = devs
    res["guards"] = {"problems": problems}

    out = OUT_DRY if dry else OUT_REAL
    out.mkdir(parents=True, exist_ok=True)
    public = {k: v for k, v in res.items()}
    public["horizons"] = {h: {k: v for k, v in e.items() if not k.startswith("_")} for h, e in res["horizons"].items()}
    (out / "metrics.json").write_text(json.dumps(public, indent=2, default=json_default) + "\n")
    levels.reset_index().to_csv(out / "sensors.csv", index=False)
    dropped.to_csv(out / "excluded_sensor_days.csv", index=False)
    runs, start = [], None
    for j in range(len(bins) + 1):
        c = j < len(bins) and covered[j]
        if c and start is None:
            start = j
        if not c and start is not None:
            runs.append({"start_utc": bins[start].isoformat(), "end_utc": (bins[j - 1] + BIN).isoformat(), "bins": j - start})
            start = None
    pd.DataFrame(runs, columns=["start_utc", "end_utc", "bins"]).to_csv(out / "coverage.csv", index=False)
    import sklearn
    manifest = {"mode": res["mode"], "generated_at_utc": res["generated_at_utc"], "git_head": (git("rev-parse", "HEAD") or "").strip(),
                "prereg_sha256": prereg.get("sha256"), "prereg_commit": prereg.get("commit"),
                "prereg_pushed_to_remote": prereg.get("pushed_to_remote"), "prereg_remote_branches": prereg.get("remote_branches"),
                "allow_short_window": allow_short_window, "files": res["data"]["files"],
                "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "summary.md").write_text(summary_md(res, dry), encoding="utf-8")
    print(f"wrote {out / 'summary.md'}" + (f"  [{DRY_LABEL}]" if dry else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help=f"plumbing check on the committed 11-12 Oct files ({DRY_LABEL})")
    ap.add_argument("--print-prereg-hash", action="store_true", help="print the SHA-256 of the README's pre-registration section")
    ap.add_argument("--allow-short-window", metavar="REASON",
                    help="real run only: proceed although the archive does not reach the end of the test window, because those data "
                         "are permanently lost; the window is not changed and the run records a deviation with REASON")
    args = ap.parse_args()
    if args.allow_short_window is not None:
        if args.dry_run or args.print_prereg_hash:
            ap.error("--allow-short-window applies to the real run only")
        if not args.allow_short_window.strip():
            ap.error("--allow-short-window needs a reason (why the data at the end of the window are permanently lost)")
    if args.print_prereg_hash:
        sec = prereg_section(README.read_text(encoding="utf-8"))
        if sec is None:
            print(f"no '{PREREG_HEADING}' section in {README_REL}", file=sys.stderr)
            return 1
        h = sha256_text(sec)
        print(h)
        print("matches PREREG_SHA256 in this script" if h == PREREG_SHA256 else "differs from PREREG_SHA256 in this script", file=sys.stderr)
        return 0
    return run(args.dry_run, args.allow_short_window.strip() if args.allow_short_window else None)


if __name__ == "__main__":
    sys.exit(main())
