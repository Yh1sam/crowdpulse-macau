"""Figures + summary for the end-to-end simulation runs in experiments/results/simulation_run/.

Run A: an operator approves the Senado Square redirect when it is recommended.
Run B: same scenario, the operator takes no action (counterfactual).
Both runs: backend with the Golden-Week live simulation at 10x, plus the iOS app in the iPhone Simulator
in video mode (YOLO11n on a CC0 crossing clip) acting as an extra sensor node at Avenida de Almeida Ribeiro.

    .venv/bin/python experiments/simulation_figures.py
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from shared.config import load_config  # noqa: E402

D = Path("experiments/results/simulation_run")
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
STATUS = {"WARNING": "#fab219", "CRITICAL": "#d03b3b"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "legend.frameon": False})


def load(tag: str):
    t = pd.read_csv(D / f"{tag}_timeline.csv")
    t["t"] = pd.to_datetime("2026-10-03 " + t["sim_time"])
    ev = json.loads((D / f"{tag}_events.json").read_text()) if (D / f"{tag}_events.json").exists() else []
    return t, ev


def first(t: pd.DataFrame, mask) -> datetime | None:
    m = t[mask]
    return m["t"].iloc[0] if len(m) else None


def milestones(t: pd.DataFrame, ev: list[dict]) -> dict:
    s = t[t.zone == "senado_square"]
    out = {
        "first_critical_forecast": first(s, (s.p5 == "CRITICAL") | (s.p10 == "CRITICAL") | (s.p15 == "CRITICAL")),
        "first_confident_critical_forecast": first(s, ((s.p5 == "CRITICAL") & (s.eff5 >= 0.6)) | ((s.p10 == "CRITICAL") & (s.eff10 >= 0.6)) | ((s.p15 == "CRITICAL") & (s.eff15 >= 0.6))),
        "first_critical_observed": first(s, s.state == "CRITICAL"),
        "first_critical_true": first(s, s.true_density >= load_config()["congestion_thresholds"]["critical"]) if "true_density" in s else None,
        "redirect_recommended": first(s, s.pending_interventions.fillna("").str.contains("senado_square:redirect_flow|senado_square:reduce_inflow")),
    }
    for e in ev:
        if e["event"] == "ui" and e.get("action") == "approve":
            out["approved"] = pd.Timestamp("2026-10-03 " + e["sim_time"] + ":00")
    return out


def main() -> None:
    cfg = load_config()
    th = cfg["congestion_thresholds"]
    a, ev_a = load("A")
    b, ev_b = load("B") if (D / "B_timeline.csv").exists() else (None, [])
    ma = milestones(a, ev_a)
    mb = milestones(b, ev_b) if b is not None else {}
    sa = a[a.zone == "senado_square"]
    sb = b[b.zone == "senado_square"] if b is not None else None

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, gridspec_kw={"height_ratios": [3, 3, 1.6]})
    ax = axes[0]
    ax.plot(sa.t, sa.true_density, color=BLUE, lw=2, label="A: operator approves the redirect")
    if sb is not None:
        ax.plot(sb.t, sb.true_density, color=ORANGE, lw=2, label="B: no action (counterfactual)")
    ax.set_title("Senado Square: true crowd density in the simulation", loc="left", fontsize=11, fontweight="bold")
    ax2 = axes[1]
    ax2.plot(sa.t, sa.density, color=BLUE, lw=1.6, label="A: approved")
    if sb is not None:
        ax2.plot(sb.t, sb.density, color=ORANGE, lw=1.6, label="B: no action")
    ax2.set_title("Senado Square: what the sensors reported (camera counts under-read dense crowds)", loc="left", fontsize=11, fontweight="bold")
    for axx in (ax, ax2):
        axx.axhline(th["warning"], color=STATUS["WARNING"], lw=1, ls=":")
        axx.axhline(th["critical"], color=STATUS["CRITICAL"], lw=1, ls=":")
        axx.text(sa.t.iloc[-1], th["critical"] - 0.012, "CRITICAL threshold", color=INK2, fontsize=8, ha="right", va="top")
        axx.text(sa.t.iloc[-1], th["warning"] - 0.012, "WARNING threshold", color=INK2, fontsize=8, ha="right", va="top")
        axx.set_ylabel("relative density index (0-1)")
        axx.set_ylim(0.3, 1.02)
        axx.legend(loc="upper left", fontsize=9)
        for key, label, style, side in [("first_critical_forecast", "first CRITICAL forecast", "--", -1), ("redirect_recommended", "redirect recommended", "-.", 1), ("approved", "operator approves (A)", "-", 1)]:
            if ma.get(key) is not None:
                axx.axvline(ma[key], color=INK2, lw=1, ls=style)
                if axx is ax:  # labels on alternating sides of their line so close events stay readable
                    axx.text(ma[key] + pd.Timedelta(seconds=15 * side), 0.34, label, color=INK, fontsize=8, va="bottom", ha="left" if side > 0 else "right", rotation=90)
    ph = a[a.zone == "almeida_ribeiro"]
    ax3 = axes[2]
    ax3.plot(ph.t, ph.phone_count, color=AQUA, lw=1.4, drawstyle="steps-post")
    ax3.set_ylabel("people counted")
    ax3.set_title("Phone node at Avenida de Almeida Ribeiro (iOS app, YOLO11n on-device, run A): people in view per reading", loc="left", fontsize=11, fontweight="bold")
    ax3.set_xlabel("simulated Macau time, Golden Week afternoon (run at 10x real time)")
    for axx in axes:
        axx.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
    fig.tight_layout()
    fig.savefig(D / "simulation_run_timeline.png", dpi=160)
    plt.close(fig)

    def peak(s, col, after):
        m = s[s.t >= after] if after is not None else s
        return float(m[col].max()) if len(m) else float("nan")

    def minutes_at_or_above(s, col, level):
        m = s[s[col] >= level].sort_values("t")
        return round(m.t.dt.floor("min").nunique(), 0)

    def fmt(x):
        return x.strftime("%H:%M:%S") if x is not None and not pd.isna(x) else "–"

    after = ma.get("approved")
    rows = [
        ("first CRITICAL forecast (any horizon, incl. low confidence)", fmt(ma["first_critical_forecast"]), fmt(mb.get("first_critical_forecast"))),
        ("first confident CRITICAL forecast (≥ 60%)", fmt(ma["first_confident_critical_forecast"]), fmt(mb.get("first_confident_critical_forecast"))),
        ("first CRITICAL reading from the sensors", fmt(ma["first_critical_observed"]), fmt(mb.get("first_critical_observed"))),
        ("first time the true density crossed CRITICAL", fmt(ma["first_critical_true"]), fmt(mb.get("first_critical_true"))),
        ("redirect recommended", fmt(ma["redirect_recommended"]), fmt(mb.get("redirect_recommended"))),
        ("operator approved", fmt(ma.get("approved")), "never"),
        ("peak true density after approval time", f"{peak(sa, 'true_density', after):.2f}", f"{peak(sb, 'true_density', after):.2f}" if sb is not None else "–"),
        ("minutes with true density ≥ CRITICAL", f"{minutes_at_or_above(sa, 'true_density', th['critical']):.0f}", f"{minutes_at_or_above(sb, 'true_density', th['critical']):.0f}" if sb is not None else "–"),
        ("true density at end of run", f"{sa.true_density.iloc[-1]:.2f}", f"{sb.true_density.iloc[-1]:.2f}" if sb is not None else "–"),
        ("backend refresh time, median / max (ms)", f"{a.refresh_ms.median():.0f} / {a.refresh_ms.max():.0f}", f"{b.refresh_ms.median():.0f} / {b.refresh_ms.max():.0f}" if b is not None else "–"),
        ("phone node online (share of samples)", f"{(ph.phone_status == 'online').mean():.0%}", f"{(b[b.zone == 'almeida_ribeiro'].phone_status == 'online').mean():.0%}" if b is not None else "–"),
    ]
    md = "| measure | A: approved | B: no action |\n|---|---|---|\n" + "\n".join(f"| {r[0]} | {r[1]} | {r[2]} |" for r in rows)
    (D / "summary_table.md").write_text(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
