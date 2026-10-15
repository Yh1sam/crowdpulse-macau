"""Record a real terminal session for the pitch video (shot S08) and draw it frame by frame.

The commands run in a real bash shell inside a pseudo-terminal. Every byte the shell prints is
saved with its time (an asciinema v2 cast), so the video shows exactly what the backend returned;
nothing is retyped. The renderer then replays the cast into 1920x1080 frames at 30 fps as a dark
terminal window in DejaVu Sans Mono (the free font bundled with matplotlib).

    .venv/bin/python video/record_terminal.py video/shots/S08_terminal.json --out video/build/clips/S08.mp4

The session file is JSON: {"cwd": dir (relative to the repo root, or absolute), "title": window title, "cols": 88, "rows": 14, "font_size": 30,
"duration": seconds, "setup": [hidden shell lines run before recording], "steps": [{"at": s,
"type": text, "speed": chars per second or 0 to paste at once}, ...]}. Each step's text is sent at
time `at` (seconds from the start of the recording) followed by Enter.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import tempfile
import termios
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
import matplotlib  # noqa: E402  (only for its bundled DejaVu Sans Mono)
MONO = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSansMono.ttf"
MONO_BOLD = MONO.with_name("DejaVuSansMono-Bold.ttf")
W, H, FPS = 1920, 1080, 30
BG, WINDOW, BAR, TEXT, DIM = (11, 18, 32), (16, 22, 34), (33, 41, 58), (230, 237, 247), (140, 152, 172)
CSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][A-Za-z0-9]|\x1b[=>]")


def record(session: dict) -> list[tuple[float, str]]:
    """Runs the session in a pseudo-terminal; returns [(time, output text)]."""
    env = {"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/tmp"), "TERM": "dumb", "LANG": "en_US.UTF-8",
           "PS1": "$ ", "PS2": "> ", "COLUMNS": str(session["cols"]), "LINES": str(session["rows"]), **session.get("env", {})}
    cwd = Path(session["cwd"])
    cwd = cwd if cwd.is_absolute() else ROOT / cwd   # relative to the repo root
    cwd.mkdir(parents=True, exist_ok=True)
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(cwd)
        os.execvpe("bash", ["bash", "--noprofile", "--norc", "-i"], env)
    # real window size, so wrapping matches the drawn terminal
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", session["rows"], session["cols"], 0, 0))
    events: list[tuple[float, str]] = []

    def drain(until: float, keep: bool, t0: float) -> None:
        while True:
            left = until - time.monotonic()
            r, _, _ = select.select([fd], [], [], max(0.0, min(left, 0.05)))
            if r:
                try:
                    data = os.read(fd, 65536).decode("utf-8", "replace")
                except OSError:
                    return
                if keep and data:
                    events.append((time.monotonic() - t0, data))
            elif left <= 0:
                return

    # no line editor: the terminal itself echoes each command exactly as sent (no sideways scrolling)
    for line in ["stty -echoctl", "set +o emacs +o vi", *session.get("setup", []), "clear"]:
        os.write(fd, (line + "\n").encode())
        drain(time.monotonic() + 0.4, False, 0)
    drain(time.monotonic() + 0.8, False, 0)
    t0 = time.monotonic()
    events.append((0.0, "$ "))
    for step in session["steps"]:
        drain(t0 + step["at"], True, t0)
        text, speed = step["type"], step.get("speed", 0)
        if speed:
            for ch in text:
                os.write(fd, ch.encode())
                drain(time.monotonic() + 1 / speed, True, t0)
        else:
            os.write(fd, text.encode())
        os.write(fd, b"\n")
    drain(t0 + session["duration"], True, t0)
    os.write(fd, b"exit\n")
    os.close(fd)
    os.waitpid(pid, 0)
    return events


class Screen:
    """A minimal terminal: printable text, CR, LF, backspace and wrapping; escape codes dropped."""

    def __init__(self, cols: int, rows: int):
        self.cols, self.rows, self.lines, self.x = cols, rows, [""], 0

    def feed(self, data: str) -> None:
        for ch in CSI.sub("", data):
            if ch == "\n":
                self.lines.append("")
                self.x = 0
            elif ch == "\r":
                self.x = 0
            elif ch == "\b":
                self.x = max(0, self.x - 1)
            elif ch == "\x07" or ord(ch) < 32:
                continue
            else:
                if self.x >= self.cols:
                    self.lines.append("")
                    self.x = 0
                line = self.lines[-1]
                self.lines[-1] = line[: self.x].ljust(self.x) + ch + line[self.x + 1:]
                self.x += 1

    def visible(self) -> list[str]:
        return self.lines[-self.rows:]


def render(events: list[tuple[float, str]], session: dict, out: Path) -> None:
    cols, rows, size = session["cols"], session["rows"], session.get("font_size", 30)
    f, fb = ImageFont.truetype(str(MONO), size), ImageFont.truetype(str(MONO_BOLD), 22)
    cw, lh = f.getlength("M"), int(size * 1.35)
    win_w, win_h = int(cw * cols + 80), int(lh * rows + 110)
    x0, y0 = (W - win_w) // 2, max(140, (H - win_h) // 2 - 40)
    base = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((x0, y0, x0 + win_w, y0 + win_h), 18, fill=WINDOW, outline=BAR, width=2)
    d.rounded_rectangle((x0, y0, x0 + win_w, y0 + 52), 18, fill=BAR)
    d.rectangle((x0, y0 + 34, x0 + win_w, y0 + 52), fill=BAR)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse((x0 + 22 + i * 30, y0 + 17, x0 + 40 + i * 30, y0 + 35), fill=c)
    title = session.get("title", "bash")
    d.text((x0 + win_w / 2, y0 + 26), title, font=fb, fill=DIM, anchor="mm")
    screen, idx = Screen(cols, rows), 0
    tmp = Path(tempfile.mkdtemp(prefix="term-"))
    try:
        n = int(round(session["duration"] * FPS))
        for i in range(n):
            t = i / FPS
            while idx < len(events) and events[idx][0] <= t:
                screen.feed(events[idx][1])
                idx += 1
            img = base.copy()
            dr = ImageDraw.Draw(img)
            vis = screen.visible()
            for r, line in enumerate(vis):
                dr.text((x0 + 40, y0 + 76 + r * lh), line, font=f, fill=TEXT)
            if int(t * 2) % 2 == 0:  # blinking block cursor
                cx, cy = x0 + 40 + screen.x * cw, y0 + 76 + (len(vis) - 1) * lh
                dr.rectangle((cx, cy + 2, cx + cw - 2, cy + size + 4), fill=TEXT)
            img.save(tmp / f"f_{i:05d}.png", compress_level=1)
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f_%05d.png"),
                        "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    session = json.loads(args.session.read_text())
    events = record(session)
    cast = args.out.with_suffix(".cast")
    cast.parent.mkdir(parents=True, exist_ok=True)
    with cast.open("w") as fh:  # asciinema v2: the raw session, kept next to the clip as the record
        fh.write(json.dumps({"version": 2, "width": session["cols"], "height": session["rows"], "title": session.get("title", "")}) + "\n")
        for t, data in events:
            fh.write(json.dumps([round(t, 4), "o", data]) + "\n")
    render(events, session, args.out)
    print(f"{args.out}: {len(events)} output events; raw session {cast}")


if __name__ == "__main__":
    main()
