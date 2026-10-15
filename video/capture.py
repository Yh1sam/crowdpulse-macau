"""Record real footage of the running web apps (dashboard, SketchFuture) for the pitch video.

Drives the installed Google Chrome in headless mode over the DevTools protocol, plays a scripted
list of steps (navigate, wait, click, scroll, type), records the page with Page.startScreencast and
turns the frames into a constant-frame-rate H.264 clip with ffmpeg. Nothing is mocked: the footage
is the real software showing real data from the running backend.

    .venv/bin/python video/capture.py video/shots/overview.json --out video/build/clips/overview.mp4

A shot file is JSON: {"url": "..." (a web URL, or "file:path" relative to the repo root), "viewport": [1280, 720], "scale": 1.5, "steps": [...]}, where each
step is one of {"wait": s}, {"click": css-selector}, {"click_text": text}, {"click_js": js returning an
element}, {"scroll": px}, {"scroll_to": css-selector}, {"eval": js}, {"navigate": url},
{"wait_for": css-selector} or {"wait_for_js": js expression}; waits poll for up to 180 s, so steps can
wait for things that appear at a run-dependent time (e.g. the Senado redirect card).
Frames are written to disk as they arrive; if a step fails, the footage recorded so far is still
encoded (as <out>.partial.mp4) and the error is reported.
A visible pointer is drawn by an overlay element so viewers can follow clicks; it is not part of
the app.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve_url(url: str) -> str:
    """'file:some/path' (no slashes after the colon) is a file relative to the repo root."""
    if url.startswith("file:") and not url.startswith("file:/"):
        return (ROOT / url[len("file:"):]).resolve().as_uri()
    return url

import websockets

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_PORT = 9333
FPS = 30

POINTER_JS = """
(() => {
  if (document.getElementById('__pitch_pointer')) return;
  const p = document.createElement('div');
  p.id = '__pitch_pointer';
  Object.assign(p.style, {position: 'fixed', left: '-40px', top: '-40px', width: '22px', height: '22px', borderRadius: '50%',
    background: 'rgba(255,255,255,0.85)', border: '2px solid rgba(20,20,20,0.9)', boxShadow: '0 0 0 6px rgba(255,255,255,0.25)',
    zIndex: 2147483647, pointerEvents: 'none', transition: 'left 0.6s ease-in-out, top 0.6s ease-in-out, transform 0.15s'});
  document.documentElement.appendChild(p);
})();
"""


class Page:
    def __init__(self, ws, frames_dir: Path):
        self.ws, self.next_id, self.pending, self.frames, self.frames_dir = ws, 0, {}, [], frames_dir

    async def pump(self):
        async for raw in self.ws:
            msg = json.loads(raw)
            if "id" in msg and msg["id"] in self.pending:
                self.pending.pop(msg["id"]).set_result(msg)
            elif msg.get("method") == "Page.screencastFrame":
                p = msg["params"]
                path = self.frames_dir / f"f{len(self.frames):05d}.jpg"
                path.write_bytes(base64.b64decode(p["data"]))
                self.frames.append((time.time(), path))  # arrival time: one clock for frames and the final hold
                await self.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]}, wait=False)

    async def send(self, method, params=None, wait=True):
        self.next_id += 1
        fut = asyncio.get_running_loop().create_future()
        if wait:
            self.pending[self.next_id] = fut
        await self.ws.send(json.dumps({"id": self.next_id, "method": method, "params": params or {}}))
        if wait:
            msg = await asyncio.wait_for(fut, 30)
            if "error" in msg:
                raise RuntimeError(f"{method}: {msg['error']}")
            return msg.get("result", {})

    async def eval(self, js):
        r = await self.send("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True})
        return r.get("result", {}).get("value")

    async def point_and_click(self, js_element):
        box = await self.eval(f"(() => {{ const e = {js_element}; if (!e) return null; e.scrollIntoView({{block: 'center'}}); const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }})()")
        if not box:
            raise RuntimeError(f"element not found: {js_element}")
        await self.eval(POINTER_JS)
        await self.eval(f"(() => {{ const p = document.getElementById('__pitch_pointer'); p.style.left = '{box[0] - 11}px'; p.style.top = '{box[1] - 11}px'; }})()")
        await asyncio.sleep(0.8)
        await self.eval("document.getElementById('__pitch_pointer').style.transform = 'scale(0.7)'")
        for kind in ("mousePressed", "mouseReleased"):
            await self.send("Input.dispatchMouseEvent", {"type": kind, "x": box[0], "y": box[1], "button": "left", "clickCount": 1})
        await asyncio.sleep(0.15)
        await self.eval("document.getElementById('__pitch_pointer').style.transform = 'scale(1)'")


async def wait_until(page: "Page", js: str, what: str, timeout: float = 180) -> None:
    deadline = time.time() + timeout
    while not await page.eval(js):
        if time.time() > deadline:
            raise RuntimeError(f"timed out waiting for {what}")
        await asyncio.sleep(0.5)


async def record(shot: dict, frames_dir: Path, frames: list, port: int) -> None:
    """Plays the shot; frames are appended to `frames` (and written to disk) as they arrive."""
    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
    page_target = next(t for t in targets if t["type"] == "page")
    async with websockets.connect(page_target["webSocketDebuggerUrl"], max_size=64 * 2**20) as ws:
        page = Page(ws, frames_dir)
        page.frames = frames
        pump = asyncio.create_task(page.pump())
        w, h = shot.get("viewport", [1280, 720])
        scale = shot.get("scale", 1.5)
        await page.send("Page.enable")
        await page.send("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": scale, "mobile": False})
        await page.send("Page.navigate", {"url": resolve_url(shot["url"])})
        await asyncio.sleep(shot.get("settle", 3))
        await page.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": int(w * scale), "maxHeight": int(h * scale), "everyNthFrame": 1})
        for step in shot["steps"]:
            (kind, arg), = step.items()
            if kind == "wait":
                await asyncio.sleep(arg)
            elif kind == "navigate":
                await page.send("Page.navigate", {"url": resolve_url(arg)})
            elif kind == "click":
                await page.point_and_click(f"document.querySelector({json.dumps(arg)})")
            elif kind == "click_text":
                await page.point_and_click(f"[...document.querySelectorAll('button, a, summary')].find(e => e.textContent.trim().includes({json.dumps(arg)}))")
            elif kind == "click_js":
                await page.point_and_click(f"({arg})")
            elif kind == "scroll":
                await page.eval(f"window.scrollBy({{top: {int(arg)}, behavior: 'smooth'}})")
            elif kind == "scroll_to":
                await page.eval(f"document.querySelector({json.dumps(arg)})?.scrollIntoView({{behavior: 'smooth', block: 'start'}})")
            elif kind == "wait_for":
                await wait_until(page, f"!!document.querySelector({json.dumps(arg)})", arg)
            elif kind == "wait_for_js":
                await wait_until(page, f"!!({arg})", arg)
            elif kind == "eval":
                await page.eval(arg)
            else:
                raise ValueError(f"unknown step {kind}")
        await asyncio.sleep(0.3)
        await page.send("Page.stopScreencast")
        pump.cancel()
        if frames:  # the screencast only sends frames on change: hold the last one until recording stopped
            frames.append((time.time(), frames[-1][1]))


def encode(frames: list[tuple[float, Path]], out: Path) -> None:
    """Constant frame rate: each screencast frame is held until the next one arrived."""
    if len(frames) < 2:
        raise RuntimeError("too few frames captured")
    concat = frames[0][1].parent / "concat.txt"
    lines = []
    for (t0, p), (t1, _) in zip(frames, frames[1:]):
        lines += [f"file '{p}'", f"duration {max(t1 - t0, 1 / FPS):.4f}"]
    lines += [f"file '{frames[-1][1]}'", f"duration {1 / FPS:.4f}", f"file '{frames[-1][1]}'"]
    concat.write_text("\n".join(lines) + "\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-vf", f"fps={FPS},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(out)], check=True)


def stop_chrome(chrome: subprocess.Popen) -> None:
    if chrome.poll() is None:
        chrome.terminate()
        try:
            chrome.wait(timeout=10)
        except subprocess.TimeoutExpired:
            chrome.kill()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("shot", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help="DevTools port; give overlapping captures different ports")
    args = ap.parse_args()
    shot = json.loads(args.shot.read_text())
    work = Path(tempfile.mkdtemp(prefix="pitch-capture-"))
    chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={args.port}", f"--user-data-dir={work / 'profile'}",
                               "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                               "--window-size=1920,1080", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{args.port}/json/version", timeout=1)
                break
            except OSError:
                time.sleep(0.2)
        frames_dir = work / "frames"
        frames_dir.mkdir()
        frames: list[tuple[float, Path]] = []
        try:
            asyncio.run(record(shot, frames_dir, frames, args.port))
        except Exception as e:  # keep and encode what was recorded, then report
            stop_chrome(chrome)
            partial = args.out.with_suffix(".partial.mp4")
            if len(frames) >= 2:
                encode(frames, partial)
            raise SystemExit(f"capture failed after {len(frames)} frames: {e}" + (f" (partial footage: {partial})" if len(frames) >= 2 else ""))
        stop_chrome(chrome)  # free the port and the CPU before encoding, so the next capture can start now
        print(f"recording stopped: {len(frames)} frames; encoding {args.out}", flush=True)
        encode(frames, args.out)
        dur = frames[-1][0] - frames[0][0]
        print(f"{args.out}: {len(frames)} screencast frames over {dur:.1f} s")
    finally:
        stop_chrome(chrome)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
