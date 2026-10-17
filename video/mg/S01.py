"""Shot S01 (0:00.0-0:13.5, 13.5 s): a sourced fact, then the Ah Po hook. Voice from 3.0 s: "This is Ah Po,
going to see the Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead."

0-3.0 s: a silent fact title on plain navy, no badge and no map (public record, not illustration): "Golden Week
2025: crowd control lifted, then reimposed 45 minutes later." with its source footer. From 3.0 s the story: the
ILLUSTRATION badge and the "Illustrative story" line come in, the top-down schematic of the zone model draws in,
and Ah Po's wheelchair icon with its "Ah Po (阿婆, grandma)" tag sets off north from Av. de Almeida Ribeiro towards
the pin at Company of Jesus Square (the square below the Ruins; she is never put on the St. Paul's steps); then
her seated eye height: an armrest in the foreground, a wall of grey silhouettes swaying ahead; then a crane back
up to the map as Senado's disc goes amber to red.

Data sources (read here, never retyped):
  - docs/video/shotlist.json, shot S01: DURATION (end_s - start_s), the voice start ("voice from 3.0 s") and
    every on-screen line (fact title, footer, small line, tag, badge), asserted against the storyboard row in
    docs/video/script.md section 3 and, for the fact, against docs/research/brief-evidence.md section 1 row 3
    (the 4 Oct 2025 control times; the "45 minutes" is checked as 16:25 minus 15:40).
  - shared/zones.json (via ahpo.py): zone lat/lon (linear projection), the 7 links, has_stairs / steep
    (the hatched steps; her dotted step-free route Senado -> St. Dominic's -> Rua de S. Paulo -> Company of
    Jesus Square is found by search over links without stairs or steep sections), Chinese place names.
  - experiments/results/simulation_run/A_timeline.csv: senado_square true_density, the ONLY data on the map.
    Shot time is mapped onto sim 13:53-14:09 across the two map beats (SIM_KEYS); the colour is the recorded
    value as held, thresholded with shared/config.json congestion_thresholds (the dashboard's).
Ah Po, the dots and the silhouettes are illustrative choreography (badge ILLUSTRATION, from 3.0 s only).

Beats are keyed to the guide voice video/build/guide/S01.wav (say -v Daniel -r 155), laid 3.0 s into the shot
(ffmpeg silencedetect boundaries, word positions inside a clause from `say` prefix lengths); re-key them to the
real take. video/assemble.py must lay this shot's voice, captions and lower-third from 3.0 s (VOICE_START).

Outputs: video/build/mg/S01.mp4, video/build/mg/stills/S01_*.png
Run:  .venv/bin/python video/mg/S01.py            (stills and render)
      .venv/bin/python video/mg/S01.py --stills   (stills only)
"""
from __future__ import annotations

import json
import re
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
import ahpo  # noqa: E402
from ahpo import MapScene, EyeLevel, Cam, HOME, MAIN_PATH, POS, AHPO_S01_END, paste, text_sprite  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SHOT = "S01"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 13.5 s

# ---------- text: the shotlist's on-screen items, checked against the storyboard and the evidence brief ----------

_ITEMS = {}
for _it in _shot["on_screen_text"].split(" | "):
    _m = re.match(r"^([^:(]+?)(?: \(([^)]*)\))?: (.*)$", _it)
    assert _m, _it
    _ITEMS[_m.group(1)] = (_m.group(2) or "", _m.group(3))
FACT_TITLE = _ITEMS["Fact title"][1]
FOOTER = _ITEMS["Footer"][1]
SMALL = _ITEMS["Small grey"][1]
TAG = _ITEMS["Tag on her icon"][1]
BADGE = _ITEMS["Badge"][1]
assert BADGE == "ILLUSTRATION" and BADGE in BADGES, BADGE
assert SMALL.startswith("Illustrative story."), SMALL
assert TAG == "Ah Po (阿婆, grandma)", TAG

# the time windows in the shotlist: title and footer 0-3.0 s, small line and badge from 3.0 s, voice from 3.0 s
TITLE_END = 3.0
assert _ITEMS["Fact title"][0].startswith(f"0-{TITLE_END} s") and _ITEMS["Footer"][0] == f"0-{TITLE_END} s", _ITEMS
assert f"from {TITLE_END} s" in _ITEMS["Small grey"][0] and f"from {TITLE_END} s" in _ITEMS["Badge"][0], _ITEMS
VOICE_START = float(re.search(r"voice from ([\d.]+) s", _shot["visual"]).group(1))
assert VOICE_START == TITLE_END, VOICE_START

# the map's labels and the pin line are drawn by ahpo.py: they must still be the storyboard's
_labels = _ITEMS["Labels"][1]
for _zid, _en in ahpo.LABEL_EN.items():
    assert f"{ahpo.ZONES[_zid]['name_zh']} {_en}" in _labels, (_zid, _labels)
assert "pin: view of the Ruins from the square below" in _labels, _labels

# the same lines, verbatim, in the storyboard row (script.md section 3)
_row = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {SHOT} |"))
for _txt in (FACT_TITLE, FOOTER, SMALL, TAG):
    assert f'"{_txt}"' in _row, _txt

# the fact: the footer's times are the evidence brief's (section 1, row 3), and "45 minutes" is their gap
_m = re.fullmatch(r"(.+?), (\d+ \w+ \d{4}): control (\d\d:\d\d)-(\d\d:\d\d), again (\d\d:\d\d)-(\d\d:\d\d) · (.+), (\d+ \w+ \d{4})",
                  FOOTER)
assert _m, FOOTER
_brief = (ROOT / "docs" / "research" / "brief-evidence.md").read_text().replace("–", "-")
_row3 = next(l for l in _brief.splitlines() if l.startswith("| 3 |"))
assert f"{_m.group(2)}: {_m.group(1)} control ran {_m.group(3)}-{_m.group(4)}" in _row3, _row3
assert f"control ran again {_m.group(5)}-{_m.group(6)}" in _row3, _row3
assert "Macao Daily News, 2025-10-05" in _row3 and _m.group(7) == "Macao Daily News" and _m.group(8) == "5 Oct 2025"
_mins = lambda hhmm: int(hhmm[:2]) * 60 + int(hhmm[3:])  # noqa: E731
GAP_MIN = _mins(_m.group(5)) - _mins(_m.group(4))
assert f"reimposed {GAP_MIN} minutes later" in FACT_TITLE and "Golden Week 2025" in FACT_TITLE, (GAP_MIN, FACT_TITLE)
assert "dangerous" not in (FACT_TITLE + FOOTER).lower()

# ---------- beats ----------

# Shot seconds. Guide clauses (silencedetect, -35 dB, 0.08 s), + 3.0 s:
#   "This is Ah Po," 3.00-4.02 ("Ah Po" from 3.64) | "going to see the Ruins of St. Paul's." 4.23-6.54 ("the Ruins"
#   about 5.15-5.94, "of St. Paul's" 6.02) | "From her wheelchair," 6.80-7.75 | "she sees only backs," 7.97-9.29 |
#   "not the crowd building ahead." 9.51-10.89 (last voiced 10 ms frame; guide regenerated 17 Oct, 7.99 s file,
#   boundaries unchanged). The shot ends at 13.5 s.
# re-key to the real voice take
BEATS = {
    "title_in": 0.0,      # fact title: line 1 rises in, line 2 just after (both fully in by 0.27 s)
    "footer_in": 0.15,    # its source footer (fully in by 0.30 s)
    "accent": 0.45,       # amber underline grows under "45 minutes later." (done by 0.85 s)
    "title_out": 2.8,     # title and footer fade; gone by 2.95, before anything of the story appears
    "map_in": TITLE_END,  # 3.0: streets, steps and zone discs draw in; badge and "Illustrative story" line come in
    "voice": VOICE_START,  # "This is"
    "almeida_label": 3.4,
    "ahpo_in": 3.62,      # "Ah Po": her icon lands with a ring
    "tag_in": 3.85,       # "Po": the tag slides in
    "move": 4.25,         # "going": she sets off north
    "senado_label": 4.5,
    "route_hint": 4.7,    # "to see": her dotted step-free route draws towards the pin
    "pin": 5.2,           # "the Ruins": the pin drops at Company of Jesus Square
    "ruins_label": 5.35,
    "pin_label": 5.55,    # "view of the Ruins from the square below" (readable until the push-in at 6.8)
    "push_in": 6.8,       # "From her wheelchair": the camera pushes in on her ...
    "move_end": 6.95,
    "eye": 7.3,           # ... cross-fades and drops to her seated eye height ("wheelchair")
    "eye_push": 8.0,      # "she sees only backs": the wall closes in a little
    "crane": 9.45,        # "not the crowd building ahead": crane back up ...
    "map_back": 9.7,      # ... the map returns, zoomed on her, and pulls out
    "map_home": 10.65,
}
# Quick title fades (0.15 s) so the 13-word title and its footer are at full strength from 0.30 s to 2.80 s
# (2.5 s) for sound-off viewers, and the title is gone before the story starts at 3.0 s.
TITLE_FADE = 0.15
assert BEATS["title_out"] + TITLE_FADE < BEATS["map_in"]
# Shot time -> sim time across the two map beats (Senado's colour): beat 1 starts at the first recorded row,
# the eye-level beat skips ahead off screen, beat 2 ends at 14:09 (storyboard window 13:53-14:09). Senado
# crosses CRITICAL (14:08:09) at about 11.2 s, on the settled map after the last word, and holds red to the end.
SIM_KEYS = [(BEATS["map_in"], ahpo.senado_series()[0][0]), (7.5, ahpo.hms("14:02:00")),
            (BEATS["map_back"], ahpo.hms("14:05:30")), (11.7, ahpo.hms("14:09:00"))]


def sim_of(t: float) -> float:
    return ahpo.sim_clock(t, SIM_KEYS)


# the storyboard's "amber to red" must match the recorded data at both ends of the window
assert ahpo.state_of(ahpo.senado_density(SIM_KEYS[0][1])) == "WARNING", "Senado should start amber"
assert ahpo.state_of(ahpo.senado_density(SIM_KEYS[-1][1])) == "CRITICAL", "Senado should end red"
assert "WARNING" in ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[1][1]) and "CRITICAL" not in ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[2][1])

SCENE = MapScene()
EYE = EyeLevel()


# ---------- the fact title (0-3.0 s, plain navy) ----------

TITLE_SIZE = 74
_cut = FACT_TITLE.index(", then ") + 1
TITLE_L1, TITLE_L2 = FACT_TITLE[:_cut], FACT_TITLE[_cut + 1:]
ACCENT = f"{GAP_MIN} minutes later."
assert TITLE_L2.endswith(ACCENT) and f"{TITLE_L1} {TITLE_L2}" == FACT_TITLE
L2_HEAD = TITLE_L2[:-len(ACCENT)]


def _line2_sprite() -> Image.Image:
    a = text_sprite(L2_HEAD, TITLE_SIZE, 700, INK)
    b = text_sprite(ACCENT, TITLE_SIZE, 700, WARNING)
    off = int(round(text_font(L2_HEAD, TITLE_SIZE, 700).getlength(L2_HEAD)))
    img = Image.new("RGBA", (off + b.width, max(a.height, b.height)), (0, 0, 0, 0))
    img.alpha_composite(a, (0, 0))
    img.alpha_composite(b, (off, 0))
    return img


T1 = text_sprite(TITLE_L1, TITLE_SIZE, 700, INK)
T2 = _line2_sprite()
T_GAP = 96                                    # baseline-to-baseline (px)
T_TOP = 540 - 40 - (T_GAP + T1.height) / 2     # the block sits a little above centre
T1_XY = ((W - T1.width) / 2, T_TOP)
T2_XY = ((W - T2.width) / 2, T_TOP + T_GAP)
assert max(T1.width, T2.width) <= W - 2 * 140, (T1.width, T2.width)
_acc_x0 = T2_XY[0] + 2 + text_font(L2_HEAD, TITLE_SIZE, 700).getlength(L2_HEAD)
ACCENT_LINE = (_acc_x0, _acc_x0 + text_font(ACCENT, TITLE_SIZE, 700).getlength(ACCENT[:-1]))   # under the words, not the stop
ACCENT_Y = T2_XY[1] + T2.height + 10
assert text_size(FOOTER, 20, 500)[0] <= 1150, text_size(FOOTER, 20, 500)


def draw_title(img: Image.Image, t: float) -> None:
    out = 1 - progress(t, BEATS["title_out"], TITLE_FADE)
    if out <= 0:
        return
    for i, (spr, (x, y)) in enumerate(((T1, T1_XY), (T2, T2_XY))):
        k = progress(t, BEATS["title_in"] + 0.05 + 0.07 * i, TITLE_FADE)
        if k > 0:
            paste(img, spr, (x, y + 14 * (1 - k)), k * out)
    u = progress(t, BEATS["accent"], 0.4)
    if u > 0:
        x0, x1 = ACCENT_LINE
        rounded(img, (x0, ACCENT_Y, lerp(x0, x1, u), ACCENT_Y + 5), 2, fill=WARNING, alpha=0.9 * out)
    footer(img, FOOTER, progress(t, BEATS["footer_in"], TITLE_FADE) * out)


# ---------- Ah Po's tag: "Ah Po (阿婆, grandma)" on two lines ----------
# ahpo.MapScene draws a one-line "Ah Po" tag in Geist only (no Chinese glyphs), so S01 hides it and draws this
# one in the same place: left of her icon, sliding in from it. Two lines keep it narrow: as one line its left
# end would run under the speaker lower-third (x 60-739, y 800-890), which video/assemble.py shows for 3 s from the
# voice start (3.0 s) while she is beside Almeida.

TAG_L1, TAG_L2 = TAG.split(" ", 2)[0] + " " + TAG.split(" ", 2)[1], TAG.split(" ", 2)[2]   # "Ah Po" / "(阿婆, grandma)"
assert f"{TAG_L1} {TAG_L2}" == TAG and TAG_L1 == "Ah Po", (TAG_L1, TAG_L2)
SS2 = 2


def _runs(text: str) -> list[str]:
    """Splits text into runs of Chinese and non-Chinese characters (each run gets its own font)."""
    return [r for r in re.split(r"([\u2e80-\u9fff\uf900-\ufaff]+)", text) if r]


def _tag_sprite() -> Image.Image:
    lines = [(TAG_L1, 22, 700), (TAG_L2, 18, 650)]
    widths = [sum(text_font(r, s * SS2, wt).getlength(r) for r in _runs(tx)) for tx, s, wt in lines]
    pad_x, top, pitch, bottom = 10 * SS2, 21 * SS2, 22 * SS2, 10 * SS2       # baselines at top and top + pitch
    w_, h_ = int(max(widths) + 2 * pad_x), int(top + pitch + bottom)
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w_ - 1, h_ - 1), 15 * SS2, fill=(*WARNING, 255))
    for i, ((tx, s, wt), wd) in enumerate(zip(lines, widths)):
        x, y = (w_ - wd) / 2, top + i * pitch
        for r in _runs(tx):
            f = text_font(r, s * SS2, wt)
            d.text((x, y), r, font=f, fill=(*NAVY, 255), anchor="ls")
            x += f.getlength(r)
    return img.reduce(SS2)


TAG_SPRITE = _tag_sprite()
TAG_GAP = 7          # between the tag and her icon's outline (px)


def tag_box(p, r: float, k: float) -> tuple[float, float]:
    """Top-left of the tag for her icon at p (screen px) with radius r; k = 0..1 slide-in."""
    return p[0] - r - TAG_GAP - TAG_SPRITE.width + (1 - k) * 10, p[1] - TAG_SPRITE.height / 2


# the tag clears the speaker lower-third that video/assemble.py lays over this shot (its own SPEAKER entry, drawn
# with style.lower_third), from where she starts to where she stops
sys.path.insert(0, str(ROOT / "video"))
from assemble import SPEAKER, VOICE_START as _ASM_VOICE_START  # noqa: E402
_lt = transparent()
lower_third(_lt, *SPEAKER[SHOT])
LT_BOX = _lt.getbbox()                                        # (60, 800, 739, 890) for [MEMBER 4]
for _s in (0.0, AHPO_S01_END):
    _x, _y = tag_box(MAIN_PATH.at(_s), 21, 1.0)
    assert _x >= LT_BOX[2] + 12 or _y + TAG_SPRITE.height <= LT_BOX[1] - 8, (_s, _x, _y, LT_BOX)


# ---------- the map beats ----------

EDGE_ORDER = ["e_senado_almeida", "e_tercena_almeida", "e_dominic_senado", "e_ruasp_tercena",
              "e_ruasp_dominic", "e_jesus_ruasp", "e_ruins_jesus"]
ZONE_ORDER = ["almeida_ribeiro", "tercena_corridor", "st_dominic", "rua_sao_paulo", "jesus_square", "ruins_st_paul"]


def draw_in_state(t: float) -> dict | None:
    t0 = BEATS["map_in"]
    if t >= t0 + 1.2:
        return None
    din = {}
    for i, eid in enumerate(EDGE_ORDER):
        din[eid] = progress(t, t0 + 0.07 * i, 0.5)
    for i, zid in enumerate(ZONE_ORDER):
        din[zid] = progress(t, t0 + 0.12 + 0.08 * i, 0.35)
    din["stairs_icon"] = progress(t, t0 + 0.75, 0.3)
    return din


def ahpo_s(t: float) -> float:
    """Her distance along the main route (1x px): she rolls north from Almeida and stops short of Senado's crowd."""
    k = clamp((t - BEATS["move"]) / (BEATS["move_end"] - BEATS["move"]))
    k = k * k * (3 - 2 * k)                       # smoothstep: gentle start and stop
    return AHPO_S01_END * k


_CAM_SWITCH = (BEATS["eye"] + 0.45 + BEATS["map_back"] - 0.1) / 2   # map hidden here: push-in done, pull-out not begun


def map_cam(t: float) -> Cam:
    """Home framing, except the push-in on Ah Po before eye level and the pull-out after it."""
    p = MAIN_PATH.at(ahpo_s(t))
    k_in = progress(t, BEATS["push_in"], BEATS["eye"] + 0.45 - BEATS["push_in"])
    k_out = 1 - progress(t, BEATS["map_back"] - 0.1, BEATS["map_home"] - BEATS["map_back"] + 0.1)
    k = k_in if t < _CAM_SWITCH else k_out
    if k <= 1e-4:
        return HOME
    zoom = lerp(1.0, 3.4, k)
    anchor = lerp(p, (W / 2, H * 0.56), k)
    return Cam(zoom, p, anchor)


def map_frame(t: float) -> Image.Image:
    cam = map_cam(t)
    sim = sim_of(t)
    s_her = ahpo_s(t)
    labels = {"almeida_ribeiro": progress(t, BEATS["almeida_label"], 0.4),
              "senado_square": progress(t, BEATS["senado_label"], 0.4),
              "ruins_st_paul": progress(t, BEATS["ruins_label"], 0.4)}
    zoomed = 0.0 if cam.home else clamp((cam.zoom - 1) / 0.3)    # labels and tag are gone before the push carries them off frame
    label_fade = 1 - zoomed
    route_k = progress(t, BEATS["route_hint"], 1.3)
    route = None
    if route_k > 0:
        s1 = s_her + (MAIN_PATH.length - s_her) * route_k
        route = {"s0": s_her + 26, "s1": s1, "style": "dotted", "alpha": 0.55 * label_fade, "phase": 0.0}
    pin_k = progress(t, BEATS["pin"], 0.5)
    ahpo_a = progress(t, BEATS["ahpo_in"], 0.35)
    ahpo_scale = lerp(0.6, 1.0, progress(t, BEATS["ahpo_in"], 0.45))
    img = SCENE.render(
        t, cam,
        draw_in=draw_in_state(t),
        senado_col=ahpo.senado_colour(t, sim_of),
        senado_dens=ahpo.senado_density_smooth(sim),
        senado_alpha=progress(t, BEATS["map_in"] + 0.35, 0.4),
        dots_alpha=progress(t, BEATS["map_in"] + 0.6, 0.6),
        labels=labels,
        pin=(pin_k, -36 * (1 - pin_k)) if pin_k > 0 else None,
        pin_label_alpha=progress(t, BEATS["pin_label"], 0.4),
        ahpo={"p": MAIN_PATH.at(s_her), "alpha": ahpo_a, "scale": ahpo_scale,
              "ring": clamp((t - BEATS["ahpo_in"] - 0.05) / 0.9) if t < BEATS["ahpo_in"] + 0.95 else 0.0,
              "tag": 0.0},                       # S01 draws its own two-line tag (below)
        route=route,
        label_fade=label_fade,
    ).convert("RGBA")
    ta = progress(t, BEATS["tag_in"], 0.35) * label_fade * (1.0 if ahpo_a >= 0.999 else ahpo_a)
    if ta > 0:
        r = 21 * cam.zoom ** 0.6 * ahpo_scale
        paste(img, TAG_SPRITE, tag_box(cam(MAIN_PATH.at(s_her)), r, ta), ta)
    # the map comes up from plain navy (the title beat has no map paper)
    k = progress(t, BEATS["map_in"], 0.35)
    if k < 0.999:
        img = Image.blend(canvas(NAVY).convert("RGBA"), img, k)
    return img


# ---------- the eye-level beat ----------

def eye_frame(t: float) -> Image.Image:
    drop = progress(t, BEATS["eye"] - 0.05, 0.95)                   # camera drops to seated height
    rise = progress(t, BEATS["crane"], 0.75)                        # and cranes back up
    crowd_dy = lerp(230, 0, drop) + lerp(0, 270, rise)
    arm_dy = lerp(360, 0, progress(t, BEATS["eye"] + 0.1, 0.8)) + lerp(0, 420, progress(t, BEATS["crane"] - 0.05, 0.6))
    push = lerp(1.0, 1.05, progress(t, BEATS["eye_push"], 1.4))      # the wall of backs closes in a little
    return EYE.frame(t, crowd_dy=crowd_dy, arm_dy=arm_dy, push=push).convert("RGBA")


def eye_mix(t: float) -> float:
    """0 = map, 1 = eye level."""
    return progress(t, BEATS["eye"], 0.4) * (1 - progress(t, BEATS["map_back"], 0.4))


# scrims over the silhouettes: bottom, so the small line stays legible; top, so the badge keeps its contrast
# over the grey heads
_SCRIM = np.zeros((H, W, 4), np.uint8)
_SCRIM[..., :3] = NAVY
_ys = np.arange(H, dtype=np.float32)
_SCRIM[..., 3] = (np.maximum(np.clip((_ys - 960) / 70, 0, 1) * 225,
                             np.clip((150 - _ys) / 110, 0, 1) * 175)).astype(np.uint8)[:, None]
SCRIM = Image.fromarray(_SCRIM, "RGBA")


# ---------- overlays (from 3.0 s only: never over the fact title) ----------

SMALL_LINES = wrap(SMALL, 20, 500, 1100)
assert len(SMALL_LINES) <= 2


def draw_overlays(img: Image.Image, t: float) -> None:
    a = progress(t, BEATS["map_in"], 0.45)
    for i, ln in enumerate(SMALL_LINES):
        draw_text(img, (60, 1006 + i * 28), ln, 20, 500, INK_2, a)
    badge(img, BADGE, alpha=progress(t, BEATS["map_in"], 0.45))


# ---------- frame ----------

TITLE_BG = canvas(NAVY).convert("RGBA")


def draw_frame(t: float) -> Image.Image:
    if t < BEATS["map_in"]:
        img = TITLE_BG.copy()                     # plain navy: no map, no badge, no story line
        draw_title(img, t)
        return img
    eye_k = eye_mix(t)
    if eye_k >= 0.999:
        img = eye_frame(t)
    elif eye_k <= 0.001:
        img = map_frame(t)
    else:
        img = Image.blend(map_frame(t), eye_frame(t), eye_k)
    if eye_k > 0:
        paste(img, SCRIM, (0, 0), eye_k)
    draw_overlays(img, t)
    return img


STILLS = {"title_in": 0.3, "title": 1.6, "title_late": 2.79, "story_in": 3.3, "tag": 4.4, "walk": 5.9, "pin": 6.6, "eye": 8.6, "crane": 10.0,
          "red": 12.0, "end": DURATION - 1 / FPS}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        still(f"{SHOT}_{name}", draw_frame(ts))
    print("Senado state by sim time:", [(ahpo.clock(s), v, ahpo.state_of(v)) for s, v in ahpo._change_points() if s <= SIM_KEYS[-1][1] + 60])
    crit = next(t / 100 for t in range(int(SIM_KEYS[0][0] * 100), int(DURATION * 100))
                if ahpo.state_of(ahpo.senado_density(sim_of(t / 100))) == "CRITICAL")
    print(f"Senado turns CRITICAL at shot {crit:.2f} s; tag {TAG_SPRITE.size}; title widths {T1.width}, {T2.width}")
    if _ASM_VOICE_START.get(SHOT, 0.2) != VOICE_START:
        print(f"WARNING: video/assemble.py VOICE_START[{SHOT!r}] is {_ASM_VOICE_START.get(SHOT, 0.2)}, the storyboard says {VOICE_START}: "
              "the voice, captions and lower-third would start over the fact title")
    if "--stills" not in sys.argv:
        print(render(SHOT, DURATION, draw_frame))
