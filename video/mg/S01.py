"""Shot S01 (0:00.0-0:12.0, 12.0 s): the Mrs Chan hook. Voice from 0.2 s: "This is Mrs Chan, going to see the
Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead."

The shot opens straight on the map (no title; since 19 Oct the 3 s fact title and its footer are gone, so the voice
starts at once): the top-down schematic of the zone model draws in under the ILLUSTRATION badge, and Mrs Chan's
wheelchair icon with its "Mrs Chan" tag sets off north from Av. de Almeida Ribeiro towards the pin at Company of
Jesus Square (the square below the Ruins; she is never put on the St. Paul's steps); then her seated eye height: an
armrest in the foreground, a wall of grey silhouettes swaying ahead; then a crane back up to the map as Senado's
disc goes amber to red. Map labels only for the three places the story needs (the Ruins, Senado, Almeida); no pin
label and no small "Illustrative story" line (the badge carries it, and S06's voice says "Mrs Chan is made up").
After the voice (8.55-11.85 s, the second review of 19 Oct) the real event the old title card carried comes back as
a short overlay over the settled map, Senado red: a two-line fact ("Crowd control lifted, reimposed 45 minutes
later") and its source, on the empty left half of the frame, bridging into S06's "Mrs Chan is made up. The crowds
are not." It is two text elements, so the three place labels and her tag dim while it shows (declutter rule 1) and
are back before the last frame: S18 opens on this shot's final map state, so the overlay is gone by 11.85 s.

Data sources (read here, never retyped):
  - docs/video/shotlist.json, shot S01: DURATION (end_s - start_s) and every on-screen line (labels, tag, badge,
    the fact line and its source), asserted against the storyboard row in docs/video/script.md section 3. The
    voice start is video/assemble.py's (VOICE_START, the default 0.2 s for this shot).
  - docs/research/brief-evidence.md, section 1, row 3: the two crowd-control windows on Rua de S. Paulo, 4 Oct 2025
    (13:00-15:40, again 16:25-17:25), whose gap is the fact line's "45 minutes" (asserted below).
  - shared/zones.json (via ahpo.py): zone lat/lon (linear projection), the 7 links, has_stairs / steep
    (the hatched steps; her dotted step-free route Senado -> St. Dominic's -> Rua de S. Paulo -> Company of
    Jesus Square is found by search over links without stairs or steep sections), Chinese place names.
  - experiments/results/simulation_run/A_timeline.csv: senado_square true_density, the ONLY data on the map.
    Shot time is mapped onto sim 13:53-14:09 across the two map beats (SIM_KEYS); the colour is the recorded
    value as held, thresholded with shared/config.json congestion_thresholds (the dashboard's).
Mrs Chan, the dots and the silhouettes are illustrative choreography (badge ILLUSTRATION, from the first frame).

Beats are keyed to the guide voice video/build/guide/S01.wav (say -v Daniel -r 155), laid 0.2 s into the shot
(ffmpeg silencedetect boundaries, word positions inside a clause from `say` prefix lengths); re-key them to the
real take.

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
from ahpo import MapScene, EyeLevel, Cam, HOME, MAIN_PATH, POS, AHPO_S01_END, paste  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

SHOT = "S01"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 12.0 s
assert DURATION == 12.0, DURATION                                # 11.0 -> 12.0 s in the second review (19 Oct)

# ---------- text: the shotlist's on-screen items, checked against the storyboard ----------

_ITEMS = {}
for _it in _shot["on_screen_text"].split(" | "):
    _m = re.match(r"^([^:(]+?)(?: \(([^)]*)\))?: (.*)$", _it)
    assert _m, _it
    _ITEMS[_m.group(1)] = (_m.group(2) or "", _m.group(3))
# 19 Oct declutter: labels, her tag and the badge (no fact title, footer, small line or pin label); second review:
# the fact line and its source, after the voice
assert set(_ITEMS) == {"Labels", "Tag on her icon", "Badge", "Fact line", "Source"}, sorted(_ITEMS)
TAG = _ITEMS["Tag on her icon"][1]
BADGE = _ITEMS["Badge"][1]
assert BADGE == "ILLUSTRATION" and BADGE in BADGES, BADGE
assert "from 0 s" in _ITEMS["Badge"][0], _ITEMS["Badge"]          # the story is labelled from its first frame
assert TAG == "Mrs Chan", TAG
FACT = _ITEMS["Fact line"][1]                                      # "Crowd control lifted, reimposed 45 minutes later"
SOURCE = _ITEMS["Source"][1]                                       # "Golden Week 2025 · Macao Daily News"
def n_words(text: str) -> int:
    """Words for the reading rule: tokens with a letter or digit (the "·" separator is not one)."""
    return sum(any(c.isalnum() for c in w) for w in text.split())


assert n_words(FACT) <= 10 and n_words(SOURCE) <= 6, (FACT, SOURCE)   # declutter: short line, ~6-word source
assert "Macao Daily News" in SOURCE and "2025" in SOURCE, SOURCE   # an outside fact wears its source and its year
for _w in ("dangerous", "crush", "partner"):                       # honesty rules, script.md section 6
    assert _w not in (FACT + SOURCE).lower(), (FACT, SOURCE)

# the fact must be brief-evidence.md section 1, row 3 (4 Oct 2025: control 13:00-15:40, then again 16:25-17:25):
# the "45 minutes" is the gap between the two windows, read from that row, never retyped
_ev = (ROOT / "docs" / "research" / "brief-evidence.md").read_text()
_sec1 = _ev.split("\n## 1. ")[1].split("\n## ")[0]
_row3 = next(l for l in _sec1.splitlines() if l.startswith("| 3 |"))
_cells = [c.strip() for c in _row3.strip().strip("|").split("|")]
assert "4 Oct 2025" in _cells[2] and "Macao Daily News, 2025-10-05" in _cells[3], _row3
_wins = re.findall(r"(\d\d):(\d\d)[–-](\d\d):(\d\d)", _cells[2].split("19 Feb")[0])   # the 4 Oct 2025 windows only
assert len(_wins) == 2, _wins
_gap_min = (int(_wins[1][0]) * 60 + int(_wins[1][1])) - (int(_wins[0][2]) * 60 + int(_wins[0][3]))   # 16:25 - 15:40
assert _gap_min == 45 and f"{_gap_min} minutes" in FACT, (_wins, _gap_min, FACT)

# the voice starts where video/assemble.py lays it (no title any more: its default, 0.2 s)
sys.path.insert(0, str(ROOT / "video"))
from assemble import SPEAKER, VOICE_START as _ASM_VOICE_START  # noqa: E402
VOICE_START = _ASM_VOICE_START.get(SHOT, 0.2)
assert VOICE_START == 0.2, VOICE_START
assert "voice from 3.0 s" not in _shot["visual"], "the shotlist still describes the old title beat"

# the map's labels are drawn by ahpo.py: they must still be the storyboard's, and only those three
_labels = _ITEMS["Labels"][1]
for _zid, _en in ahpo.LABEL_EN.items():
    assert f"{ahpo.ZONES[_zid]['name_zh']} {_en}" in _labels, (_zid, _labels)
assert _labels.count(" · ") == len(ahpo.LABEL_EN) - 1 and "pin" not in _labels, _labels

# the same lines in the storyboard row (script.md section 3)
_row = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {SHOT} |"))
_on_screen = _row.split(" | ")[5]                                 # the storyboard's on-screen cell
assert f'"{TAG}"' in _on_screen and BADGE in _on_screen and _labels in _on_screen, _on_screen
assert f'"{FACT}"' in _on_screen and f'"{SOURCE}"' in _on_screen, _on_screen
assert _on_screen.count("<br>") == len(_ITEMS) - 1, "storyboard row S01 shows more on-screen items than the shotlist"

# ---------- beats ----------

# Shot seconds. Guide clauses (silencedetect, -35 dB, 0.08 s), + 0.2 s:
#   "This is Mrs Chan," 0.20-1.50 ("Mrs" from 0.84, "Chan" about 1.26) | "going to see the Ruins of St. Paul's."
#   1.72-4.02 ("the Ruins" about 2.63-3.42, "of St. Paul's" 3.50) | "From her wheelchair," 4.28-5.24 |
#   "she sees only backs," 5.45-6.78 | "not the crowd building ahead." 7.00-8.38 (8.28 s file, the same audio as
#   when the voice started at 3.0 s behind the old fact title: every beat moved 2.8 s earlier). The shot ends at
#   12.0 s (11.0 -> 12.0 s in the second review): after the voice the fact overlay reads 8.55-11.85 s over the settled
#   map, and the last frames hold the map alone, as S18 opens on it.
# re-key to the real voice take
BEATS = {
    "map_in": 0.0,        # first frame: map paper; streets, steps and zone discs draw in (done by about 1.05 s)
    "voice": VOICE_START,  # "This is"
    "almeida_label": 0.6,
    "ahpo_in": 0.82,      # "Mrs Chan": her icon lands with a ring
    "tag_in": 1.2,        # "Chan": the tag slides in
    "move": 1.73,         # "going": she sets off north
    "senado_label": 1.98,
    "route_hint": 2.18,   # "to see": her dotted step-free route draws towards the pin
    "pin": 2.68,          # "the Ruins": the pin drops at Company of Jesus Square
    "ruins_label": 2.83,  # (all three labels read until the push-in at 4.28)
    "push_in": 4.28,      # "From her wheelchair": the camera pushes in on her ...
    "move_end": 4.43,
    "eye": 4.78,          # ... cross-fades and drops to her seated eye height ("wheelchair")
    "eye_push": 5.48,     # "she sees only backs": the wall closes in a little
    "crane": 6.93,        # "not the crowd building ahead": crane back up ...
    "map_back": 7.18,     # ... the map returns, zoomed on her, and pulls out
    "map_home": 8.13,
    "fact_in": 8.55,      # after the last word (8.38) and the guide's end (8.48): the fact line and its source fade in
    "fact_out": 11.55,    # ... and fade out, gone by 11.85: the last frames are the map alone (S18 opens on them)
}
assert abs(BEATS["voice"] - 0.2) < 1e-9 and BEATS["ahpo_in"] > BEATS["voice"]
# Shot time -> sim time across the two map beats (Senado's colour): beat 1 starts at the first recorded row,
# the eye-level beat skips ahead off screen, beat 2 ends at 14:09 (storyboard window 13:53-14:09). Senado
# crosses CRITICAL (14:08:09) at about 8.7 s, on the settled map after the last word (8.38), and holds red to the end.
SIM_KEYS = [(BEATS["map_in"], ahpo.senado_series()[0][0]), (4.98, ahpo.hms("14:02:00")),
            (BEATS["map_back"], ahpo.hms("14:05:30")), (9.18, ahpo.hms("14:09:00"))]


def sim_of(t: float) -> float:
    return ahpo.sim_clock(t, SIM_KEYS)


# the storyboard's "amber to red" must match the recorded data at both ends of the window
assert ahpo.state_of(ahpo.senado_density(SIM_KEYS[0][1])) == "WARNING", "Senado should start amber"
assert ahpo.state_of(ahpo.senado_density(SIM_KEYS[-1][1])) == "CRITICAL", "Senado should end red"
assert "WARNING" in ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[1][1]) and "CRITICAL" not in ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[2][1])

SCENE = MapScene()
EYE = EyeLevel()


# ---------- her tag: "Mrs Chan" ----------
# The same pill as ahpo.MapScene's tag (which S18 carries on), drawn here so it can slide in on its own beat: left
# of her icon, sliding in from it. It must clear the speaker lower-third (x 60-559, y 800-890), which
# video/assemble.py shows for 3 s from the voice start (0.2-3.2 s) while she is beside Almeida.

assert TAG == ahpo.NAME, (TAG, ahpo.NAME)
TAG_SPRITE = ahpo.tag_sprite(TAG).reduce(ahpo.SS)
TAG_GAP = 7          # between the tag and her icon's outline (px)


def tag_box(p, r: float, k: float) -> tuple[float, float]:
    """Top-left of the tag for her icon at p (screen px) with radius r; k = 0..1 slide-in."""
    return p[0] - r - TAG_GAP - TAG_SPRITE.width + (1 - k) * 10, p[1] - TAG_SPRITE.height / 2


# the tag clears the speaker lower-third that video/assemble.py lays over this shot (its own SPEAKER entry, drawn
# with style.lower_third), from where she starts to where she stops
_lt = transparent()
lower_third(_lt, *SPEAKER[SHOT])
LT_BOX = _lt.getbbox()                                        # (60, 800, x1, 890) for [MEMBER 4], "Medicine"
for _s in (0.0, AHPO_S01_END):
    _x, _y = tag_box(MAIN_PATH.at(_s), 21, 1.0)
    assert _x >= LT_BOX[2] + 12 or _y + TAG_SPRITE.height <= LT_BOX[1] - 8, (_s, _x, _y, LT_BOX)


# ---------- the fact overlay: the real 2025 event, after the voice ----------
# Second review (19 Oct): the Golden Week 2025 fact that the old 3 s title card carried returns as a short overlay
# over the settled map (Senado red), after the last word, never as a title. Two text elements (the fact line, wrapped
# to two lines, and its source), so the three place labels and her tag dim with it (declutter rule 1: at most two
# text elements beside the badge) and are back before the last frame. It sits on the empty left half of the frame:
# the map's nearest feature there is the Tercena disc (x ~830, y ~570), Senado's area starts at x ~930, y ~690, the
# caption band is y 920-990 and the speaker lower-third (0.2-3.2 s) is long gone.

FACT_FADE_IN, FACT_FADE_OUT = 0.25, 0.3


def fact_alpha(t: float) -> float:
    return progress(t, BEATS["fact_in"], FACT_FADE_IN) * (1 - progress(t, BEATS["fact_out"], FACT_FADE_OUT))


_fully = BEATS["fact_out"] - (BEATS["fact_in"] + FACT_FADE_IN)                 # fully readable: 2.75 s
for _txt in (FACT, SOURCE):
    assert _fully >= 0.3 * n_words(_txt) + 0.5, (_txt, _fully)                # declutter rule 5, at full opacity
assert BEATS["fact_out"] + FACT_FADE_OUT - BEATS["fact_in"] >= 3.0            # the brief: at least 3 s on screen
assert BEATS["fact_in"] >= VOICE_START + 8.28 and BEATS["fact_in"] >= BEATS["map_home"]   # after the guide and the pull-out
assert fact_alpha(DURATION - 3 / FPS) == 0.0 == fact_alpha(DURATION - 1 / FPS)  # the last frames are the map alone

FACT_X, FACT_Y = 100, 440
FACT_SIZE, SOURCE_SIZE = 44, 26
FACT_W = 680                                                       # the free left half, short of the map
FACT_LINES = wrap(FACT, FACT_SIZE, 700, FACT_W)
assert len(FACT_LINES) == 2 and all(text_size(l, FACT_SIZE, 700)[0] <= FACT_W for l in FACT_LINES), FACT_LINES
assert text_size(SOURCE, SOURCE_SIZE, 500)[0] <= FACT_W, SOURCE
FACT_H = int(len(FACT_LINES) * FACT_SIZE * 1.25) + 10 + SOURCE_SIZE            # block height: 440-592, above Senado's area
assert FACT_Y + FACT_H <= 690 and FACT_X + FACT_W <= 800, (FACT_Y + FACT_H, FACT_X + FACT_W)


def fact_overlay(img: Image.Image, t: float) -> None:
    a = fact_alpha(t)
    if a <= 0:
        return
    rise = (1 - a) * 8                                             # settles 8 px as it fades in, like the labels
    h = draw_text(img, (FACT_X, FACT_Y + rise), FACT, FACT_SIZE, 700, INK, a, max_width=FACT_W)
    draw_text(img, (FACT_X, FACT_Y + rise + h + 10), SOURCE, SOURCE_SIZE, 500, INK_2, a)


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
    """Home framing, except the push-in on her before eye level and the pull-out after it."""
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
              "ruins_st_paul": progress(t, BEATS["ruins_label"], 0.4)}       # the storyboard's three, no more
    zoomed = 0.0 if cam.home else clamp((cam.zoom - 1) / 0.3)    # labels and tag are gone before the push carries them off frame
    label_fade = 1 - zoomed
    dim = 1 - fact_alpha(t)                                       # labels and tag give way to the fact overlay, then return
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
        pin=(pin_k, -36 * (1 - pin_k)) if pin_k > 0 else None,      # no pin label (19 Oct declutter)
        ahpo={"p": MAIN_PATH.at(s_her), "alpha": ahpo_a, "scale": ahpo_scale,
              "ring": clamp((t - BEATS["ahpo_in"] - 0.05) / 0.9) if t < BEATS["ahpo_in"] + 0.95 else 0.0,
              "tag": 0.0},                       # S01 draws the tag itself, on its own beat (below)
        route=route,
        label_fade=label_fade * dim,
    ).convert("RGBA")
    ta = progress(t, BEATS["tag_in"], 0.35) * label_fade * dim * (1.0 if ahpo_a >= 0.999 else ahpo_a)
    if ta > 0:
        r = 21 * cam.zoom ** 0.6 * ahpo_scale
        paste(img, TAG_SPRITE, tag_box(cam(MAIN_PATH.at(s_her)), r, ta), ta)
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


# scrims over the silhouettes: bottom, so the caption band stays calm over the grey bodies; top, so the badge keeps
# its contrast over the grey heads
_SCRIM = np.zeros((H, W, 4), np.uint8)
_SCRIM[..., :3] = NAVY
_ys = np.arange(H, dtype=np.float32)
_SCRIM[..., 3] = (np.maximum(np.clip((_ys - 960) / 70, 0, 1) * 225,
                             np.clip((150 - _ys) / 110, 0, 1) * 175)).astype(np.uint8)[:, None]
SCRIM = Image.fromarray(_SCRIM, "RGBA")


# ---------- frame ----------

def draw_frame(t: float) -> Image.Image:
    eye_k = eye_mix(t)
    if eye_k >= 0.999:
        img = eye_frame(t)
    elif eye_k <= 0.001:
        img = map_frame(t)
    else:
        img = Image.blend(map_frame(t), eye_frame(t), eye_k)
    if eye_k > 0:
        paste(img, SCRIM, (0, 0), eye_k)
    fact_overlay(img, t)                           # after the voice: the real 2025 event, sourced
    badge(img, BADGE)                              # from the first frame: the story is an illustration
    return img


STILLS = {"open": 0.0, "story_in": 0.5, "tag": 1.8, "walk": 3.4, "pin": 4.1, "eye": 6.1, "crane": 7.5, "red": 9.2,
          "fact": 9.7, "fact_fading": 11.7, "end": DURATION - 1 / FPS}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        still(f"{SHOT}_{name}", draw_frame(ts))
    print("Senado state by sim time:", [(ahpo.clock(s), v, ahpo.state_of(v)) for s, v in ahpo._change_points() if s <= SIM_KEYS[-1][1] + 60])
    crit = next(t / 100 for t in range(int(SIM_KEYS[0][0] * 100), int(DURATION * 100))
                if ahpo.state_of(ahpo.senado_density(sim_of(t / 100))) == "CRITICAL")
    print(f"Senado turns CRITICAL at shot {crit:.2f} s; tag {TAG_SPRITE.size}; lower-third {LT_BOX}")
    print(f"fact overlay {BEATS['fact_in']}-{BEATS['fact_out'] + FACT_FADE_OUT} s, lines {FACT_LINES}; "
          f"labels back for the last frame: dim {1 - fact_alpha(DURATION - 1 / FPS):.2f}")
    if "--stills" not in sys.argv:
        print(render(SHOT, DURATION, draw_frame))
