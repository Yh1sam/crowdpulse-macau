"""Build the approved 18-scene product-film reconstruction.

Usage: .venv/bin/python video/pitch_v2.py --stills
       .venv/bin/python video/pitch_v2.py --render --workers 3
       .venv/bin/python video/pitch_v2.py --assemble

Old recordings remain immutable inputs. All derived media lives in video/build/v2.
The versioned story and recording documents are generated from v2_story.py.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import re
import subprocess
import sys
import wave
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "video"), str(ROOT / "video" / "mg")]
from v2_story import PEOPLE, RUNTIME_S, export, scenes
from style import font, text_size, wrap, wheelchair_icon, staff_icon
from assemble import caption_chunks, caption_bounds, pauses

W, H, FPS = 1920, 1080, 30
BUILD = ROOT / "video" / "build" / "v2"
CLIPS = ROOT / "video" / "build" / "clips"
BG, PANEL, LINE = (8, 14, 25), (17, 27, 43), (43, 60, 79)
WHITE, MUTED, CYAN = (241, 246, 252), (157, 174, 194), (48, 211, 221)
RED, AMBER, PURPLE = (239, 91, 103), (246, 187, 78), (167, 135, 235)
COLOUR = ["-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
          "-color_primaries", "bt709", "-color_trc", "bt709"]
H264_COLOUR = "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0"
REVIEW_NOTE = "Guide audio"
SHOTS = {s["id"]: s for s in scenes()}


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "default=nw=1:nk=1", str(path)], text=True))


def ease(x):
    x = max(0.0, min(1.0, float(x)))
    return x * x * (3 - 2 * x)


def phase(t, start, span=.65):
    return ease((t - start) / span)


def mix(a, b, k):
    if isinstance(a, tuple):
        return tuple(mix(x, y, k) for x, y in zip(a, b))
    return a + (b - a) * k


@lru_cache(maxsize=2048)
def lettering(text, size, weight, colour, max_width=0):
    lines = wrap(text, size, weight, max_width) if max_width else text.split("\n")
    widths = [text_size(line, size, weight)[0] for line in lines]
    tile = Image.new("RGBA", (max(widths or [1]) + 12, int(size * 1.24 * len(lines)) + 12))
    d = ImageDraw.Draw(tile)
    for i, line in enumerate(lines):
        d.text((5, 2 + i * size * 1.24), line, font=font(size, weight), fill=(*colour, 255), anchor="lt")
    return tile


def paste(img, tile, x, y, alpha=1.0):
    if alpha <= 0:
        return
    if alpha < .999:
        tile = tile.copy()
        tile.putalpha(tile.getchannel("A").point(lambda a: int(a * max(0, alpha))))
    img.paste(tile, (round(x), round(y)), tile)


def dissolve(img, previous, following, amount):
    """Blend complete layouts; never move a crop through unrelated UI panels."""
    img.alpha_composite(Image.blend(previous, following, max(0, min(1, amount))))


def text(img, x, y, value, size=36, weight=500, colour=WHITE, alpha=1, width=0, centre=False):
    tile = lettering(str(value), size, weight, colour, width)
    paste(img, tile, x - tile.width / 2 if centre else x, y, alpha)
    return tile.height


def roundbox(img, box, fill=PANEL, radius=24, outline=None, stroke=1):
    ImageDraw.Draw(img).rounded_rectangle(tuple(round(x) for x in box), radius, fill=fill,
                                         outline=outline, width=stroke)


@lru_cache(maxsize=1)
def backdrop():
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx - 1230) / 780) ** 2 + ((yy - 420) / 610) ** 2))
    arr = np.zeros((H, W, 3), np.uint8)
    for i, (base, extra) in enumerate(zip(BG, (3, 11, 15))):
        arr[..., i] = base + glow * extra
    return Image.fromarray(arr).convert("RGBA")


def pill(img, value, x, y, colour=CYAN, size=20):
    width = text_size(value, size, 600)[0] + 36
    roundbox(img, (x, y, x + width, y + size + 24), fill=tuple(int(c * .14 + b * .86) for c, b in zip(colour, BG)),
             radius=20, outline=tuple(int(c * .45) for c in colour))
    text(img, x + 16, y + 9, value, size, 600, colour)


def header(img, title, subtitle="", t=10):
    a = phase(t, .05, .55)
    text(img, 90, 55 + 12 * (1 - a), title, 46, 650, alpha=a)
    if subtitle:
        text(img, 92, 119, subtitle, 23, 450, MUTED, a)


def footer(img, value):
    text(img, 82, 1035, value, 17, 450, MUTED)


@lru_cache(maxsize=16)
def legacy(name):
    return importlib.import_module(name)


@lru_cache(maxsize=32)
def snapshot(name, at):
    path = BUILD / "assets" / f"{name}_{at:g}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", str(CLIPS / f"{name}.mp4"),
             "-frames:v", "1", str(path)], stdout=subprocess.DEVNULL)
    return Image.open(path).convert("RGBA")


@lru_cache(maxsize=64)
def mask_for(size, radius):
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return mask


def image_panel(img, source, box, crop=None, radius=24, contain=False):
    x0, y0, x1, y1 = map(round, box)
    width, height = max(2, x1 - x0), max(2, y1 - y0)
    if crop:
        # Recording crop coordinates use a common 1920x1080 reference.
        sx, sy = source.width / 1920, source.height / 1080
        source = source.crop(tuple(round(v * (sx if i % 2 == 0 else sy)) for i, v in enumerate(crop)))
    if contain:
        source = ImageOps.contain(source, (width, height), Image.Resampling.LANCZOS)
        tile = Image.new("RGBA", (width, height), (15, 20, 28, 255))
        tile.paste(source, ((width - source.width) // 2, (height - source.height) // 2))
    else:
        tile = ImageOps.fit(source, (width, height), method=Image.Resampling.LANCZOS)
    tile.putalpha(mask_for((width, height), radius))
    paste(img, tile, x0, y0)


def window(img, source, box, title, crop=None):
    x0, y0, x1, y1 = box
    roundbox(img, (x0 - 10, y0 - 42, x1 + 10, y1 + 10), (40, 49, 61), 27, outline=(74, 86, 101))
    roundbox(img, (x0 - 6, y0 - 38, x1 + 6, y1 + 6), (14, 19, 29), 24)
    d = ImageDraw.Draw(img)
    for i, c in enumerate(((220, 96, 100), (223, 180, 99), (101, 176, 135))):
        x = x0 + 22 + i * 23
        d.ellipse((x - 5, y0 - 24, x + 5, y0 - 14), fill=c)
    text(img, x0 + 110, y0 - 31, title, 18, 500, MUTED)
    image_panel(img, source, (x0, y0, x1, y1), crop, 14, contain=True)


def phone(img, source, x, y, height):
    width = height * 1206 / 2622
    roundbox(img, (x - 12, y - 12, x + width + 12, y + height + 12), (67, 78, 91), 51)
    roundbox(img, (x - 7, y - 7, x + width + 7, y + height + 7), (4, 7, 12), 47)
    image_panel(img, source, (x, y, x + width, y + height), radius=40)


class Frames:
    """Sequential decoder with bounded memory; forwards seeks do not store whole recordings."""
    def __init__(self, name, width=1600):
        self.path = CLIPS / f"{name}.mp4"
        meta = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
                           "-show_entries", "stream=width,height", "-of", "json", str(self.path)], text=True))["streams"][0]
        self.width = width
        self.duration = duration(self.path)
        self.height = round(meta["height"] * width / meta["width"] / 2) * 2
        self.proc, self.index, self.last = None, -1, None

    def close(self):
        if self.proc:
            self.proc.stdout.close()
            self.proc.terminate()
            self.proc.wait()
            self.proc = None

    def get(self, at):
        # Deliberately hold the final recorded frame when a source excerpt ends.
        target = min(max(0, round(at * FPS)), max(0, int(self.duration * FPS) - 2))
        if self.proc is None or target < self.index or target - self.index > FPS * 2:
            self.close()
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "1", "-ss", str(target / FPS),
                 "-i", str(self.path), "-vf", f"fps={FPS},scale={self.width}:{self.height}",
                 "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.index = target - 1
        while self.index < target:
            data = self.proc.stdout.read(self.width * self.height * 3)
            if len(data) != self.width * self.height * 3:
                if self.last is None:
                    raise RuntimeError(f"Unreadable recording: {self.path}")
                break
            self.last = Image.frombytes("RGB", (self.width, self.height), data).convert("RGBA")
            self.index += 1
        return self.last


def sentences(shot):
    result = re.split(r"(?<=[.!?])\s+", shot["narration"].strip())
    if shot["id"] == "N10":
        result = result[:2] + [part.strip() + ("," if i < 2 else "")
                                for i, part in enumerate(result[2].split(","))]
    return [s for s in result if s]


def make_guides():
    guide = BUILD / "guide"
    guide.mkdir(parents=True, exist_ok=True)
    report = {}
    for shot in scenes():
        sid, slot = shot["id"], shot["end_s"] - shot["start_s"]
        if not shot["narration"]:
            report[sid] = dict(cues=[], captions=[], speech_s=0, slot_s=slot)
            continue
        sounds, cues, captions = [], [], []
        for i, line in enumerate(sentences(shot)):
            aiff, wav = guide / f"{sid}_{i}.aiff", guide / f"{sid}_{i}.wav"
            spoken = line.replace("Senado", "Se-nah-doo").replace("face-ID", "face I D")
            tempo = .94 if sid == "N15" else .90
            signature = hashlib.sha256(f"Daniel|155|{tempo}|{spoken}".encode()).hexdigest()
            stamp = wav.with_suffix(".sha256")
            if not wav.exists() or not stamp.exists() or stamp.read_text() != signature:
                run(["say", "-v", "Daniel", "-r", "155", "-o", str(aiff), spoken])
                run(["ffmpeg", "-v", "error", "-y", "-i", str(aiff), "-af", f"atempo={tempo}",
                     "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
                aiff.unlink()
                stamp.write_text(signature)
            with wave.open(str(wav)) as f:
                sounds.append((line, wav, f.readframes(f.getnframes())))
        speech = sum(len(s[2]) / 96000 for s in sounds)
        gap = .35 if len(sounds) > 1 else 0
        if speech + gap * (len(sounds) - 1) + .50 > slot:
            raise RuntimeError(f"{sid}: guide needs retiming ({speech:.2f}s plus pauses in {slot}s)")
        timeline = bytearray(b"\0" * round(.35 * 96000))
        for i, (line, wav, pcm) in enumerate(sounds):
            start = len(timeline) / 96000
            length = len(pcm) / 96000
            cues.append(dict(text=line, start=start, end=start + length))
            chunks = caption_chunks(line)
            bounds = caption_bounds(chunks, length, pauses(wav))
            for j, chunk in enumerate(chunks):
                captions.append(dict(text=chunk, start=start + bounds[j],
                                     end=start + bounds[j + 1] + (.18 if j == len(chunks) - 1 else 0)))
            timeline.extend(pcm)
            if i != len(sounds) - 1:
                timeline.extend(b"\0" * round(gap * 96000))
        end = len(timeline) / 96000
        timeline.extend(b"\0" * max(0, round((slot - end) * 96000)))
        with wave.open(str(guide / f"{sid}.wav"), "wb") as out:
            out.setnchannels(1); out.setsampwidth(2); out.setframerate(48000)
            out.writeframes(timeline)
        report[sid] = dict(cues=cues, captions=captions, speech_s=round(speech, 3),
                           voice_end_s=round(end, 3), slot_s=slot)
        print(f"{sid}: guide speech {speech:.2f}s, ends {end:.2f}s / {slot}s", flush=True)
    (BUILD / "guide.json").write_text(json.dumps(report, indent=2) + "\n")


def cue(report, index, fallback=0):
    values = report["cues"]
    return values[min(index, len(values) - 1)]["start"] if values else fallback


def group(img, t, mode):
    top = 210 if mode == "intro" else 160
    for i, (key, person) in enumerate(PEOPLE.items()):
        x, a = 130 + i * 425, phase(t, i * .10, .7)
        tile = Image.new("RGBA", (385, 430))
        roundbox(tile, (0, 0, 384, 429), PANEL, 28, LINE)
        d = ImageDraw.Draw(tile)
        d.ellipse((143, 55, 242, 154), fill=(72, 93, 117))
        d.rounded_rectangle((91, 166, 294, 310), 70, fill=(44, 63, 87))
        text(tile, 192, 330, person["name"], 29, 600, centre=True)
        text(tile, 192, 381, person["role"], 18, 450, MUTED, centre=True)
        paste(img, tile, x, top + 18 * (1 - a), a)
    if mode == "intro":
        text(img, W / 2, 70, "CrowdPulse Macau", 80, 650, alpha=phase(t, .1), centre=True)
        text(img, W / 2, 700, "Ordinary phones. Thoughtful decisions.", 34, 450, MUTED, centre=True)
    elif mode == "question":
        text(img, W / 2, 650, SHOTS["N04"]["narration"], 52, 600, width=1530, centre=True)
    else:
        text(img, W / 2, 700, "The AI recommends. A person decides.", 64, 650, centre=True)
    text(img, W / 2, 1010, "Camera placeholders · replace with the four-person take", 19, 450, MUTED, centre=True)


def big_words(img, lines, y=300, size=76, colour=WHITE, t=10, delay=0):
    for i, line in enumerate(lines):
        a = phase(t, delay + i * .14)
        text(img, 120, y + i * size * 1.15 + 22 * (1 - a), line, size, 650, colour, a)


def dot_grid(img, x, y, amount=1):
    d = ImageDraw.Draw(img)
    for i in range(40):
        cx, cy = x + i % 10 * 47, y + i // 10 * 49
        colour = PURPLE if i < 24 else (86, 104, 126)
        radius = 14 * max(.01, amount)
        d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=colour)


class Scene:
    def __init__(self, sid):
        self.sid, self.shot = sid, SHOTS[sid]
        self.report = json.loads((BUILD / "guide.json").read_text())[sid]
        self.readers = {}
        self.entry_frame = None

    def footage(self, name, at, width=1600):
        if name not in self.readers:
            self.readers[name] = Frames(name, width)
        return self.readers[name].get(at)

    def close(self):
        for reader in self.readers.values():
            reader.close()

    def finish(self, img, t):
        person = PEOPLE.get(self.shot["speaker"])
        if person and t < 4.8:
            a = phase(t, .1, .45) * (1 - phase(t, 4.2, .6))
            tile = Image.new("RGBA", (630, 68))
            roundbox(tile, (0, 0, 625, 67), (15, 25, 40), 18, LINE)
            text(tile, 18, 9, person["name"], 24, 650)
            text(tile, 18, 40, person["role"], 17, 450, MUTED)
            text(tile, 602, 22, person["letters"], 21, 650, CYAN, centre=True)
            paste(img, tile, 80, 850, a)
        for item in self.report["captions"]:
            if item["start"] <= t < item["end"]:
                lines = wrap(item["text"], 33, 500, 1480)
                height = 40 * len(lines) + 22
                width = max(text_size(s, 33, 500)[0] for s in lines) + 48
                x, y = (W - width) / 2, 1000 - height
                roundbox(img, (x, y, x + width, y + height), (3, 8, 14), 15)
                for j, line in enumerate(lines):
                    text(img, W / 2, y + 10 + j * 40, line, 33, 500, centre=True)
                break
        text(img, 1750, 1036, REVIEW_NOTE, 17, 450, MUTED)
        return img.convert("RGB")

    def content(self, t):
        img = backdrop().copy()
        getattr(self, f"draw_{self.sid}")(img, t)
        return img

    def draw(self, t):
        img = self.content(t)
        if self.sid != "N01" and t < .3:
            if self.entry_frame is None:
                previous = Scene(f"N{int(self.sid[1:]) - 1:02d}")
                slot = previous.shot["end_s"] - previous.shot["start_s"]
                self.entry_frame = previous.content(slot - 1 / FPS)
                previous.close()
            img = Image.blend(self.entry_frame, img, phase(t, 0, .3))
        return self.finish(img, t)

    def draw_N01(self, img, t):
        group(img, t, "intro")

    def draw_N02(self, img, t):
        hook = legacy("S01")
        eye_start, return_start = cue(self.report, 2), cue(self.report, 3)
        if t < eye_start:
            source_t = .3 + 3.9 * ease(t / max(1, eye_start))
            frame = hook.map_frame(source_t)
        elif t < return_start:
            frame = hook.eye_frame(5.3 + .6 * ease((t - eye_start) / max(1, return_start - eye_start)))
            if t < eye_start + .6:
                frame = Image.blend(hook.map_frame(4.2), frame, phase(t, eye_start, .6))
        else:
            frame = hook.map_frame(8.3)
            if t < return_start + .6:
                frame = Image.blend(hook.eye_frame(5.9), frame, phase(t, return_start, .6))
        img.alpha_composite(frame)
        pill(img, "ILLUSTRATION", 1590, 50, MUTED)

    def draw_N03(self, img, t):
        header(img, "Decisions affect different people", "Macau · Golden Week 2026", t)
        q = cue(self.report, 1)
        if q <= t < q + 2.5:
            text(img, W / 2, 390, "Why do these decisions matter?", 78, 650, centre=True)
        else:
            d = ImageDraw.Draw(img)
            for i, label in enumerate(("Event staff", "Visitors", "Mobility needs")):
                x = 130 + i * 575
                roundbox(img, (x, 245, x + 510, 500), PANEL, 28, LINE)
                if i == 2:
                    wheelchair_icon(d, x + 255, 335, 1.6, colour=PURPLE, width=5)
                else:
                    staff_icon(d, x + 255, 335, 1.6)
                text(img, x + 255, 430, label, 36, 550, centre=True)
        if t >= cue(self.report, 3) - .3:
            for i, day in enumerate(("2 Oct", "3 Oct", "4 Oct")):
                x = 560 + i * 285
                roundbox(img, (x, 620, x + 245, 745), PANEL, 24, LINE)
                text(img, x + 122, 658, day, 40, 600, centre=True)
            text(img, W / 2, 785, "Brief crowd controls at the Ruins", 29, 450, MUTED, centre=True)
        footer(img, "Source: Public Security Police Force · 8 Oct 2026")
        if q <= t < q + .3:
            previous = backdrop().copy()
            self.draw_N03(previous, q - 1 / FPS)
            dissolve(img, previous, img.copy(), phase(t, q, .3))
        elif q + 2.5 <= t < q + 2.8:
            previous = backdrop().copy()
            self.draw_N03(previous, q + 2.5 - 1 / FPS)
            dissolve(img, previous, img.copy(), phase(t, q + 2.5, .3))

    def draw_N04(self, img, t):
        group(img, t, "question")

    def draw_N05(self, img, t):
        d = ImageDraw.Draw(img)
        points = [(240 + i * 140, 610 + math.sin(i * .65 + t * .9) * 65) for i in range(11)]
        d.line(points, fill=(30, 83, 105), width=4)
        for i, (x, y) in enumerate(points):
            r = 7 + 4 * (.5 + .5 * math.sin(t * 1.2 - i * .3))
            d.ellipse((x - r, y - r, x + r, y + r), fill=CYAN)
        text(img, W / 2, 310, "CrowdPulse", 135, 650, alpha=phase(t, 0, .65), centre=True)
        text(img, W / 2, 495, "The changing rhythm of crowds", 37, 450, MUTED, centre=True)

    def draw_N06(self, img, t):
        reveal = cue(self.report, 1)
        existing = backdrop().copy()
        header(existing, "Building on existing work", "Public information · Macau", t)
        big_words(existing, ["Crowd warning", "already exists."], 280, 84, t=t)
        text(existing, 125, 535, "Public Security Police Force", 34, 450, MUTED)
        footer(existing, "Source: Legislative Assembly reply · 28 Jan 2026")
        if t < reveal:
            img.alpha_composite(existing)
            return
        a = phase(t, reveal, 1.0)
        product = backdrop().copy()
        header(product, "A temporary sensing kit", "For event staff · proposed support", t)
        p = snapshot("S02_sim_masked", 0)
        screen = snapshot("C2a", 119)
        zoom = phase(t, 14.4, 3.2)
        box = (540, 260, 1710, 795)
        composition = Image.new("RGBA", (W, H))
        window(composition, screen, box, "CrowdPulse dashboard", crop=(280, 65, 1910, 810))
        staff_icon(ImageDraw.Draw(composition), 1795, 750, 1.7)
        text(composition, 260, 835, "Phone", 28, 550, MUTED, centre=True)
        text(composition, 1125, 835, "Dashboard + staff review", 28, 550, MUTED, centre=True)
        paste(product, composition, 0, 0, 1 - zoom)
        phone(product, p, mix(130, 785, zoom), mix(205, 168, zoom), mix(600, 704, zoom))
        pill(product, "NO PARTNER YET", 1470, 56, AMBER)
        dissolve(img, existing, product, a)

    def phone_readout(self, img, frame, amount=1):
        """A crop expands into the free space beside its source, without crossing the device."""
        tile = frame.crop((0, int(frame.height * .414), frame.width, int(frame.height * .658)))
        box = mix((1090, 492, 1200, 545), (120, 501, 830, 838), amount)
        x0, y0, x1, y1 = box
        layer = Image.new("RGBA", (W, H))
        roundbox(layer, (x0 - 8, y0 - 8, x1 + 8, y1 + 8), (53, 66, 83), 26)
        image_panel(layer, tile, box, radius=20, contain=True)
        paste(img, layer, 0, 0, amount)

    def draw_N07(self, img, t):
        header(img, "The crowd. In numbers.", "Working prototype · iPhone Simulator · Toronto test clip", t)
        frame = self.footage("S02_sim_masked", t, 600)
        k = phase(t, 4.0, 1.2)
        phone(img, frame, mix(785, 1220, k), 168, 704)
        if k > 0:
            big_words(img, ["On-device", "counting."], 245, 76, t=t, delay=4.3)
            self.phone_readout(img, frame, phase(t, 6.3, 1.1))
        footer(img, "Recorded excerpt · final readout held · Toronto: Raysonho / Wikimedia Commons / CC0 · faces pixelated")

    def draw_N08(self, img, t):
        switch = cue(self.report, 2)
        feed = backdrop().copy()
        header(feed, "From phone to dashboard", "Numerical test feed · Almeida Ribeiro", t)
        p = self.footage("S02_sim_masked", 7.05, 600)
        phone(feed, p, 1220, 168, 704)
        self.phone_readout(feed, p)
        big_words(feed, ["Numbers received."], 265, 65, t=t)
        if t >= cue(self.report, 1):
            text(feed, 125, 385, "Test-feed zone: Almeida Ribeiro", 31, 500, CYAN,
                 phase(t, cue(self.report, 1), .45))
        footer(feed, "Recorded phone readout · held for explanation")
        if t < switch:
            img.alpha_composite(feed)
            return

        dashboard = backdrop().copy()
        header(dashboard, "Inspect the forecast", "Recorded views · simulated Senado scenario", t)
        box = (130, 245, 1790, 830)
        forecast_start = cue(self.report, 3) - .55
        reasons_start = cue(self.report, 3) + 3.25
        if t < forecast_start:
            frame = self.footage("C2a", 100.4 + min(2.6, t - switch))
            crop = (280, 60, 1920, 1040)
            window(dashboard, frame, box, "SIMULATED MACAU CROWD · LIVE-MAP RECORDING", crop)
        else:
            forecast = backdrop().copy()
            header(forecast, "Inspect the forecast", "Recorded views · simulated Senado scenario", t)
            # A labelled recorded detail keeps all magnified readings from one actual frame.
            frame = snapshot("C2a", 119)
            crop = mix((280, 65, 1910, 1070), (300, 785, 1100, 1067),
                       phase(t, forecast_start, 1.0))
            window(forecast, frame, box, "RECORDED FORECAST DETAIL", crop)
            if t < reasons_start:
                dashboard = forecast
                if t < forecast_start + .5:
                    previous = backdrop().copy()
                    header(previous, "Inspect the forecast", "Recorded views · simulated Senado scenario", t)
                    window(previous, snapshot("C2a", 103), box,
                           "SIMULATED MACAU CROWD · LIVE-MAP RECORDING", (280, 60, 1920, 1040))
                    dissolve(dashboard, previous, forecast, phase(t, forecast_start, .5))
            else:
                reasons = backdrop().copy()
                header(reasons, "See the reasons", "Recorded explanation · simulated Senado scenario", t)
                window(reasons, snapshot("C2a", 104.3), box, "RECORDED EXPLANATION DETAIL",
                       (1180, 663, 1915, 1000))
                dissolve(dashboard, forecast, reasons, phase(t, reasons_start, .6))
        footer(dashboard, "Map © OpenStreetMap contributors · recorded details from separate moments of the simulated scenario")
        dissolve(img, feed, dashboard, phase(t, switch, .6))

    def approval_view(self, t, stage):
        view = backdrop().copy()
        header(view, "Review before acting", "Working software · simulated crowd · scripted click", t)
        start = cue(self.report, 1)
        if stage == 0:
            at, crop = 111.8 + min(t, start) * .4, (300, 70, 1880, 940)
        elif stage == 1:
            at = min(127.5, 125.5 + max(0, t - start) * .5)
            crop = (335, 100, 1880, 900)
        elif stage == 2:
            at, crop = 137 + max(0, t - start - 4) * .35, (322, 350, 1880, 780)
        else:
            window(view, snapshot("C2b2", 116.5), (130, 230, 1790, 780),
                   "RECORDED NOTICE EXAMPLE", (335, 520, 1880, 745))
            for i, label in enumerate(("Chinese", "English", "Portuguese")):
                pill(view, label, 420 + i * 410, 825, CYAN)
            return view
        window(view, self.footage("C2b2", at), (130, 230, 1790, 835),
               "STAFF APPROVAL WORKFLOW" if stage < 2 else "RECORDED DECISION · AUDIT LOG", crop)
        return view

    def draw_N09(self, img, t):
        starts = [0, cue(self.report, 1), cue(self.report, 1) + 4, cue(self.report, 2)]
        stage = sum(t >= point for point in starts[1:])
        current = self.approval_view(t, stage)
        if stage and t < starts[stage] + .45:
            previous = self.approval_view(starts[stage] - 1 / FPS, stage - 1)
            dissolve(img, previous, current, phase(t, starts[stage], .45))
        else:
            img.alpha_composite(current)
        footer(img, "Scripted click · demo-operator-1 is a fictional, self-declared demonstration name")

    def draw_N10(self, img, t):
        header(img, "Privacy by design", "Numerical observations · no image uploads", t)
        terminal = cue(self.report, 2)
        local = img.copy()
        big_words(local, ["Process locally.", "Send numbers."], 300, 87, t=t)
        pill(local, "ON THE DEVICE", 125, 580)
        if t < terminal:
            img.alpha_composite(local)
            return
        n = 0 if t < cue(self.report, 3) else 1 if t < cue(self.report, 4) else 2
        frame = snapshot("S08", (2.5, 4.9, 7.35)[n])
        window(img, frame, (130, 230, 1790, 820), "RECORDED SERVER TEST", (60, 170, 1860, 775))
        label, colour = (("202 · accepted", CYAN), ("422 · rejected", AMBER), ("403 · image refused", RED))[n]
        pill(img, label, 1370, 58, colour, 23)
        if t < terminal + .45:
            current = img.copy()
            dissolve(img, local, current, phase(t, terminal, .45))

    def draw_N11(self, img, t):
        header(img, "Test the counts", "Real camera benchmark · held-out frames", t)
        if t < cue(self.report, 1):
            chart = Image.open(ROOT / "experiments/results/mall/mall_count_scatter.png").convert("RGBA")
            window(img, chart, (650, 230, 1690, 825), "ONE CAMERA · UNDER-COUNT", None)
            text(img, 130, 350, "Counting was\nharder than expected.", 55, 600, width=440)
        else:
            metrics = json.loads((ROOT / "experiments/results/uncertainty/metrics.json").read_text())["mall"]
            error = metrics["detectors"]["yolo11n"]["calibrated_20"]["mae_held_out"]
            guess = metrics["detector_free"]["mean_of_20_calibration_frames"]["mae_held_out"]
            assert round(error, 1) == 3.3 and round(guess, 1) == 4.8
            for i, (value, label, colour) in enumerate(((error, "Calibrated detector", CYAN), (guess, "Fixed-count baseline", MUTED))):
                x = 120 + i * 870
                roundbox(img, (x, 230, x + 800, 750), PANEL, 32, LINE)
                text(img, x + 400, 292, label, 33, 550, MUTED, centre=True)
                text(img, x + 400, 385, f"{value:.1f}", 142, 650, colour, centre=True)
                text(img, x + 400, 585, "people per frame · mean absolute error", 25, 450, MUTED, centre=True)
            pill(img, "20 labelled frames · one camera · offline", 120, 790, PURPLE)
        if t >= cue(self.report, 3) - .15:
            pill(img, "NOT YET IN THE APP", 1330, 60, AMBER)
        footer(img, "Mall dataset: Chen et al., 2012 · derived analysis only")
        boundary = cue(self.report, 1)
        if boundary <= t < boundary + .45:
            previous = backdrop().copy()
            self.draw_N11(previous, boundary - 1 / FPS)
            dissolve(img, previous, img.copy(), phase(t, boundary, .45))

    def draw_N12(self, img, t):
        failure = cue(self.report, 2)
        review = cue(self.report, 3)
        if t < failure:
            header(img, "Test the prediction", "Held-out simulated days · 15-minute forecast", t)
            m = json.loads((ROOT / "ml/models/metrics.json").read_text())["per_horizon"]["h15"]
            a, b = m["test"]["f1_macro"], m["persistence_baseline"]["test"]["f1_macro"]
            for i, (v, label, colour) in enumerate(((a, "Model", CYAN), (b, "No change", MUTED))):
                x = 380 + i * 660
                text(img, x + 245, 230, label, 31, 550, MUTED, centre=True)
                text(img, x + 245, 310, f"{v:.3f}", 125, 650, colour, centre=True)
            text(img, W / 2, 480, "Macro-F1", 39, 600, centre=True)
            if t > 3:
                roundbox(img, (225, 600, 1695, 790), PANEL, 24)
                text(img, 270, 630, "Accuracy       96.4%  vs  94.3%", 31, 500)
                text(img, 270, 685, "Critical recall   91%  vs  79%", 31, 500)
                text(img, 1080, 650, "Always SAFE\naccuracy: 84.6%", 25, 450, MUTED)
            footer(img, "SIMULATED · observed-class test labels · these scores do not measure warning lead time")
        elif t < review:
            header(img, "The warning came later", "Recorded simulation · one fast-surge scenario", t)
            d = ImageDraw.Draw(img)
            d.line((320, 520, 1600, 520), fill=LINE, width=7)
            for x, title, clock, colour in ((490, "Threshold crossed", "14:08:09", RED),
                                           (1390, "First confident warning", "14:09:08", AMBER)):
                d.ellipse((x - 20, 500, x + 20, 540), fill=colour)
                text(img, x, 360, title, 33, 550, colour, centre=True)
                text(img, x, 575, clock, 49, 600, centre=True)
            text(img, W / 2, 730, "Prototype threshold 0.70 · not a validated safety limit", 28, 450, MUTED, centre=True)
            footer(img, "Run A sampled timeline · a high score does not establish useful warning time")
        else:
            header(img, "Uncertainty stays visible", "Adjusted score · staff review cue", t)
            frame = snapshot("C2a", 108)
            window(img, frame, (200, 260, 1720, 750), "ACTUAL REVIEW INTERFACE", (300, 790, 1100, 1070))
            if t >= cue(self.report, 4):
                text(img, W / 2, 800, "Not a calibrated probability", 35, 550, AMBER,
                     phase(t, cue(self.report, 4), .45), centre=True)
        for boundary in (failure, review):
            if boundary <= t < boundary + .45:
                previous = backdrop().copy()
                self.draw_N12(previous, boundary - 1 / FPS)
                dissolve(img, previous, img.copy(), phase(t, boundary, .45))

    def draw_N13(self, img, t):
        header(img, "Who can use the route?", "MODEL CHECK · full closure · synthetic wheelchair journeys", t)
        if t < cue(self.report, 1):
            text(img, W / 2, 425, "What about Mrs Chan?", 84, 650, centre=True)
            return
        source = self.footage("C2c", 7 + min(3, (t - cue(self.report, 1)) * .6))
        window(img, source, (130, 230, 1790, 835), "RECORDED SKETCHFUTURE MODEL CHECK")
        grid_start = cue(self.report, 1) + 3.4
        if t < grid_start:
            footer(img, "Map © OpenStreetMap contributors · full-closure stress test, not route certification")
            return
        recorded = img.copy()
        cohort = backdrop().copy()
        header(cohort, "Who can use the route?", "MODEL CHECK · full closure · synthetic wheelchair journeys", t)
        roundbox(cohort, (160, 260, 1760, 745), PANEL, 32, LINE)
        for i, title in enumerate(("Before", "After full closure")):
            x = 285 + i * 850
            text(cohort, x + 190, 300, title, 35, 600, centre=True)
            dot_grid(cohort, x, 405)
            text(cohort, x + 190, 625, "24 / 40", 56, 650, PURPLE, centre=True)
        text(cohort, W / 2, 795, "Purple: no mapped step-free route in either plan", 32, 550, centre=True)
        if t >= cue(self.report, 2):
            pill(cohort, "MAP DATA + ON-SITE CHECKS", 660, 862, AMBER)
        dissolve(img, recorded, cohort, phase(t, grid_start, .6))
        footer(img, "Map © OpenStreetMap contributors · model reachability is not field certification")

    def draw_N14(self, img, t):
        header(img, "Three separate checks", "What the tests taught us", t)
        for i, (label, sub, colour) in enumerate((("Prediction quality", "How well does it classify?", CYAN),
                     ("Warning time", "Is there time to act?", AMBER), ("Route accessibility", "Who can use the route?", PURPLE))):
            x = 110 + i * 575
            roundbox(img, (x, 285, x + 540, 730), PANEL, 30, LINE)
            text(img, x + 270, 355, f"0{i + 1}", 85, 650, colour, centre=True)
            text(img, x + 270, 505, label, 32, 600, centre=True)
            text(img, x + 270, 575, sub, 24, 450, MUTED, centre=True)

    def draw_N15(self, img, t):
        header(img, "The next milestone is evidence", "Validation before field claims", t)
        for i, (title, status, colour) in enumerate((("Melbourne forecasting test", "PRE-REGISTERED · PENDING", AMBER),
                      ("Supervised pilot", "PROPOSED · WITH PERMISSION", CYAN))):
            x = 120 + i * 880
            roundbox(img, (x, 300, x + 800, 735), PANEL, 30, LINE)
            text(img, x + 400, 400, title, 39, 600, width=700, centre=True)
            text(img, x + 400, 585, status, 23, 550, colour, centre=True)

    def draw_N16(self, img, t):
        source_t = float(np.interp(t, [0, 1.4, 2, 3.6, 5.4, 8], [0, 1.6, 3.53, 4.3, 5.1, 6.95]))
        frame = legacy("S18").draw_frame(source_t)
        img.alpha_composite(frame)

    def draw_N17(self, img, t):
        group(img, t, "close")

    def draw_N18(self, img, t):
        text(img, W / 2, 85, "CrowdPulse Macau", 92, 650, centre=True)
        text(img, W / 2, 220, "github.com/Yh1sam/crowdpulse-macau", 39, 550, CYAN, centre=True)
        for i, p in enumerate(PEOPLE.values()):
            x = 130 + i * 425
            roundbox(img, (x, 340, x + 385, 520), PANEL, 22, LINE)
            text(img, x + 192, 375, p["name"], 29, 600, centre=True)
            text(img, x + 192, 440, p["role"], 19, 450, MUTED, centre=True)
        text(img, W / 2, 575, "School and supervisor details pending", 24, 450, AMBER, centre=True)
        credits = ["Toronto clip: Raysonho · Wikimedia Commons · CC0", "Map: OpenStreetMap contributors · ODbL",
                   "Mall dataset: Chen et al., BMVC 2012 · derived results", "Melbourne counts: City of Melbourne · CC BY",
                   "YOLO11: Ultralytics · AGPL-3.0", "Fonts: Geist + Noto Sans TC · SIL OFL"]
        for i, line in enumerate(credits):
            text(img, 140 + (i % 2) * 850, 690 + (i // 2) * 63, line, 21, 450, MUTED)


def render_scene(sid):
    shot, scene = SHOTS[sid], Scene(sid)
    slot = shot["end_s"] - shot["start_s"]
    path = BUILD / "scenes" / f"{sid}.mp4"
    path.parent.mkdir(parents=True, exist_ok=True)
    encoder = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-preset", "fast", "-crf", "18", "-threads", "2", *COLOUR, "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    try:
        for i in range(round(slot * FPS)):
            encoder.stdin.write(scene.draw(i / FPS).tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f"Encoder failed: {sid}")
    finally:
        scene.close()
        if encoder.poll() is None:
            encoder.terminate(); encoder.wait()
    assert abs(duration(path) - slot) < 1 / FPS
    return f"{sid}: {slot:.1f}s rendered"


def stills():
    out = BUILD / "stills"
    out.mkdir(parents=True, exist_ok=True)
    points = {"N01": [2], "N02": [5, 13, 22], "N03": [5, 13], "N04": [4], "N05": [2],
              "N06": [4, 16], "N07": [3, 10, 16], "N08": [3, 10, 16], "N09": [3, 7, 11, 17],
              "N10": [4, 12, 18], "N11": [3, 12, 18], "N12": [6, 15, 24], "N13": [9, 23],
              "N14": [5], "N15": [6], "N16": [6], "N17": [2], "N18": [3]}
    for sid, times in points.items():
        scene = Scene(sid)
        for t in times:
            scene.draw(t).save(out / f"{sid}_{t:g}.png")
        scene.close()
        print(f"{sid}: stills", flush=True)


def assemble():
    out = BUILD / "cut"
    out.mkdir(parents=True, exist_ok=True)
    paths = [BUILD / "scenes" / f"{s['id']}.mp4" for s in scenes()]
    for path, shot in zip(paths, scenes()):
        assert abs(duration(path) - (shot["end_s"] - shot["start_s"])) < 1 / FPS
    listing = out / "clips.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in paths))
    video = out / "video.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(video)])
    audio = out / "narration.wav"
    with wave.open(str(audio), "wb") as dest:
        dest.setnchannels(1); dest.setsampwidth(2); dest.setframerate(48000)
        for shot in scenes():
            path = BUILD / "guide" / f"{shot['id']}.wav"
            if path.exists():
                with wave.open(str(path)) as src:
                    dest.writeframes(src.readframes(src.getnframes()))
            else:
                dest.writeframes(b"\0" * (shot["end_s"] - shot["start_s"]) * 96000)
    final = out / "crowdpulse_v2_reviewed_full_1080p.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(audio), "-c:v", "copy", "-bsf:v", H264_COLOUR,
         "-af", "loudnorm=I=-18:TP=-2:LRA=9", "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
         "-t", str(RUNTIME_S), "-movflags", "+faststart", str(final)])
    preview = out / "crowdpulse_v2_reviewed_full_preview_720p.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-vf", "scale=1280:720", "-c:v", "libx264",
         "-crf", "21", "-preset", "fast", *COLOUR, "-bsf:v", H264_COLOUR,
         "-c:a", "copy", "-movflags", "+faststart", str(preview)])
    print(final, flush=True)
    print(preview, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--guides", action="store_true")
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    export()
    BUILD.mkdir(parents=True, exist_ok=True)
    if args.guides or not (BUILD / "guide.json").exists():
        make_guides()
    if args.stills:
        stills()
    if args.render:
        ids = args.only or list(SHOTS)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(render_scene, sid): sid for sid in ids}
            for future in as_completed(futures):
                print(future.result(), flush=True)
    if args.assemble:
        assemble()


if __name__ == "__main__":
    main()
