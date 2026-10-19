"""Shot S18 (4:21.5-4:28.5, 7.0 s): back to Mrs Chan. "Back to Mrs Chan. The system flags the risk; staff check her
route and stay beside her."

The system flags, people act. The shot opens on S01's last frame (same map and framing, ahpo.py: her icon stopped
short of Senado on her main route, Senado red, her dotted route to the pin, the place labels and her tag); the place
labels fade and an amber ring pulses on her; a red ring pulses from Senado and a short "Risk flagged" marker takes
Senado's label's place; a staff icon (hi-vis vest) walks up from Av. de Almeida Ribeiro to her side while her route
north turns into marching dashes in the vest colour, labelled "staff check" (being checked, never shown as cleared);
the staff member stays beside her to the end. No approval stamp, no detour, no notice board: the video says that 24
of 40 simulated wheelchair users had no step-free route (S15), so the ending must not read as the accessibility
problem solved. Senado stays red (CRITICAL) throughout, and she does not move on through its crowd.

Data sources (read here, never retyped):
  - docs/video/shotlist.json, shot S18: DURATION (end_s - start_s) and the on-screen items (the marker, the label,
    the badge), asserted against the storyboard row in docs/video/script.md section 3.
  - shared/zones.json (via ahpo.py): projection, links, her step-free main route (as in S01).
  - experiments/results/simulation_run/A_timeline.csv + A_events.json: shot time is mapped onto run A from the sim
    time S01 ends on (the last of S01.py's SIM_KEYS, read from its source: 14:09:00) to the end of the run (14:40);
    Senado's colour is its recorded true_density, thresholded with shared/config.json, and the script asserts it is
    CRITICAL for the whole window (it ended at 0.75) and that run A had flagged Senado (its CRITICAL forecast, 14:08)
    before the window starts.
Mrs Chan, the staff member, the check line and the dots are illustrative choreography (badge ILLUSTRATION).

Outputs: video/build/mg/S18.mp4, video/build/mg/stills/S18_*.png
Run:  .venv/bin/python video/mg/S18.py            (stills and render)
      .venv/bin/python video/mg/S18.py --stills   (stills only)
"""
from __future__ import annotations

import json
import math
import re
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
import ahpo  # noqa: E402
from ahpo import MapScene, HOME, MAIN_PATH, POS, AHPO_S01_END, VEST, paste  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

SHOT = "S18"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 7.0 s

# ---------- text: the shotlist's on-screen items, checked against the storyboard ----------

_ITEMS = {}
for _it in _shot["on_screen_text"].split(" | "):
    _m = re.match(r"^([^:(]+?)(?: \(([^)]*)\))?: (.*)$", _it)
    assert _m, _it
    _ITEMS[_m.group(1)] = (_m.group(2) or "", _m.group(3))
MARKER = _ITEMS["Marker at Senado"][1]                 # "Risk flagged"
LABEL = _ITEMS["Label beside her route"][1]           # "staff check"
BADGE = _ITEMS["Badge"][1]
assert BADGE == "ILLUSTRATION" and BADGE in BADGES, BADGE
assert len(_ITEMS) == 3, _ITEMS                        # the badge plus at most two short labels (declutter rule 1)
for _txt in (MARKER, LABEL):
    assert len(_txt.split()) <= 6, _txt
# the ending must not read as "solved": no approval, all-clear or open-route wording on screen
assert not re.search(r"approv|safe|clear|open|solved", f"{MARKER} {LABEL}".lower()), (MARKER, LABEL)
# each label comes in on the words its item names, and those words are in the narration
_CUES = {k: re.fullmatch(r"from '([^']+)'", _ITEMS[k][0]).group(1) for k in ("Marker at Senado", "Label beside her route")}
assert all(c in _shot["narration"] for c in _CUES.values()), (_CUES, _shot["narration"])
# the same lines, verbatim, in the storyboard row (script.md section 3)
_row = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {SHOT} |"))
for _txt in (MARKER, LABEL):
    assert f'"{_txt}"' in _row, _txt
assert ahpo.NAME == "Mrs Chan" and ahpo.NAME in _shot["narration"]

# ---------- beats ----------

# Beats in seconds from the shot start, keyed to the robot guide voice (video/build/guide/S18.wav, laid 0.2 s into the
# shot by assemble.py). Clause boundaries from
#   ffmpeg -i video/build/guide/S18.wav -af silencedetect=noise=-35dB:d=0.08 -f null -
# (speech 0.00-1.30 | 1.54-3.09 | 3.33-5.84), each + 0.2 s; words inside a clause from the length of
# `say -v Daniel -r 155` on the words before them and the level dips between words:
# "Back to Mrs (0.95) Chan." 0.2-1.5 | "The system (1.74-2.36) flags (2.36-2.68) the risk;" (-3.29) |
# "staff (3.53) check (3.92) her route (4.2-4.85) and stay (5.1) beside her." (-6.04)
# re-key to the real voice take
BEATS = {
    "labels_out": 0.35,   # the place labels carried over from S01's last frame fade (gone by 0.85)
    "ring": 0.95,         # "Mrs Chan": an amber ring pulses out from her icon
    "tag_out": 1.6,       # her "Mrs Chan" tag (from S01) fades once her name has been said (gone by 1.9)
    "flag": 2.36,         # "flags": a red ring pulses from Senado; its label gives way to the "Risk flagged" marker
    "staff": 3.53,        # "staff": the staff member steps out at Av. de Almeida Ribeiro and walks up to her side ...
    "staff_at": 4.6,      # ... reaching her on "her route"
    "check": 3.92,        # "check her route": her route north turns into marching vest-colour dashes (drawn by 4.85)
    "check_label": 4.0,   # ... and the "staff check" label comes in beside it
    "stay": 5.1,          # "stay beside her": a vest ring pulses around the staff member, who stays at her side to the end
}
assert BEATS["check"] + 0.93 <= 4.85 + 1e-9 and BEATS["staff_at"] <= 4.85

# Shot time -> run A sim time: from where S01 ends (the last of its SIM_KEYS, so the cut has no jump in Senado's
# crowd) to the end of the run.
_s01_keys = re.search(r"^SIM_KEYS = \[(.*?)\]\n", (Path(__file__).resolve().parent / "S01.py").read_text(), re.S | re.M)
assert _s01_keys, "S01.py has no SIM_KEYS"
S01_END_SIM = ahpo.hms(re.findall(r'ahpo\.hms\("([\d:]+)"\)', _s01_keys.group(1))[-1])     # 14:09:00
SIM_KEYS = [(0.0, S01_END_SIM), (DURATION, ahpo.end_sim())]                                  # 14:09 -> 14:40


def sim_of(t: float) -> float:
    return ahpo.sim_clock(t, SIM_KEYS)


# Senado never turns green or amber here: the recorded true_density stays above CRITICAL to the end of the run
assert ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[-1][1]) == {"CRITICAL"}, ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[-1][1])
# "The system flags the risk": run A's CRITICAL forecast for Senado came before the window this shot shows
_FLAG_SIM = ahpo.hms(next(e for e in ahpo.run_a_events() if e.get("event") == "senado_critical_forecast")["sim_time"])
assert _FLAG_SIM <= SIM_KEYS[0][1], (ahpo.clock(_FLAG_SIM), ahpo.clock(SIM_KEYS[0][1]))

SCENE = MapScene()
# the scene's own clock (drifting dots, Senado's pulse) runs on from S01's last frame, so nothing jumps at the cut
_s01 = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == "S01")
SCENE_T0 = round(_s01["end_s"] - _s01["start_s"], 3)                                         # 11.0 s

# ---------- Mrs Chan (stopped where S01 left her) and the staff member ----------

P_HER = MAIN_PATH.at(AHPO_S01_END)
R_MARK = 21                                    # marker radius (1x), hers and the staff member's
_dx, _dy = MAIN_PATH.direction(AHPO_S01_END)
STAFF_AT = (P_HER[0] - _dy * 46, P_HER[1] + _dx * 46)   # on her right-hand side on screen, 46 px from her centre
STAFF_FROM = POS["almeida_ribeiro"]
STAFF_VIA = (1000.0, 880.0)                     # the walk bows south-east, clear of her icon


def staff_state(t: float) -> dict | None:
    a = progress(t, BEATS["staff"], 0.35)
    if a <= 0:
        return None
    k = progress(t, BEATS["staff"] + 0.07, BEATS["staff_at"] - BEATS["staff"] - 0.07)
    p = tuple((1 - k) ** 2 * f + 2 * (1 - k) * k * v + k * k * e for f, v, e in zip(STAFF_FROM, STAFF_VIA, STAFF_AT))
    return {"p": p, "alpha": a, "scale": lerp(0.7, 1.0, a) * R_MARK / 18}


# the walk never covers her icon (both markers about 21 px, plus their glow)
assert min(math.dist(P_HER, staff_state(BEATS["staff"] + i / 50)["p"]) for i in range(1, 80)) >= 2 * R_MARK + 2

TAG_SPRITE = ahpo.tag_sprite(ahpo.NAME).reduce(ahpo.SS)
TAG_GAP = 7          # between the tag and her icon's outline (px), as S01 draws it


def tag_alpha(t: float) -> float:
    return 1 - progress(t, BEATS["tag_out"], 0.3)


# ---------- her route, as staff check it ----------

ROUTE_S0 = AHPO_S01_END + 26                     # S01's dotted route starts 26 px ahead of her
DOTTED_ALPHA = 0.55                              # as S01 draws it at its end


def routes(t: float) -> list[dict]:
    """S01's dotted route ahead of the check line's head; behind it, marching dashes in the vest colour."""
    k = progress(t, BEATS["check"], 0.93)
    head = ROUTE_S0 + (MAIN_PATH.length - ROUTE_S0) * k
    out = []
    if head < MAIN_PATH.length - 1:
        s0 = ROUTE_S0 if k <= 0 else max(ROUTE_S0, head + 8)
        # phase: the dots stay where S01 put them while the head eats into them
        out.append({"s0": s0, "s1": MAIN_PATH.length, "style": "dotted", "alpha": DOTTED_ALPHA, "phase": ROUTE_S0 - s0})
    if k > 0:
        out.append({"s0": ROUTE_S0, "s1": head, "style": "dashed", "colour": VEST, "alpha": 0.95, "phase": 30.0 * t})
    return out


# the "staff check" label sits right of the route's St. Dominic's -> Rua de S. Paulo leg, at y 500
_a, _b = POS["st_dominic"], POS["rua_sao_paulo"]
LABEL_Y = 500
LABEL_X = _a[0] + (_b[0] - _a[0]) * (_a[1] - LABEL_Y) / (_a[1] - _b[1]) + 30
LABEL_SIZE = 28


def label_alpha(t: float) -> float:
    return progress(t, BEATS["check_label"], 0.35)


# ---------- the "Risk flagged" marker and the rings ----------

SENADO = POS["senado_square"]
MARK_X = SENADO[0] + ahpo.SENADO_R + ahpo.LABEL_DX["senado_square"]   # where Senado's label starts
MARK_SIZE, MARK_H, MARK_PAD = 26, 42, 18
MARK_W = text_size(MARKER, MARK_SIZE, 700)[0] + 2 * MARK_PAD


def senado_label_alpha(t: float) -> float:
    return 1 - progress(t, BEATS["flag"] - 0.05, 0.2)


def marker_alpha(t: float) -> float:
    return progress(t, BEATS["flag"] + 0.1, 0.3)


def draw_marker(img: Image.Image, t: float) -> None:
    k = marker_alpha(t)
    if k <= 0:
        return
    x0 = MARK_X - 14 * (1 - k)
    y0 = SENADO[1] - MARK_H / 2
    rounded(img, (x0, y0, x0 + MARK_W, y0 + MARK_H), MARK_H // 2, fill=CRITICAL, alpha=k)
    draw_text(img, (x0 + MARK_W / 2, y0 + MARK_H / 2 + 1), MARKER, MARK_SIZE, 700, NAVY, k, anchor="mm")


def rings(img: Image.Image, t: float) -> None:
    """Expanding outline rings, drawn at 2x and reduced: red from Senado on "flags", vest around the staff on "stay"."""
    q = 2
    todo = []
    for t0 in (BEATS["flag"], BEATS["flag"] + 0.4):
        k = clamp((t - t0) / 0.8)
        if 0 < k < 1:
            todo.append((SENADO, ahpo.SENADO_R + 6 + 70 * ease(k), CRITICAL, 0.9 * (1 - k)))
    st = staff_state(t)
    k = clamp((t - BEATS["stay"]) / 0.8)
    if st and 0 < k < 1:
        todo.append((st["p"], R_MARK + 4 + 34 * ease(k), VEST, 0.8 * (1 - k)))
    if not todo:
        return
    xs = [c[0] for c, *_ in todo]
    ys = [c[1] for c, *_ in todo]
    pad = 120
    ox, oy = int(min(xs) - pad), int(min(ys) - pad)
    lay = Image.new("RGBA", (int(max(xs) - min(xs) + 2 * pad) * q, int(max(ys) - min(ys) + 2 * pad) * q), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for (cx, cy), r, col, a in todo:
        x, y = (cx - ox) * q, (cy - oy) * q
        d.ellipse((x - r * q, y - r * q, x + r * q, y + r * q), outline=(*col, int(255 * a)), width=3 * q)
    lay = lay.resize((lay.width // q, lay.height // q), Image.LANCZOS)
    img.alpha_composite(lay, (ox, oy))


# ---------- what is on screen, and for how long ----------

def texts_on(t: float) -> list[str]:
    """Text elements on screen at t besides the badge (and the captions, added at assembly)."""
    on = []
    if 1 - progress(t, BEATS["labels_out"], 0.5) > 0.01:
        on += ["Almeida label", "Ruins label"]
    if senado_label_alpha(t) > 0.01:
        on.append("Senado label")
    if tag_alpha(t) > 0.01:
        on.append("tag")
    if marker_alpha(t) > 0.01:
        on.append(MARKER)
    if label_alpha(t) > 0.01:
        on.append(LABEL)
    return on


# Declutter rule 1: once S01's labels have faded, at most two text elements at a time; rule 5: each label stays at
# least 0.3 s per word + 0.5 s
_T_CLEAR = BEATS["labels_out"] + 0.5
assert all(len(texts_on(i / FPS)) <= 2 for i in range(int(_T_CLEAR * FPS) + 1, int(DURATION * FPS))), \
    [(i / FPS, texts_on(i / FPS)) for i in range(int(DURATION * FPS)) if len(texts_on(i / FPS)) > 2][:3]
for _txt, _t0 in ((MARKER, BEATS["flag"] + 0.4), (LABEL, BEATS["check_label"] + 0.35)):
    assert DURATION - _t0 >= 0.3 * len(_txt.split()) + 0.5, (_txt, DURATION - _t0)
# both labels clear the caption band (y 920-990) and the badge
assert SENADO[1] + MARK_H / 2 < 900 and LABEL_Y + LABEL_SIZE < 900 and MARK_X + MARK_W < 1600


# ---------- frame ----------

def draw_frame(t: float) -> Image.Image:
    sim = sim_of(t)
    la = 1 - progress(t, BEATS["labels_out"], 0.5)
    img = SCENE.render(
        SCENE_T0 + t, HOME,
        senado_col=ahpo.senado_colour(t, sim_of),
        senado_dens=ahpo.senado_density_smooth(sim),
        dots_alpha=1.0 - 0.25 * progress(t, BEATS["check"], 0.9),      # a little quieter while her route is checked
        labels={"almeida_ribeiro": la, "ruins_st_paul": la, "senado_square": senado_label_alpha(t)},
        pin=(1.0, 0.0),                                                  # no pin label, as in S01 (19 Oct)
        ahpo={"p": P_HER, "alpha": 1.0, "tag": 0.0,                     # the tag is drawn below, where S01 draws it
              "ring": clamp((t - BEATS["ring"]) / 0.9) if BEATS["ring"] < t < BEATS["ring"] + 0.9 else 0.0},
        staff=staff_state(t),
        route=routes(t),
    ).convert("RGBA")
    ta = tag_alpha(t)
    if ta > 0:
        paste(img, TAG_SPRITE, (P_HER[0] - R_MARK - TAG_GAP - TAG_SPRITE.width, P_HER[1] - TAG_SPRITE.height / 2), ta)
    rings(img, t)
    draw_marker(img, t)
    k = label_alpha(t)
    if k > 0:
        draw_text(img, (LABEL_X + 10 * (1 - k), LABEL_Y), LABEL, LABEL_SIZE, 600, VEST, k, anchor="lm")
    badge(img, BADGE)
    return img


STILLS = {"start": 0.0, "tag": 1.3, "flag": 2.9, "check": 4.5, "stay": 5.4, "end": DURATION - 1 / FPS}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        still(f"{SHOT}_{name}", draw_frame(ts))
    print("text elements on screen:", {n: texts_on(ts) for n, ts in STILLS.items()})
    print(f"sim {ahpo.clock(SIM_KEYS[0][1])} -> {ahpo.clock(SIM_KEYS[-1][1])}; Senado flagged {ahpo.clock(_FLAG_SIM)}")
    if "--stills" not in sys.argv:
        print(render(SHOT, DURATION, draw_frame))
