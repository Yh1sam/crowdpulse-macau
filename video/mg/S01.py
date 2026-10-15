"""Shot S01 (0:00.0-0:11.5, 11.5 s): the Ah Po hook. "This is Ah Po, going to see the Ruins of St. Paul's.
From her wheelchair, she sees only backs, not the crowd building ahead."

0-1 s kinetic title "Macau · Golden Week" (it then docks top-left as a dateline); 1-6 s the top-down schematic
of the zone model: Ah Po's wheelchair icon with its "Ah Po" tag sets off north from Av. de Almeida Ribeiro
towards the pin at Company of Jesus Square (the square below the Ruins; she is never put on the St. Paul's
steps); 6-9 s her seated eye height: an armrest in the foreground, a wall of grey silhouettes swaying ahead;
9-11.5 s crane back up to the map as Senado's disc goes amber to red.

Data sources (read here, never retyped):
  - docs/video/shotlist.json, shot S01: DURATION (end_s - start_s).
  - shared/zones.json (via ahpo.py): zone lat/lon (linear projection), the 7 links, has_stairs / steep
    (the hatched steps; her dotted step-free route Senado -> St. Dominic's -> Rua de S. Paulo -> Company of
    Jesus Square is found by search over links without stairs or steep sections), Chinese place names.
  - experiments/results/simulation_run/A_timeline.csv: senado_square true_density, the ONLY data on screen.
    Shot time is mapped onto sim 13:53-14:09 across the two map beats (SIM_KEYS); the colour is the recorded
    value as held, thresholded with shared/config.json congestion_thresholds (the dashboard's).
  - docs/video/script.md section 3 row S01: title, labels, pin text, tag, small line and badge (verbatim).
Ah Po, the dots and the silhouettes are illustrative choreography (badge ILLUSTRATION).

Outputs: video/build/mg/S01.mp4, video/build/mg/stills/S01_*.png
Run:  .venv/bin/python video/mg/S01.py            (stills and render)
      .venv/bin/python video/mg/S01.py --stills   (stills only)
"""
from __future__ import annotations

import json
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
import ahpo  # noqa: E402
from ahpo import MapScene, EyeLevel, Cam, HOME, MAIN_PATH, POS, AHPO_S01_END, paste, text_sprite  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

SHOT = "S01"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 11.5 s

# Beats in seconds from the shot start, keyed to the narration at about 140 wpm (0.43 s a word), voice from 1.0 s:
# "This is Ah Po, | going to see the Ruins of St. Paul's. | From her wheelchair, she sees only backs, | not the crowd building ahead."
# re-key to the real voice take
BEATS = {
    "title_in": 0.0,      # kinetic title on navy
    "title_dock": 0.78,   # title shrinks to the top-left dateline while the map draws in
    "map_in": 0.72,       # streets, steps and zone discs draw in
    "voice": 1.0,         # "This is"
    "ahpo_in": 1.25,      # "Ah Po": her icon lands with a ring
    "tag_in": 1.75,       # "Po": the "Ah Po" tag slides in
    "almeida_label": 1.45,
    "move": 2.45,         # "going": she sets off north
    "senado_label": 2.7,
    "route_hint": 3.2,    # "to see": her dotted step-free route draws towards the pin
    "pin": 4.05,          # "the Ruins": the pin drops at Company of Jesus Square
    "ruins_label": 4.25,
    "pin_label": 4.85,    # "of St. Paul's": "view of the Ruins from the square below"
    "move_end": 5.55,
    "push_in": 5.3,       # "From her wheelchair": the camera pushes in on her ...
    "eye": 5.85,          # ... cross-fades and drops to her seated eye height
    "eye_push": 7.4,      # "she sees only backs": the wall closes in a little
    "crane": 8.95,        # "not the crowd building ahead": crane back up ...
    "map_back": 9.2,      # ... the map returns, zoomed on her, and pulls out
    "map_home": 10.15,
}
# Shot time -> sim time across the two map beats (Senado's colour): beat 1 starts at the first recorded row,
# the eye-level beat skips ahead off screen, beat 2 ends at 14:09 (storyboard window 13:53-14:09).
SIM_KEYS = [(1.0, ahpo.senado_series()[0][0]), (6.0, ahpo.hms("14:02:00")),
            (9.0, ahpo.hms("14:05:30")), (11.0, ahpo.hms("14:09:00"))]

# Text, verbatim from the storyboard (script.md section 3, S01).
TITLE_A, TITLE_DOT, TITLE_B = "Macau", " · ", "Golden Week"
SMALL = ("Illustrative story. The people are fictional; the map is a schematic of our zone model; "
         "Senado's colour follows our recorded simulation.")
BADGE = "ILLUSTRATION"
LABELS = ["almeida_ribeiro", "senado_square", "ruins_st_paul"]   # zh + en, as in the storyboard


def sim_of(t: float) -> float:
    return ahpo.sim_clock(t, SIM_KEYS)


# the storyboard's "amber to red" must match the recorded data at both ends of the window
assert ahpo.state_of(ahpo.senado_density(SIM_KEYS[0][1])) == "WARNING", "Senado should start amber"
assert ahpo.state_of(ahpo.senado_density(SIM_KEYS[-1][1])) == "CRITICAL", "Senado should end red"
assert "WARNING" in ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[1][1]) and "CRITICAL" not in ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[2][1])

SCENE = MapScene()
EYE = EyeLevel()


# ---------- title and dateline ----------

TITLE_SIZE, DATE_SIZE = 96, 34


def _title_sprite(size: int) -> tuple[Image.Image, list[int]]:
    """'Macau · Golden Week' with an amber middle dot; also returns the x of every character boundary."""
    text = TITLE_A + TITLE_DOT + TITLE_B
    f = font(size, 700)
    asc, desc = f.getmetrics()
    w_ = int(f.getlength(text)) + 8
    img = Image.new("RGBA", (w_, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((4, 4), TITLE_A, font=f, fill=(*INK, 255))
    d.text((4 + f.getlength(TITLE_A), 4), TITLE_DOT, font=f, fill=(*WARNING, 255))
    d.text((4 + f.getlength(TITLE_A + TITLE_DOT), 4), TITLE_B, font=f, fill=(*INK, 255))
    bounds = [0] + [int(round(4 + f.getlength(text[:i + 1]))) for i in range(len(text))]
    bounds[-1] = w_
    return img, bounds


TITLE, TITLE_BOUNDS = _title_sprite(TITLE_SIZE)
TITLE_STRIPS = [TITLE.crop((a, 0, b, TITLE.height)) for a, b in zip(TITLE_BOUNDS, TITLE_BOUNDS[1:])]
DATE, _ = _title_sprite(DATE_SIZE)
TITLE_XY = ((W - TITLE.width) / 2, 470 - TITLE.height / 2)
DATE_XY = (60 - 4, 48 - 4)                     # top-left slot (S01 has no chapter card)


def draw_title(img: Image.Image, t: float) -> None:
    dock = progress(t, BEATS["title_dock"], 0.6)
    if dock <= 0:
        # letters rise in one after another, the underline grows from the centre
        for i, strip in enumerate(TITLE_STRIPS):
            k = progress(t, BEATS["title_in"] + 0.04 + 0.022 * i, 0.34)
            if k > 0:
                paste(img, strip, (TITLE_XY[0] + TITLE_BOUNDS[i], TITLE_XY[1] + 28 * (1 - k)), k)
        u = progress(t, 0.32, 0.4)
        if u > 0:
            half = 0.5 * (TITLE.width - 8) * u
            cx, y = W / 2, TITLE_XY[1] + TITLE.height + 18
            rounded(img, (cx - half, y, cx + half, y + 4), 2, fill=WARNING, alpha=0.9)
        return
    # dock: scale and move to the dateline slot; once there, the crisp small sprite takes over
    # (same size and place, so the swap is invisible)
    if dock >= 0.999:
        paste(img, DATE, DATE_XY)
        return
    s = lerp(1.0, DATE.width / TITLE.width, dock)
    x, y = lerp(TITLE_XY[0], DATE_XY[0], dock), lerp(TITLE_XY[1], DATE_XY[1], dock)
    spr = TITLE.resize((max(1, round(TITLE.width * s)), max(1, round(TITLE.height * s))), Image.LANCZOS)
    paste(img, spr, (x, y))
    u = 1 - progress(t, BEATS["title_dock"], 0.25)
    if u > 0:
        half = 0.5 * (TITLE.width - 8) * s
        cx, yy = x + spr.width / 2, y + spr.height + 18 * s
        rounded(img, (cx - half, yy, cx + half, yy + 4), 2, fill=WARNING, alpha=0.9 * u)


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


def map_cam(t: float) -> Cam:
    """Home framing, except the push-in on Ah Po before eye level and the pull-out after it."""
    p = MAIN_PATH.at(ahpo_s(t))
    k_in = progress(t, BEATS["push_in"], BEATS["eye"] + 0.45 - BEATS["push_in"])
    k_out = 1 - progress(t, BEATS["map_back"] - 0.1, BEATS["map_home"] - BEATS["map_back"] + 0.1)
    k = k_in if t < 7.5 else k_out
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
        ahpo={"p": MAIN_PATH.at(s_her), "alpha": progress(t, BEATS["ahpo_in"], 0.35),
              "scale": lerp(0.6, 1.0, progress(t, BEATS["ahpo_in"], 0.45)),
              "ring": clamp((t - BEATS["ahpo_in"] - 0.05) / 0.9) if t < BEATS["ahpo_in"] + 0.95 else 0.0,
              "tag": progress(t, BEATS["tag_in"], 0.35)},
        route=route,
        label_fade=label_fade,
    )
    return img.convert("RGBA")


# ---------- the eye-level beat ----------

def eye_frame(t: float) -> Image.Image:
    drop = progress(t, BEATS["eye"] - 0.05, 0.95)                   # camera drops to seated height
    rise = progress(t, BEATS["crane"], 0.75)                        # and cranes back up
    crowd_dy = lerp(230, 0, drop) + lerp(0, 270, rise)
    arm_dy = lerp(360, 0, progress(t, BEATS["eye"] + 0.1, 0.8)) + lerp(0, 420, progress(t, BEATS["crane"] - 0.05, 0.6))
    push = lerp(1.0, 1.05, progress(t, BEATS["eye_push"], 1.6))      # the wall of backs closes in a little
    return EYE.frame(t, crowd_dy=crowd_dy, arm_dy=arm_dy, push=push).convert("RGBA")


def eye_mix(t: float) -> float:
    """0 = map, 1 = eye level."""
    return progress(t, BEATS["eye"], 0.4) * (1 - progress(t, BEATS["map_back"], 0.4))


# scrims over the silhouettes: bottom, so the small line stays legible; top, so the dateline and the badge
# keep their contrast over the grey heads (pasted before the dateline is drawn)
_SCRIM = np.zeros((H, W, 4), np.uint8)
_SCRIM[..., :3] = NAVY
_ys = np.arange(H, dtype=np.float32)
_SCRIM[..., 3] = (np.maximum(np.clip((_ys - 960) / 70, 0, 1) * 225,
                             np.clip((150 - _ys) / 110, 0, 1) * 175)).astype(np.uint8)[:, None]
SCRIM = Image.fromarray(_SCRIM, "RGBA")


# ---------- overlays ----------

SMALL_LINES = wrap(SMALL, 20, 500, 1100)
assert len(SMALL_LINES) <= 2


def draw_overlays(img: Image.Image, t: float, eye_k: float) -> None:
    a = progress(t, 0.45, 0.45)
    for i, ln in enumerate(SMALL_LINES):
        draw_text(img, (60, 1006 + i * 28), ln, 20, 500, INK_2, a)
    badge(img, BADGE, alpha=progress(t, 0.55, 0.45))


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
    draw_title(img, t)
    draw_overlays(img, t, eye_k)
    return img


STILLS = {"title": 0.55, "walk": 3.6, "pin": 5.25, "eye": 8.2, "crane": 9.75, "red": 11.3}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        still(f"{SHOT}_{name}", draw_frame(ts))
    print("Senado state by sim time:", [(ahpo.clock(s), v, ahpo.state_of(v)) for s, v in ahpo._change_points() if s <= SIM_KEYS[-1][1] + 60])
    if "--stills" not in sys.argv:
        print(render(SHOT, DURATION, draw_frame))
