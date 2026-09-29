"""Tiny Chrome DevTools Protocol driver for evidence screenshots (headless, real time, no virtual clock).

    cdp.py start                         launch headless Chrome on port 9333
    cdp.py shot URL OUT.png [WAIT] [H]   navigate, wait WAIT s (default 6), save a screenshot (height H, default full page up to 2600)
    cdp.py grab OUT.png [H]              screenshot the current page without navigating
    cdp.py eval JS                       evaluate JS in the current page, print the JSON result
    cdp.py stop
"""
import base64, json, subprocess, sys, tempfile, time, itertools
from pathlib import Path
import httpx
from websockets.sync.client import connect

PORT = 9333
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE = str(Path(tempfile.gettempdir()) / "crowdpulse-headless-chrome")
_ids = itertools.count(1)


def start():
    subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={PROFILE}", "--use-angle=swiftshader",
                      "--enable-unsafe-swiftshader", "--hide-scrollbars", "--no-first-run", "--window-size=1440,1000", "about:blank"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        try:
            httpx.get(f"http://localhost:{PORT}/json/version", timeout=1); print("chrome up"); return
        except Exception:
            time.sleep(0.2)
    sys.exit("chrome did not start")


def page_ws():
    targets = [t for t in httpx.get(f"http://localhost:{PORT}/json", timeout=5).json() if t["type"] == "page"]
    return targets[0]["webSocketDebuggerUrl"]


def call(ws, method, **params):
    i = next(_ids)
    ws.send(json.dumps({"id": i, "method": method, "params": params}))
    while True:
        m = json.loads(ws.recv(timeout=60))
        if m.get("id") == i:
            if "error" in m:
                raise RuntimeError(f"{method}: {m['error']}")
            return m.get("result", {})


def evaluate(ws, js):
    r = call(ws, "Runtime.evaluate", expression=js, awaitPromise=True, returnByValue=True)
    return r.get("result", {}).get("value")


def screenshot(ws, out, height=None):
    call(ws, "Emulation.setDeviceMetricsOverride", width=1440, height=1000, deviceScaleFactor=1, mobile=False)
    time.sleep(0.3)
    h = height or min(2600, int(evaluate(ws, "Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)") or 1000))
    call(ws, "Emulation.setDeviceMetricsOverride", width=1440, height=h, deviceScaleFactor=1, mobile=False)
    time.sleep(1.2)  # let the map and charts re-layout at the new size
    data = call(ws, "Page.captureScreenshot", format="png")["data"]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_bytes(base64.b64decode(data))
    call(ws, "Emulation.setDeviceMetricsOverride", width=1440, height=1000, deviceScaleFactor=1, mobile=False)
    print(f"saved {out} (1440x{h})")


def main():
    cmd = sys.argv[1]
    if cmd == "start":
        return start()
    if cmd == "stop":
        subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"]); return
    with connect(page_ws(), max_size=64 * 1024 * 1024) as ws:
        call(ws, "Page.enable"); call(ws, "Runtime.enable")
        if cmd == "shot":
            url, out = sys.argv[2], sys.argv[3]
            wait = float(sys.argv[4]) if len(sys.argv) > 4 else 6
            height = int(sys.argv[5]) if len(sys.argv) > 5 else None
            call(ws, "Emulation.setDeviceMetricsOverride", width=1440, height=1000, deviceScaleFactor=1, mobile=False)
            call(ws, "Page.navigate", url=url)
            time.sleep(wait)
            screenshot(ws, out, height)
        elif cmd == "grab":
            screenshot(ws, sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None)
        elif cmd == "eval":
            print(json.dumps(evaluate(ws, sys.argv[2])))


if __name__ == "__main__":
    main()
