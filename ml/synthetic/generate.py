"""CLI: generate synthetic observation + ground-truth datasets.

Examples
--------
    python -m ml.synthetic.generate --days 14 --out ml/data
    python -m ml.synthetic.generate --scenario stress_rain_closure --out ml/data --prefix stress
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from ml.synthetic.scenarios import SCENARIOS, training_days
from ml.synthetic.simulator import CrowdSimulator
from shared.schemas import SensorObservation


def generate_days(n_days: int, seed: int, sensor_interval_s: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    obs_all, truth_all = [], []
    for p in training_days(n_days=n_days, seed=seed, sensor_interval_s=sensor_interval_s):
        sim = CrowdSimulator(p)
        obs, truth = sim.run()
        obs_all.extend(obs)
        truth_all.extend(truth)
    return pd.DataFrame(obs_all), pd.DataFrame(truth_all)


def generate_scenario(name: str, sensor_interval_s: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    p = SCENARIOS[name](sensor_interval_s=sensor_interval_s)
    sim = CrowdSimulator(p)
    obs, truth = sim.run()
    return pd.DataFrame(obs), pd.DataFrame(truth)


def validate_sample(df: pd.DataFrame, n: int = 200) -> None:
    """Validate a sample of generated rows against the shared schema (fail loudly)."""
    for rec in df.head(n).to_dict(orient="records"):
        SensorObservation.model_validate(rec)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--interval", type=int, default=20, help="sensor observation interval (s)")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), default=None)
    ap.add_argument("--out", default="ml/data")
    ap.add_argument("--prefix", default="synthetic")
    args = ap.parse_args()

    t0 = time.time()
    if args.scenario:
        obs, truth = generate_scenario(args.scenario, args.interval)
    else:
        obs, truth = generate_days(args.days, args.seed, args.interval)
    validate_sample(obs)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    obs_path = out / f"{args.prefix}_observations.csv.gz"
    truth_path = out / f"{args.prefix}_ground_truth.csv.gz"
    obs.to_csv(obs_path, index=False, compression="gzip")
    truth.to_csv(truth_path, index=False, compression="gzip")
    summary = {
        "observations": int(len(obs)),
        "ground_truth_rows": int(len(truth)),
        "sensors": int(obs["sensor_id"].nunique()),
        "label_distribution": truth["label"].value_counts(normalize=True).round(3).to_dict(),
        "density_mean": round(float(truth["density"].mean()), 3),
        "density_max": round(float(truth["density"].max()), 3),
        "seconds": round(time.time() - t0, 1),
        "files": [str(obs_path), str(truth_path)],
    }
    (out / f"{args.prefix}_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
