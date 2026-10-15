"""Shot S16 (3:21.5-3:38.5, 17.0 s): "What's next?" - the Melbourne real-data test, announced before its result.

Storyboard: docs/video/script.md section 3, row S16; claims table section 4, rows S16; section 6
("Global look and tools", "motion_graphic": S16 reads minute/*.csv.gz, filtering sensors.csv to the ids
present); shot list docs/video/shotlist.json (id S16).

Left: one dot per sensor at its real latitude / longitude, only for the location_ids that actually occur
in the minute archive (no basemap; a 1 km scale bar and a north arrow only). Each dot's area follows that
sensor's archived pedestrians per minute (total_of_directions, a 15-minute centred average so the playback
does not flicker; a missing minute counts as zero, as the dataset README says), played back over the whole
archived period. Right: the sensor count (counted here, not assumed), the Melbourne-time playback clock and
a calendar strip of hour cells filling from 12 Oct 2026 to the latest archived date, and the "Not Macau"
caveat. From "...before its result" the map dims and the result panel comes in: a grey dashed PENDING
stamp and the verbatim result placeholder in an amber dashed box. The count-to-level mapping line is NOT
drawn: no mapping has been committed to experiments/datasets/melbourne/README.md.

Data (read, never retyped):
  experiments/datasets/melbourne/minute/*.csv.gz   location_id, sensing_datetime (UTC), sensing_date /
                                                   sensing_time (Melbourne local), total_of_directions
  experiments/datasets/melbourne/sensors.csv       latitude / longitude of the ids present
  docs/video/shotlist.json                         duration and the on-screen wording (checked below)

Run: .venv/bin/python video/mg/S16.py [--stills]  -> video/build/mg/S16.mp4, stills in video/build/mg/stills/
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import sys
from datetime import datetime, timedelta
from functools import lru_cache

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from style import FONTS, ROOT  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

# ---------- timing ----------

SHOTS = json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text())
SHOT = next(s for s in SHOTS if s["id"] == "S16")
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)  # 17.0 s

# Seconds from the shot start, keyed to the narration at 140 wpm (0.43 s per word, voice from 0.3 s;
# "99" is read "ninety-nine", two words). re-key to the real voice take
BEATS = {
    "dots": 0.3,          # "Because our forecasting results..." -> sensor dots ripple in from the centre
    "playback": 1.6,      # "...are simulated," -> the archive starts playing; clock and calendar strip fill
    "real_counts": 4.5,   # "real counts" -> the sensor count ticks up, each dot pinging as it is counted
    "ninety_nine": 5.9,   # "ninety-nine" -> the count lands on the number of ids found
    "melbourne": 6.7,     # "Melbourne street sensors:" -> the "Not Macau" caveat card
    "result": 10.1,       # "...before its result." -> map dims, the result panel slides in
    "pending": 10.6,      # result slot starts -> the PENDING stamp lands
    "placeholder": 11.1,  # -> the verbatim result placeholder in its amber dashed box
}
CHAPTER_END = 2.0                 # chapter card for about 2 s
PLAYBACK_END = DURATION - 0.6     # the whole archived period plays from BEATS["playback"] to here

# ---------- on-screen text (storyboard wording, checked against the shot list) ----------

CHAPTER = "What's next?"
CREDIT = "City of Melbourne pedestrian counts · per minute · CC BY"
SINCE = "archived hourly since 12 Oct 2026"
CAVEAT_LEAD = "Not Macau:"
CAVEAT_REST = "counts people crossing a line, not camera density. Tests the method, not accuracy in Macau."
PLACEHOLDER = "[RESULT PENDING - fill after analysis, report honestly whatever it shows]"
BADGE_SUB = "Real data, analysis pending"            # section 4 claims table, status of the S16 row
SENSORS_LABEL = "Melbourne street sensors"           # narration: "...from 99 Melbourne street sensors"
SENSORS_SUB = "real counts · one dot per sensor"
RESULT_HEAD = "Melbourne test · result"

_ost = SHOT["on_screen_text"]
for s_ in (CHAPTER, "City of Melbourne pedestrian counts · per minute", "CC BY", SINCE,
           f"{CAVEAT_LEAD} {CAVEAT_REST}", PLACEHOLDER):
    assert s_ in _ost, f"not in the storyboard's on-screen text: {s_!r}"
assert SENSORS_LABEL in SHOT["narration"]
assert BADGE_SUB in (ROOT / "docs" / "video" / "script.md").read_text()

# ---------- data ----------

MEL = ROOT / "experiments" / "datasets" / "melbourne"


def load_archive():
    """All rows of minute/*.csv.gz as (location_id, utc minute, local minute, total_of_directions)."""
    rows = []
    for f in sorted((MEL / "minute").glob("*.csv.gz")):
        with gzip.open(f, "rt", newline="") as fh:
            for r in csv.DictReader(fh):
                utc = datetime.fromisoformat(r["sensing_datetime"]).replace(tzinfo=None)
                loc = datetime.strptime(f'{r["sensing_date"]} {r["sensing_time"]}', "%Y-%m-%d %H:%M")
                rows.append((r["location_id"], utc, loc, int(r["total_of_directions"])))
    return rows


ROWS = load_archive()
with open(MEL / "sensors.csv", newline="") as fh:
    SENSORS = {r["location_id"]: r for r in csv.DictReader(fh)}

IDS = sorted({r[0] for r in ROWS}, key=int)                      # only the ids present in the archive
missing = [i for i in IDS if i not in SENSORS]
assert not missing, f"location_ids with no row in sensors.csv: {missing}"
N = len(IDS)
LAT = np.array([float(SENSORS[i]["latitude"]) for i in IDS])
LON = np.array([float(SENSORS[i]["longitude"]) for i in IDS])

offsets = {loc - utc for _, utc, loc, _ in ROWS}
assert len(offsets) == 1, f"several UTC offsets in the archive (daylight-saving change?): {offsets}"
LOCAL_OFFSET = offsets.pop()                                     # +11 h (AEDT)
UTC0 = min(r[1] for r in ROWS)
UTC1 = max(r[1] for r in ROWS)
M = int((UTC1 - UTC0).total_seconds() // 60) + 1                 # archived minutes, first to last
LOC0, LOC1 = UTC0 + LOCAL_OFFSET, UTC1 + LOCAL_OFFSET

COUNTS = np.zeros((N, M), dtype=np.float32)                       # a missing minute is zero (README)
_col = {i: k for k, i in enumerate(IDS)}
for lid, utc, _, c in ROWS:
    COUNTS[_col[lid], int((utc - UTC0).total_seconds() // 60)] = c

SMOOTH_MIN = 15                                                   # display smoothing: centred 15-min mean
_pad = np.pad(COUNTS, ((0, 0), (SMOOTH_MIN // 2, SMOOTH_MIN // 2)), mode="edge")
_cs = np.concatenate([np.zeros((N, 1)), np.cumsum(_pad, axis=1, dtype=np.float64)], axis=1)
SMOOTH = ((_cs[:, SMOOTH_MIN:] - _cs[:, :-SMOOTH_MIN]) / SMOOTH_MIN).astype(np.float32)
assert SMOOTH.shape == (N, M)

DAY0 = datetime(LOC0.year, LOC0.month, LOC0.day)                 # first archived local day (12 Oct)
DAYS = (datetime(LOC1.year, LOC1.month, LOC1.day) - DAY0).days + 1
assert SINCE.endswith(f"{DAY0.day} {DAY0:%b %Y}"), f"archive starts on {DAY0:%d %b %Y}, not as the storyboard says"
if f"{N} sensors" not in _ost or f"from {N} Melbourne" not in SHOT["narration"]:
    print(f"WARNING: the archive has {N} distinct location_ids; the storyboard and narration say otherwise. "
          f"Update the voice line and captions to {N}.")

# ---------- layout ----------

MAP_BOX = (80, 150, 820, 790)          # map panel (bottom stays above the lower-third slot, y 795)
MW, MH = MAP_BOX[2] - MAP_BOX[0], MAP_BOX[3] - MAP_BOX[1]
SS = 3                                 # supersampling for the dots
FIT = (130, 205, 790, 700)             # where the sensors are fitted (frame coordinates); key below y 710
RX0, RX1 = 900, 1860                   # right column
NUM_BASE = 282                         # baseline of the sensor count
CAL_HEAD, CLOCK_BASE, DAYLAB_BASE = 392, 446, 492
STRIP_Y0, STRIP_Y1 = 512, 550
HOURLAB_BASE = 578
CAVEAT_Y1 = MAP_BOX[3]                 # the caveat card's bottom lines up with the map panel


def meridian_km_per_deg(lat: float) -> float:
    p = math.radians(lat)
    return (111132.954 - 559.822 * math.cos(2 * p) + 1.175 * math.cos(4 * p)) / 1000


_la0, _la1, _lo0, _lo1 = LAT.min(), LAT.max(), LON.min(), LON.max()
_kx = math.cos(math.radians((_la0 + _la1) / 2))
_scale = min((FIT[2] - FIT[0]) / ((_lo1 - _lo0) * _kx), (FIT[3] - FIT[1]) / (_la1 - _la0))  # px per deg lat
PX_PER_KM = _scale / meridian_km_per_deg((_la0 + _la1) / 2)
_cx, _cy = (FIT[0] + FIT[2]) / 2, (FIT[1] + FIT[3]) / 2
_mx, _my = (_lo0 + _lo1) / 2, (_la0 + _la1) / 2
PX = _cx + (LON - _mx) * _kx * _scale                              # frame coordinates of each sensor
PY = _cy - (LAT - _my) * _scale

# reveal order: a ripple out from the busiest part of the network (distance from the median position)
_d = np.hypot(PX - np.median(PX), PY - np.median(PY))
RANK = np.argsort(np.argsort(_d))
APPEAR = BEATS["dots"] + 1.1 * RANK / max(1, N - 1)              # each dot grows in over 0.45 s
PING = BEATS["real_counts"] + (BEATS["ninety_nine"] - BEATS["real_counts"] - 0.15) * RANK / max(1, N - 1)

R0, RK = 3.0, 2.6                      # dot radius (px) = R0 + RK * sqrt(people per minute)


def radius(v):
    return R0 + RK * np.sqrt(np.maximum(v, 0))


# ---------- small drawing helpers ----------


def rgba(c, a: float = 1.0) -> tuple[int, int, int, int]:
    return (*[int(v) for v in c[:3]], int(round(255 * clamp(a))))


def with_alpha(src: Image.Image, alpha: float) -> Image.Image:
    if alpha >= 1:
        return src
    out = src.copy()
    out.putalpha(out.getchannel("A").point(lambda v: int(v * alpha)))
    return out


def paste(dst: Image.Image, src: Image.Image, xy, alpha: float = 1.0) -> None:
    if alpha <= 0:
        return
    dst.alpha_composite(with_alpha(src, alpha), (int(round(xy[0])), int(round(xy[1]))))


@lru_cache(maxsize=4096)
def tsprite(text: str, size: int, weight: int, fill: tuple) -> tuple[Image.Image, int, int, float]:
    """Text on a tight transparent sprite: (image, x of the origin, y of the baseline, advance width)."""
    f = text_font(text, size, weight)
    asc, desc = f.getmetrics()
    adv = f.getlength(text)
    pad = 4
    im = Image.new("RGBA", (int(adv) + 2 * pad + 2, asc + desc + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad, pad + asc), text, font=f, fill=rgba(fill), anchor="ls")
    return im, pad, pad + asc, adv


def put(dst: Image.Image, x: float, y: float, text: str, size: int, weight: int = 500, fill=INK,
        alpha: float = 1.0, align: str = "l") -> float:
    """Draws text with its baseline at y; align l / m / r. Returns the advance width."""
    im, ox, oy, adv = tsprite(text, size, weight, tuple(fill))
    dx = {"l": 0, "m": adv / 2, "r": adv}[align]
    paste(dst, im, (x - dx - ox, y - oy), alpha)
    return adv


@lru_cache(maxsize=1)
def _tnum_font_bytes() -> bytes:
    """Geist with its own tabular figures (the 'tnum' .tf glyphs) mapped to the digit characters.
    This Pillow build has no raqm, so OpenType features cannot be switched on; remapping the cmap in
    memory gives the same glyphs. Nothing is written to disk."""
    import io
    from fontTools.ttLib import TTFont
    f = TTFont(str(FONTS / "Geist[wght].ttf"))
    sub = {}
    for fr in f["GSUB"].table.FeatureList.FeatureRecord:
        if fr.FeatureTag == "tnum":
            for li in fr.Feature.LookupListIndex:
                for st in f["GSUB"].table.LookupList.Lookup[li].SubTable:
                    st = getattr(st, "ExtSubTable", st)
                    sub.update(getattr(st, "mapping", {}) or {})
    for tbl in f["cmap"].tables:
        if tbl.isUnicode():
            for c in "0123456789":
                g = tbl.cmap.get(ord(c))
                if g in sub:
                    tbl.cmap[ord(c)] = sub[g]
    buf = io.BytesIO()
    f.save(buf)
    return buf.getvalue()


@lru_cache(maxsize=None)
def tnum_font(size: int, weight: int):
    import io
    try:
        f = ImageFont.truetype(io.BytesIO(_tnum_font_bytes()), size)
        f.set_variation_by_axes([weight])
        return f
    except Exception:                                   # fall back to the plain font
        return font(size, weight)


@lru_cache(maxsize=4096)
def tnum_sprite(text: str, size: int, weight: int, fill: tuple) -> tuple[Image.Image, int, int, float]:
    f = tnum_font(size, weight)
    asc, desc = f.getmetrics()
    adv = f.getlength(text)
    pad = 4
    im = Image.new("RGBA", (int(adv) + 2 * pad + 2, asc + desc + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad, pad + asc), text, font=f, fill=rgba(fill), anchor="ls")
    return im, pad, pad + asc, adv


def put_tabular(dst: Image.Image, x: float, y: float, text: str, size: int, weight: int, fill, alpha: float = 1.0) -> float:
    """Left-aligned text set in tabular figures (every digit the same width), so a ticking value never
    shifts. Returns the x after the text."""
    im, ox, oy, adv = tnum_sprite(text, size, weight, tuple(int(v) for v in fill[:3]))
    paste(dst, im, (x - ox, y - oy), alpha)
    return x + adv


def tabular_width(text: str, size: int, weight: int) -> float:
    return tnum_font(size, weight).getlength(text)


def rrect_path(box, r: float, n: int = 12):
    x0, y0, x1, y1 = box
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts


def dashed_path(d: ImageDraw.ImageDraw, pts, fill, width: float, dash: float, gap: float) -> None:
    """Dashes along a closed polyline, continuous around the corners."""
    acc, run = 0.0, []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / 2))
        for i in range(n + 1):
            s = acc + seg * i / n
            p = (x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
            if (s % (dash + gap)) < dash:
                run.append(p)
            elif run:
                if len(run) > 1:
                    d.line(run, fill=fill, width=int(width), joint="curve")
                run = []
        acc += seg
    if len(run) > 1:
        d.line(run, fill=fill, width=int(width), joint="curve")


def hires(size, fn, ss: int = 3) -> Image.Image:
    """Draws with fn(ImageDraw, k) at ss x scale and downsamples (antialiased shapes)."""
    big = Image.new("RGBA", (size[0] * ss, size[1] * ss), (0, 0, 0, 0))
    fn(ImageDraw.Draw(big), ss)
    return big.resize(size, Image.LANCZOS)


def dashed_box_sprite(w_: int, h_: int, radius: int, border, fill=None, width: float = 3, dash: float = 16,
                      gap: float = 10) -> Image.Image:
    def fn(d, k):
        m = width * k
        b = (m, m, w_ * k - m, h_ * k - m)
        if fill is not None:
            d.rounded_rectangle(b, radius * k, fill=fill)
        dashed_path(d, rrect_path(b, radius * k), rgba(border), width * k, dash * k, gap * k)
    return hires((w_, h_), fn)


# ---------- static layers ----------


def map_background() -> Image.Image:
    """The bare map panel at SS x scale (the frame region it covers, opaque)."""
    k = SS
    big = Image.new("RGBA", (MW * k, MH * k), rgba(NAVY))
    ImageDraw.Draw(big).rounded_rectangle((0, 0, MW * k - 1, MH * k - 1), 24 * k, fill=rgba(NAVY_2))
    return big


MAP_BG = map_background()
MAP_BG_RGB = MAP_BG.convert("RGB")     # opaque: ImageDraw blends translucent shapes only on RGB
MAP_BG_SMALL = MAP_BG.resize((MW, MH), Image.BOX)
KEY_VALUES = (10, 30, 60)              # dot-size key, people per minute


def map_key() -> Image.Image:
    """Scale bar, north arrow and dot-size key on a transparent layer the size of the map panel."""
    lay = Image.new("RGBA", (MW, MH), (0, 0, 0, 0))
    ox, oy = MAP_BOX[0], MAP_BOX[1]

    def shapes(d, k):
        def L(x, y):  # frame -> supersampled panel coordinates
            return ((x - ox) * k, (y - oy) * k)
        # north arrow, top-right corner
        nx, ny = MAP_BOX[2] - 46, MAP_BOX[1] + 52
        d.polygon([L(nx, ny - 2), L(nx + 11, ny + 26), L(nx, ny + 19), L(nx - 11, ny + 26)], fill=rgba(INK_2))
        # scale bar (1 km) to the left of the arrow
        x1, y = nx - 40, MAP_BOX[1] + 60
        d.line([L(x1 - PX_PER_KM, y), L(x1, y)], fill=rgba(INK_2), width=3 * k)
        for xx in (x1 - PX_PER_KM, x1):
            d.line([L(xx, y - 7), L(xx, y + 7)], fill=rgba(INK_2), width=3 * k)
        # dot-size key circles, bottom-left
        for v, cx, _ in KEY_POS:
            r = float(radius(v))
            d.ellipse((*L(cx - r, KEY_BASE - 2 * r), *L(cx + r, KEY_BASE)), fill=rgba(CYAN, 0.30),
                      outline=rgba(CYAN, 0.85), width=int(1.6 * k))
            m = 2.4
            d.ellipse((*L(cx - m, KEY_BASE - r - m), *L(cx + m, KEY_BASE - r + m)), fill=rgba(INK))

    lay.alpha_composite(hires((MW, MH), shapes))
    nx = MAP_BOX[2] - 46
    put(lay, nx - ox, MAP_BOX[1] + 42 - oy, "N", 22, 700, INK_2, align="m")
    put(lay, nx - 40 - PX_PER_KM / 2 - ox, MAP_BOX[1] + 46 - oy, "1 km", 22, 600, INK_2, align="m")
    for v, cx, lx in KEY_POS:
        put(lay, lx - ox, KEY_BASE - float(radius(v)) + 8 - oy, str(v), 21, 600, INK_2)
    tx = KEY_POS[-1][2] + 60
    put(lay, tx - ox, KEY_BASE - 30 - oy, "dot size: people per minute", 22, 600, INK_2)
    put(lay, tx - ox, KEY_BASE - 3 - oy, f"{SMOOTH_MIN}-minute average, both directions", 20, 500, INK_3)
    return lay


KEY_BASE = MAP_BOX[3] - 26             # the key circles sit on this line
KEY_POS, _x = [], MAP_BOX[0] + 34      # (value, circle centre x, label x)
for _v in KEY_VALUES:
    _r = float(radius(_v))
    KEY_POS.append((_v, _x + _r, _x + 2 * _r + 7))
    _x += 2 * _r + 7 + font(21, 600).getlength(str(_v)) + 20
MAP_KEY = map_key()


def base_static(with_badge: bool) -> Image.Image:
    img = canvas()
    legend_strip(img)
    footer(img, CREDIT)
    if with_badge:
        badge(img, "PENDING", sub=BADGE_SUB)
    return img


BASE = base_static(False)
BASE_BADGE = base_static(True)

# calendar strip geometry: DAYS x 24 hour cells
DAY_GAP, HOUR_GAP = 12, 2
DAY_W = (RX1 - RX0 - DAY_GAP * (DAYS - 1)) / DAYS
CELL_W = (DAY_W - HOUR_GAP * 23) / 24


def cell_x(day: int, hour: int) -> float:
    return RX0 + day * (DAY_W + DAY_GAP) + hour * (CELL_W + HOUR_GAP)


ARCH0 = (LOC0 - DAY0).total_seconds() / 60          # first archived minute, in local minutes after 00:00 of day 0


def strip_static() -> Image.Image:
    """Empty hour cells, day labels and hour labels (transparent layer, right column only)."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for day in range(DAYS):
        for h in range(24):
            x = cell_x(day, h)
            d.rounded_rectangle((x, STRIP_Y0, x + CELL_W, STRIP_Y1), 3, fill=rgba(NAVY_3))
        date = DAY0 + timedelta(days=day)
        label = f"{date:%a} {date.day} {date:%b}" if DAY_W >= 140 else f"{date.day}"
        put(lay, cell_x(day, 0), DAYLAB_BASE, label, 22, 600, INK_2)
        if DAY_W >= 300:
            for h in (6, 12, 18):
                put(lay, cell_x(day, h) - HOUR_GAP / 2, HOURLAB_BASE, f"{h:02d}:00", 20, 500, INK_3, align="m")
                d.line([(cell_x(day, h) - HOUR_GAP / 2, STRIP_Y1 + 3), (cell_x(day, h) - HOUR_GAP / 2, STRIP_Y1 + 8)],
                       fill=rgba(INK_3), width=2)
    return lay.crop((RX0 - 10, DAYLAB_BASE - 30, RX1 + 10, HOURLAB_BASE + 12))


STRIP = strip_static()
STRIP_XY = (RX0 - 10, DAYLAB_BASE - 30)


def caveat_sprite() -> Image.Image:
    """The "Not Macau" card: info glyph, bold lead, the rest wrapped; height fitted to the text."""
    w_ = RX1 - RX0
    size, lh, tx, top = 27, 38, 84, 58
    lead_w = font(size, 700).getlength(CAVEAT_LEAD) + font(size, 500).getlength(" ")
    lines, line, avail = [], "", w_ - tx - 36 - lead_w
    for w__ in CAVEAT_REST.split():
        trial = f"{line} {w__}".strip()
        if font(size, 500).getlength(trial) <= avail or not line:
            line = trial
        else:
            lines.append(line)
            line, avail = w__, w_ - tx - 36
    lines.append(line)
    h_ = top + (len(lines) - 1) * lh + 34
    spr = hires((w_, h_), lambda d, k: d.rounded_rectangle((0, 0, w_ * k - 1, h_ * k - 1), 18 * k, fill=rgba(NAVY_2)))
    gi = hires((34, 34), lambda d, k: d.ellipse((1 * k, 1 * k, 33 * k, 33 * k), outline=rgba(INK_2), width=3 * k))
    spr.alpha_composite(gi, (32, top - 27))
    put(spr, 49, top - 2, "i", 22, 700, INK_2, align="m")
    put(spr, tx, top, CAVEAT_LEAD, size, 700, INK)
    for i, ln in enumerate(lines):
        put(spr, tx + (lead_w if i == 0 else 0), top + i * lh, ln, size, 500, INK_2)
    return spr


CAVEAT = caveat_sprite()
CAVEAT_XY = (RX0, CAVEAT_Y1 - CAVEAT.height)


def stamp_sprite() -> Image.Image:
    """Grey dashed PENDING stamp (unrotated), drawn large."""
    size, track = 92, 10
    f = font(size, 800)
    widths = [f.getlength(c) for c in "PENDING"]
    tw = sum(widths) + track * 6
    pad_x, pad_y = 46, 26
    w_, h_ = int(tw + 2 * pad_x), int(size * 0.72 + 2 * pad_y + 16)
    spr = dashed_box_sprite(w_, h_, 22, GREY, fill=rgba(NAVY_2), width=5, dash=22, gap=12)
    x = pad_x
    for c, cw in zip("PENDING", widths):
        put(spr, x, h_ / 2 + size * 0.36, c, size, 800, INK_2)
        x += cw + track
    return spr


STAMP = stamp_sprite()


def placeholder_sprite() -> Image.Image:
    size, lh = 30, 42
    lines = wrap(PLACEHOLDER, size, 600, 640)
    w_ = int(max(font(size, 600).getlength(l) for l in lines)) + 2 * 32
    h_ = len(lines) * lh + 2 * 24
    spr = dashed_box_sprite(w_, h_, 14, WARNING, fill=rgba(NAVY), width=3, dash=16, gap=10)
    for i, ln in enumerate(lines):
        put(spr, 32, 24 + 31 + i * lh, ln, size, 600, WARNING)
    return spr


PLACE = placeholder_sprite()
HEAD_BACK = hires((int(font(26, 600).getlength(RESULT_HEAD)) + 34, 64),
                  lambda d, k: d.rounded_rectangle((0, 0, (int(font(26, 600).getlength(RESULT_HEAD)) + 34) * k - 1, 64 * k - 1),
                                                   12 * k, fill=rgba(NAVY_2)))
RES_CX = (MAP_BOX[0] + MAP_BOX[2]) / 2          # the result content is centred in the map panel
RES_HEAD_BASE = MAP_BOX[1] + 64
STAMP_CY = MAP_BOX[1] + 262
PLACE_Y = MAP_BOX[1] + 420
assert PLACE.width <= MW - 40 and PLACE_Y + PLACE.height <= MAP_BOX[3] - 30

# ---------- per-frame drawing ----------


def playback_pos(t: float) -> float:
    """Archive minute (float, 0 .. M-1) shown at shot time t (linear playback)."""
    return clamp((t - BEATS["playback"]) / (PLAYBACK_END - BEATS["playback"])) * (M - 1)


def values_at(pos: float) -> np.ndarray:
    i0 = int(math.floor(pos))
    i1 = min(M - 1, i0 + 1)
    f = pos - i0
    return SMOOTH[:, i0] * (1 - f) + SMOOTH[:, i1] * f


def ease_out(x: float) -> float:
    x = clamp(x)
    return 1 - (1 - x) ** 3


def map_frame(t: float) -> Image.Image:
    # Draw on an RGB copy so every translucent disc and ping ring is blended over what is below it.
    # (On an RGBA image ImageDraw replaces the pixels, alpha included, and a fading ring then shows the
    # navy page through the panel as a dark halo.)
    big = MAP_BG_RGB.copy()
    d = ImageDraw.Draw(big, "RGBA")
    k = SS
    vals = values_at(playback_pos(t))
    rad = radius(vals)
    grow = np.array([ease_out((t - a) / 0.45) for a in APPEAR])
    order = np.argsort(-rad)                      # big discs first, so small ones stay visible on top
    ox, oy = MAP_BOX[0], MAP_BOX[1]
    for i in order:
        g = grow[i]
        if g <= 0:
            continue
        x, y = (PX[i] - ox) * k, (PY[i] - oy) * k
        r = rad[i] * g * k
        heat = clamp(vals[i] / 60)
        d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(CYAN, (0.16 + 0.22 * heat) * g),
                  outline=rgba(CYAN, 0.8 * g), width=max(1, int(1.6 * k)))
    for i in order:                               # sensor position markers on top
        g = grow[i]
        if g <= 0:
            continue
        x, y = (PX[i] - ox) * k, (PY[i] - oy) * k
        m = 2.4 * k * g
        d.ellipse((x - m, y - m, x + m, y + m), fill=rgba(INK, g))
        # counting ping: a ring that expands and fades as this sensor is counted
        q = (t - PING[i]) / 0.7
        if 0 <= q <= 1:
            rr = (rad[i] + 3 + 14 * ease_out(q)) * k
            d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=rgba(INK, 0.75 * (1 - q)), width=int(2 * k))
    small = big.resize((MW, MH), Image.BOX).convert("RGBA")
    p = progress(t, BEATS["result"], 0.6)          # result: the dots fade to a faint texture, the key goes
    if p < 1:
        small.alpha_composite(with_alpha(MAP_KEY, 1 - p))
    if p > 0:
        small = Image.blend(small, MAP_BG_SMALL, 0.86 * p)
    return small


def local_time(t: float) -> datetime:
    return LOC0 + timedelta(minutes=playback_pos(t))


def clock_prefix(d: datetime) -> str:
    return f"{d:%a} {d.day} {d:%b} · "


def shot_time_of_local(dt: datetime) -> float:
    """Shot time at which the playback clock reaches local time dt."""
    pos = (dt - LOC0).total_seconds() / 60
    return BEATS["playback"] + pos / max(1, M - 1) * (PLAYBACK_END - BEATS["playback"])


# when the date changes at midnight, the time and its label glide to their new place (no jump)
PREFIX_W = [font(40, 700).getlength(clock_prefix(DAY0 + timedelta(days=i))) for i in range(DAYS)]
MIDNIGHT_T = [shot_time_of_local(DAY0 + timedelta(days=i)) for i in range(1, DAYS)]


def clock_time_x(t: float) -> float:
    w_ = PREFIX_W[0]
    for i, tm in enumerate(MIDNIGHT_T):
        w_ = lerp(w_, PREFIX_W[i + 1], progress(t, tm, 0.25))
    return RX0 + w_


def draw_right_column(img: Image.Image, t: float) -> None:
    # sensor count, ticking up as each dot is counted
    a_num = progress(t, BEATS["real_counts"] - 0.15, 0.4)
    if a_num > 0:
        p = clamp((t - BEATS["real_counts"]) / (BEATS["ninety_nine"] - BEATS["real_counts"] - 0.15))
        shown = int(round(N * p))
        flash = 1 - progress(t, BEATS["ninety_nine"] + 0.1, 0.9) if t >= BEATS["ninety_nine"] - 0.2 else 0.0
        col = lerp(INK, CYAN, flash * progress(t, BEATS["ninety_nine"] - 0.2, 0.2))
        nw = tabular_width(str(N), 150, 800)
        put_tabular(img, RX0 + nw - tabular_width(str(shown), 150, 800), NUM_BASE, str(shown), 150, 800, col, a_num)
        lx = RX0 + nw + 34
        put(img, lx, NUM_BASE - 58, SENSORS_LABEL, 40, 700, INK, a_num)
        put(img, lx, NUM_BASE - 8, SENSORS_SUB, 26, 500, INK_2, a_num)

    # playback clock and calendar strip
    a_cal = progress(t, BEATS["playback"] - 0.3, 0.5)
    if a_cal > 0:
        put(img, RX0, CAL_HEAD, SINCE, 24, 600, INK_2, a_cal)
        lt = local_time(t)
        put(img, RX0, CLOCK_BASE, clock_prefix(lt), 40, 700, INK, a_cal)
        x = put_tabular(img, clock_time_x(t), CLOCK_BASE, f"{lt:%H:%M}", 40, 700, INK, a_cal)
        put(img, x + 16, CLOCK_BASE, "Melbourne time", 24, 500, INK_2, a_cal)
        paste(img, STRIP, STRIP_XY, a_cal)
        # fill: archived minutes up to the playhead, cell by cell
        now = ARCH0 + playback_pos(t)
        lay = Image.new("RGBA", (RX1 - RX0 + 20, STRIP_Y1 - STRIP_Y0 + 30), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        oxl, oyl = RX0 - 10, STRIP_Y0 - 14
        for day in range(DAYS):
            for h in range(24):
                c0 = (day * 24 + h) * 60
                s, e = max(c0, ARCH0), min(c0 + 60, now)
                if e <= s:
                    continue
                x = cell_x(day, h)
                xa, xb = x + CELL_W * (s - c0) / 60, x + CELL_W * (e - c0) / 60
                d.rounded_rectangle((xa - oxl, STRIP_Y0 - oyl, max(xa + 1, xb) - oxl, STRIP_Y1 - oyl), 3, fill=rgba(CYAN))
        # playhead
        day, rem = divmod(now, 24 * 60)
        hx = cell_x(int(day), int(rem // 60)) + CELL_W * (rem % 60) / 60 if day < DAYS else RX1
        d.polygon([(hx - 6 - oxl, STRIP_Y0 - 10 - oyl), (hx + 6 - oxl, STRIP_Y0 - 10 - oyl), (hx - oxl, STRIP_Y0 - 2 - oyl)], fill=rgba(INK))
        d.line([(hx - oxl, STRIP_Y0 - 2 - oyl), (hx - oxl, STRIP_Y1 + 3 - oyl)], fill=rgba(INK), width=2)
        paste(img, lay, (oxl, oyl), a_cal)

    # "Not Macau" caveat
    a_cav = progress(t, BEATS["melbourne"], 0.5)
    if a_cav > 0:
        paste(img, CAVEAT, (CAVEAT_XY[0], CAVEAT_XY[1] + (1 - a_cav) * 20), a_cav)


def draw_result(img: Image.Image, t: float) -> None:
    """The result slot, inside the map panel: heading, PENDING stamp, the verbatim placeholder."""
    a = progress(t, BEATS["result"] + 0.15, 0.45)
    if a <= 0:
        return
    # the heading sits on its own panel-coloured backing, so the faint sensor texture never runs under it
    paste(img, HEAD_BACK, (MAP_BOX[0] + 24, RES_HEAD_BASE - 40), a)
    put(img, MAP_BOX[0] + 40, RES_HEAD_BASE + (1 - a) * 14, RESULT_HEAD, 26, 600, INK_2, a)
    # PENDING stamp: lands from 125% scale, settling at a slight tilt
    q = clamp((t - BEATS["pending"]) / 0.4)
    if q > 0:
        e = ease_out(q)
        s = 1.25 - 0.25 * e
        spr = STAMP.resize((round(STAMP.width * s), round(STAMP.height * s)), Image.BICUBIC) if q < 1 else STAMP
        spr = spr.rotate(-1 - 3 * e, resample=Image.BICUBIC, expand=True)
        paste(img, spr, (RES_CX - spr.width / 2, STAMP_CY - spr.height / 2), clamp(q * 1.8))
    # the verbatim placeholder
    b = progress(t, BEATS["placeholder"], 0.45)
    if b > 0:
        paste(img, PLACE, (RES_CX - PLACE.width / 2, PLACE_Y + (1 - b) * 16), b)


def draw_frame(t: float) -> Image.Image:
    img = (BASE_BADGE if t >= 0.6 else BASE).copy()
    img.alpha_composite(map_frame(t), (MAP_BOX[0], MAP_BOX[1]))
    draw_right_column(img, t)
    draw_result(img, t)
    if t < 0.6:
        badge(img, "PENDING", sub=BADGE_SUB, alpha=progress(t, 0.1, 0.4))
    if t <= CHAPTER_END:
        chapter_card(img, CHAPTER, fade(t, 0.0, CHAPTER_END, 0.3))
    return img


STILLS = {
    "card": 1.2,
    "night": 3.4,
    "count": 5.3,
    "day": 9.2,
    "pending": 11.6,
    "end": 16.9,
}

if __name__ == "__main__":
    vmax = float(SMOOTH.max())
    print(f"S16: {DURATION} s; {N} location_ids in the archive (of {len(SENSORS)} in sensors.csv); "
          f"{M} minutes, {LOC0:%d %b %H:%M} - {LOC1:%d %b %H:%M} Melbourne time ({DAYS} calendar days); "
          f"busiest {SMOOTH_MIN}-min average {vmax:.0f}/min; {PX_PER_KM:.0f} px per km")
    for name, ts in STILLS.items():
        print(still(f"S16_{name}", draw_frame(ts)))
    if "--stills" not in sys.argv:
        print(render("S16", DURATION, draw_frame))
