"""Orchestrate one complete simulation run against a live backend + dashboard.

    run_sim.py --tag A --out DIR [--shots full|minimal] [--end 14:36]

Timeline: polls the backend every ~3 real seconds and appends one row to DIR/<tag>_timeline.csv.
Screenshots: taken through headless Chrome (cdp.py) when simulated-time conditions are met.
Operator action: when a Senado Square redirect/inflow recommendation is pending, clicks APPROVE in the
Interventions page (a real UI click), exactly as an operator would. The dashboard only enables APPROVE once a name is
set under "Deciding as" (it is recorded in the audit log); the harness decides as the fictional OPERATOR_NAME by
writing the dashboard's localStorage key before the page loads.
"""
import argparse, csv, json, os, subprocess, sys, threading, time
from datetime import datetime, timedelta
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).parent))
import cdp  # noqa: E402

API = os.environ.get("CROWDPULSE_API", "http://localhost:8000")
WEB = os.environ.get("CROWDPULSE_WEB", "http://localhost:3100")
PHONE = os.environ.get("CROWDPULSE_PHONE_NODE", "node-a3cd4a")  # the iOS app's anonymous node id (Setup page)
OPERATOR_NAME = "demo-operator-1"  # fictional demo name shown in "Deciding as" and written to the audit log
OPERATOR_STORAGE_KEY = "crowdpulse.operatorName"  # dashboard/src/lib/operator.ts
client = httpx.Client(timeout=30)
lock = threading.Lock()
events: list[dict] = []


def get(path):
    return client.get(API + path).json()


def sim_local() -> str:
    t = datetime.fromisoformat(get("/health")["time"]) + timedelta(hours=8)
    return t.strftime("%H:%M")


def note(event_name, **kw):
    e = {"real_time": datetime.now().strftime("%H:%M:%S"), "sim_time": sim_local(), "event": event_name, **kw}
    with lock:
        events.append(e)
    print(json.dumps(e), flush=True)


def recorder(path: Path, stop: threading.Event):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["real_time", "sim_time", "zone", "density", "state", "reliability", "n_sensors", "disagreement",
                    "p5", "p10", "p15", "eff5", "eff10", "eff15", "review_any", "ood_any", "phone_status", "phone_zone", "phone_count", "phone_density", "pending_interventions", "refresh_ms", "true_density"])
        while not stop.is_set():
            try:
                h = get("/health")
                t = (datetime.fromisoformat(h["time"]) + timedelta(hours=8)).strftime("%H:%M:%S")
                try:
                    ph = get(f"/sensors/{PHONE}")
                except Exception:
                    ph = {}
                pend = [f"{i['zone_id']}:{i['kind']}" for i in get("/interventions?status=pending")]
                for zid in ("senado_square", "almeida_ribeiro"):
                    z = get(f"/zones/{zid}")
                    st = z.get("state") or {}
                    pr = {p["horizon_min"]: p for p in z.get("predictions", [])}
                    w.writerow([datetime.now().strftime("%H:%M:%S"), t, zid, round(st.get("density", float("nan")), 3), st.get("congestion_state"),
                                round(st.get("reliability", float("nan")), 3), st.get("n_sensors"), round(st.get("disagreement", float("nan")), 3),
                                *[pr.get(k, {}).get("predicted_class") for k in (5, 10, 15)],
                                *[round(pr.get(k, {}).get("effective_confidence", float("nan")), 3) for k in (5, 10, 15)],
                                any(p.get("human_review_required") for p in pr.values()), any(p.get("ood_flag") for p in pr.values()),
                                ph.get("status"), ph.get("zone_id"), ph.get("person_count"), round(ph.get("estimated_density", float("nan")), 3),
                                "|".join(pend), h["stats"].get("last_refresh_ms"),
                                ((h.get("live_sim") or {}).get("ground_truth") or {}).get(zid, {}).get("density")])
                f.flush()
            except Exception as e:  # keep recording through transient errors
                print("recorder error:", e, flush=True)
            stop.wait(3)


def wait_until(pred, label, timeout_s=600, every=1.0):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            if pred():
                return True
        except Exception:
            pass
        time.sleep(every)
    note("timeout", waiting_for=label)
    return False


def at_or_after(hhmm):
    return lambda: sim_local() >= hhmm


def senado_critical_forecast():
    z = get("/zones/senado_square")
    return any(p["predicted_class"] == "CRITICAL" for p in z["predictions"])


def senado_redirect_pending():
    return [i for i in get("/interventions?status=pending") if i["zone_id"] == "senado_square" and i["kind"] in ("redirect_flow", "reduce_inflow")]


def shot(ws_path_url, out: Path, wait=9, height=None):
    try:
        _shot(ws_path_url, out, wait, height)
    except Exception as e:  # a failed screenshot must not end the run
        note("screenshot_failed", file=out.name, error=str(e))


def _shot(ws_path_url, out: Path, wait=9, height=None):
    with cdp.connect(cdp.page_ws(), max_size=64 * 1024 * 1024) as ws:
        cdp.call(ws, "Page.enable"); cdp.call(ws, "Runtime.enable")
        cdp.call(ws, "Emulation.setDeviceMetricsOverride", width=1440, height=1000, deviceScaleFactor=1, mobile=False)
        cdp.call(ws, "Page.navigate", url=WEB + ws_path_url)
        time.sleep(wait)
        cdp.screenshot(ws, str(out), height)
        cdp.call(ws, "Page.navigate", url="about:blank")  # stop the live map rendering between shots (CPU)
    note("screenshot", file=out.name, page=ws_path_url)


def ui(js, wait_after=0.0):
    with cdp.connect(cdp.page_ws(), max_size=64 * 1024 * 1024) as ws:
        cdp.call(ws, "Runtime.enable")
        r = cdp.evaluate(ws, js)
    time.sleep(wait_after)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shots", default="full", choices=["full", "minimal"])
    ap.add_argument("--end", default="14:36")
    ap.add_argument("--no-approve", action="store_true", help="counterfactual: the operator never approves anything")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    P = lambda name: out / f"{a.tag}{name}.png"
    stop = threading.Event()
    rec = threading.Thread(target=recorder, args=(out / f"{a.tag}_timeline.csv", stop), daemon=True)
    rec.start()
    note("start", health=get("/health")["live_sim"]["scenario"])

    if a.shots == "full":
        shot("/", P("01_overview_start"))
        shot("/map", P("02_live_map"))
        shot("/reliability", P("03_reliability_phone_node"))
        shot("/zones/almeida_ribeiro", P("04_zone_almeida_with_phone"))

    wait_until(senado_critical_forecast, "Senado CRITICAL forecast")
    note("senado_critical_forecast", preds=[(p["horizon_min"], p["predicted_class"], round(p["effective_confidence"], 2), p["human_review_required"]) for p in get("/zones/senado_square")["predictions"]])
    shot("/zones/senado_square", P("05_zone_senado_critical_forecast"))
    if a.shots == "full":
        shot("/alerts", P("06_alerts"), height=1400)

    wait_until(lambda: bool(senado_redirect_pending()), "Senado redirect recommendation")
    iv = senado_redirect_pending()[0]
    note("senado_redirect_pending", intervention=iv["id"], iv_kind=iv["kind"], title=iv["title"], confidence=iv["confidence"])
    if a.no_approve:
        note("operator_takes_no_action", intervention=iv["id"])
        wait_until(at_or_after(a.end), f"sim {a.end}", timeout_s=900)
        stop.set(); rec.join(timeout=10)
        note("end", stats=get("/health")["stats"])
        (out / f"{a.tag}_events.json").write_text(json.dumps(events, indent=2))
        return
    # operator opens Interventions, looks at the evidence, approves: real UI clicks
    with cdp.connect(cdp.page_ws(), max_size=64 * 1024 * 1024) as ws:
        cdp.call(ws, "Page.enable"); cdp.call(ws, "Runtime.enable")
        cdp.call(ws, "Emulation.setDeviceMetricsOverride", width=1440, height=1000, deviceScaleFactor=1, mobile=False)
        # sign in before the page's scripts run, so APPROVE is enabled when the page renders
        cdp.call(ws, "Page.addScriptToEvaluateOnNewDocument",
                 source=f"try {{ localStorage.setItem({json.dumps(OPERATOR_STORAGE_KEY)}, {json.dumps(OPERATOR_NAME)}); }} catch (e) {{}}")
        cdp.call(ws, "Page.navigate", url=WEB + "/interventions")
        time.sleep(8)
        card_js = f"""(() => {{ const cards = [...document.querySelectorAll('main div.rounded-lg')].filter(d => d.innerText.includes('#{iv['id']} ·'));
            return cards.length ? cards[0] : null; }})()"""
        clicked = cdp.evaluate(ws, f"""(() => {{ const c = {card_js}; if (!c) return 'card not found';
            const b = [...c.querySelectorAll('button')].find(b => b.innerText.trim() === 'VIEW EVIDENCE'); if (!b) return 'no evidence button'; b.click(); return 'evidence opened'; }})()""")
        note("ui", action="view_evidence", result=clicked)
        time.sleep(3)
        cdp.screenshot(ws, str(P("07_intervention_evidence")))
        note("screenshot", file=P("07_intervention_evidence").name, page="/interventions")
        clicked = cdp.evaluate(ws, f"""(() => {{ const c = {card_js}; if (!c) return 'card not found';
            const b = [...c.querySelectorAll('button')].find(b => b.innerText.trim() === 'APPROVE'); if (!b) return 'no approve button';
            if (b.disabled) return 'approve disabled (no operator name set)'; b.click(); return 'approve clicked'; }})()""")
        note("ui", action="approve", result=clicked, intervention=iv["id"])
        time.sleep(5)
        cdp.screenshot(ws, str(P("08_after_approval_audit")))
        note("screenshot", file=P("08_after_approval_audit").name, page="/interventions")
        cdp.call(ws, "Page.navigate", url="about:blank")
    decided = get(f"/interventions/{iv['id']}")
    note("intervention_state", status=decided["status"], decided_by=decided["decided_by"], effect_applied=decided["effect_applied"],
         projected_after={h: v["predicted_class"] for h, v in (decided.get("projected_after") or {}).get("horizons", {}).items()})

    wait_until(at_or_after("14:28"), "sim 14:28", timeout_s=900)
    shot("/zones/senado_square", P("09_zone_senado_after_approval"))
    if a.shots == "full":
        shot("/explain", P("10_ai_explanation"), height=1800)
        shot("/evaluation", P("11_evaluation"), wait=10, height=2600)
        shot("/privacy", P("12_privacy"))
        shot("/reliability", P("13_reliability_end"))
    wait_until(at_or_after(a.end), f"sim {a.end}", timeout_s=900)
    stop.set(); rec.join(timeout=10)
    h = get("/health")
    note("end", stats=h["stats"])
    (out / f"{a.tag}_events.json").write_text(json.dumps(events, indent=2))


if __name__ == "__main__":
    main()
