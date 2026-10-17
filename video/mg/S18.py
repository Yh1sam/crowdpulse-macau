"""Shot S18 (4:03.5-4:09.5, 6.0 s): back to Ah Po. "Back to Ah Po: her main route stays open, with staff beside her."

Same map and framing as S01 (ahpo.py). An APPROVED stamp lands; the approved card's step-free detour draws as a
dashed line and grey walkers take it; a small zh / en / pt notice flashes at Av. de Almeida Ribeiro (where the
card displays it); her main route north to Company of Jesus Square is drawn open through Senado's crowd and a
staff icon (hi-vis vest) joins her on it. Senado stays red (CRITICAL) throughout.

Data sources (read here, never retyped):
  - docs/video/shotlist.json, shot S18: DURATION (end_s - start_s).
  - shared/zones.json (via ahpo.py): projection, links, her step-free main route, and the detour, built by
    following the approved card's links by name (run A card #5, A07_intervention_evidence.png:
    Rua dos Ervanarios descent -> Rua da Tercena west link -> Rua de S. Paulo (lower), to St. Dominic's Square).
  - experiments/results/simulation_run/A_events.json + A_timeline.csv: shot time is mapped onto run A from the
    approval (14:14) to the end of the run (14:40); Senado's colour is its recorded true_density, thresholded with
    shared/config.json, and the script asserts it is CRITICAL for the whole window (it ended at 0.75).
  - backend/app/services/intervention.py: the notice (public_messages for that card, first sentence of each
    language, ending in "…" as on S04's gloss panel: the full notice goes on to the route, the staff sentence
    and the AI clause, so the board must not read as a whole notice without it) and the source of the
    on-screen recommendation line.
  - docs/video/script.md section 3 row S18: the two on-screen lines (verbatim).
Ah Po, the staff member, the walkers and the dots are illustrative choreography (badge ILLUSTRATION).

Outputs: video/build/mg/S18.mp4, video/build/mg/stills/S18_*.png
Run:  .venv/bin/python video/mg/S18.py            (stills and render)
      .venv/bin/python video/mg/S18.py --stills   (stills only)
"""
from __future__ import annotations

import json
import math
import random
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
import ahpo  # noqa: E402
from ahpo import MapScene, HOME, MAIN_PATH, DETOUR_PATH, POS, AHPO_S01_END, FIRST_LEG, paste, text_sprite  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

SHOT = "S18"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 6.0 s

# Beats in seconds from the shot start, keyed to the narration at about 140 wpm (0.43 s a word), voice from 0.3 s:
# "Back to Ah Po: | her main route stays open, | with staff beside her."
# re-key to the real voice take
BEATS = {
    "stamp": 0.35,        # "Back": the APPROVED stamp lands
    "tag_out": 0.7,       # her "Ah Po" tag (carried over from S01's last frame) fades before the detour reaches it:
                          # it sits left of her icon, exactly where the detour leaves Almeida, for the whole shot
    "detour": 0.75,       # "to Ah Po": the approved card's dashed step-free detour draws
    "notice": 1.05,       # the zh / en / pt notice flashes at Almeida ...
    "walkers": 1.25,      # ... and grey walkers take the detour
    "route": 2.15,        # "her main route": her route north draws, solid
    "statement": 2.35,    # the recommendation line appears (read through to the end)
    "lane": 2.6,          # "stays open": a lane opens through Senado's crowd
    "move": 2.6,          # she rolls on north
    "notice_out": 4.4,    # the notice fades
    "staff": 4.25,        # "with staff": the staff member joins her
}
SIM_KEYS = [(0.0, ahpo.approve_sim()), (DURATION, ahpo.end_sim())]    # run A: approval (14:14) -> end (14:40)

# Text, verbatim from the storyboard (script.md section 3, S18).
SMALL = "Illustrative story"
STATEMENT = "Every redirect recommendation includes keeping the main route open, with staff, for reduced-mobility visitors"
SOURCE = "Detour from run A's approved card · recommendation and notice wording: backend/app/services/intervention.py"
BADGE = "ILLUSTRATION"
STAMP = "APPROVED"
NOTICE = ahpo.notice_excerpts()                       # {"en", "zh", "pt"} from intervention.py, each ending "…"
CHIP = "CRITICAL"


def sim_of(t: float) -> float:
    return ahpo.sim_clock(t, SIM_KEYS)


# Senado never turns green or amber here: the recorded true_density stays above CRITICAL from approval to the end
assert ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[-1][1]) == {"CRITICAL"}, ahpo.window_states(SIM_KEYS[0][1], SIM_KEYS[-1][1])
assert "senado_square" not in ahpo.DETOUR and ahpo.DETOUR[0] == "almeida_ribeiro"

SCENE = MapScene()


# ---------- Ah Po and the staff member ----------

S_END = FIRST_LEG + 64        # she ends just past Senado's centre, on towards St. Dominic's


def ahpo_s(t: float) -> float:
    """Distance along her main route: eases in, then rolls on at constant speed (she is still moving at the cut)."""
    t0, ramp = BEATS["move"], 0.7
    T = DURATION - t0
    v = (S_END - AHPO_S01_END) / (T - ramp / 2)
    u = t - t0
    if u <= 0:
        return AHPO_S01_END
    if u < ramp:
        return AHPO_S01_END + v * u * u / (2 * ramp)
    return AHPO_S01_END + v * (ramp / 2 + (u - ramp))


def staff_state(t: float, s: float) -> dict:
    """The staff member walks in from ahead-right and settles on her right, 46 px from her centre (marker as large as hers)."""
    k = progress(t, BEATS["staff"], 0.6)
    dx, dy = MAIN_PATH.direction(s)
    side = (-dy, dx)                                        # her right-hand side on screen
    p = MAIN_PATH.at(s)
    off = 46
    target = (p[0] + side[0] * off, p[1] + side[1] * off)
    start = (target[0] + dx * 40 + side[0] * 18, target[1] + dy * 40 + side[1] * 18)
    return {"p": lerp(start, target, k), "alpha": k, "scale": lerp(0.7, 1.0, k) * 21 / 18}


# ---------- walkers on the detour ----------

_rng = random.Random(18)
WALKERS = [(BEATS["walkers"] + 0.11 * i + _rng.uniform(-0.03, 0.03), _rng.uniform(-4.0, 4.0), _rng.uniform(150, 175))
           for i in range(48)]


def walkers(t: float) -> list[tuple[tuple[float, float], float]]:
    out = []
    L = DETOUR_PATH.length
    for t0, off, v in WALKERS:
        s = (t - t0) * v
        if s <= 0 or s >= L:
            continue
        p = DETOUR_PATH.at(s)
        dx, dy = DETOUR_PATH.direction(s)
        p = (p[0] - dy * off, p[1] + dx * off)
        a = clamp(s / 30) * clamp((L - s) / 30)
        out.append((p, a))
    return out


# ---------- stamp, notice, statement, chip ----------

def _stamp_sprite(ring: bool = False) -> Image.Image:
    """The stamp (or, with ring=True, just its outer frame, for the landing ring), tilted 8 degrees."""
    q = 2
    f = font(52 * q, 800)
    tw = f.getlength(STAMP)
    pad_x, pad_y = 30 * q, 18 * q
    asc, desc = f.getmetrics()
    w_, h_ = int(tw + 2 * pad_x), int(asc + 2 * pad_y - 6 * q)
    img = Image.new("RGBA", (w_ + 40 * q, h_ + 40 * q), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0 = 20 * q, 20 * q
    if ring:
        d.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 12 * q, outline=(*SAFE, 255), width=3 * q)
    else:
        d.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 12 * q, fill=(*NAVY, 200), outline=(*SAFE, 255), width=5 * q)
        d.rounded_rectangle((x0 + 10 * q, y0 + 10 * q, x0 + w_ - 10 * q, y0 + h_ - 10 * q), 6 * q, outline=(*SAFE, 255), width=2 * q)
        d.text((x0 + w_ / 2, y0 + h_ / 2 + 2 * q), STAMP, font=f, fill=(*SAFE, 255), anchor="mm")
    img = img.rotate(8, resample=Image.BICUBIC, expand=True)
    return img.resize((img.width // q, img.height // q), Image.LANCZOS)


STAMP_SPR = _stamp_sprite()
STAMP_RING = _stamp_sprite(ring=True)
STAMP_C = (585, 430)                                    # left of the map, beside the detour


def draw_stamp(img: Image.Image, t: float) -> None:
    k = clamp((t - BEATS["stamp"]) / 0.26)
    if k <= 0:
        return
    s = lerp(1.7, 1.0, k * k)                              # accelerates onto the page
    spr = STAMP_SPR if s == 1.0 else STAMP_SPR.resize((round(STAMP_SPR.width * s), round(STAMP_SPR.height * s)), Image.LANCZOS)
    paste(img, spr, (STAMP_C[0] - spr.width / 2, STAMP_C[1] - spr.height / 2), clamp(k * 1.6))
    r = clamp((t - BEATS["stamp"] - 0.26) / 0.45)              # landing ring, tilted like the stamp
    if 0 < r < 1:
        g = 1.0 + 0.22 * ease(r)
        ring = STAMP_RING.resize((round(STAMP_RING.width * g), round(STAMP_RING.height * g)), Image.LANCZOS)
        paste(img, ring, (STAMP_C[0] - ring.width / 2, STAMP_C[1] - ring.height / 2), 0.6 * (1 - r))


def _notice_sprite() -> tuple[Image.Image, tuple[int, int]]:
    rows = [("ZH", NOTICE["zh"]), ("EN", NOTICE["en"]), ("PT", NOTICE["pt"])]
    tag_w = 44
    text_w = max(text_size(txt, 22, 500)[0] for _, txt in rows)
    w_, line = 24 + tag_w + text_w + 26, 38
    h_ = 18 + line * len(rows) + 10
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    rounded(img, (0, 0, w_ - 1, h_ - 1), 14, fill=NAVY_2, outline=INK_3, width=2)
    for i, (tag, txt) in enumerate(rows):
        y = 16 + i * line
        draw_text(img, (24, y + 3), tag, 20, 700, INK_3)
        draw_text(img, (24 + tag_w, y), txt, 22, 500, INK)
    return img, (w_, h_)


NOTICE_SPR, NOTICE_WH = _notice_sprite()
NOTICE_XY = (812 - NOTICE_WH[0], 640)                    # right edge at x 812, bottom above y 790
ELBOW_X = 792                                            # leader drops at x 792 (right of the lower-third area)


def draw_notice(img: Image.Image, t: float) -> None:
    a = progress(t, BEATS["notice"], 0.25) * (1 - progress(t, BEATS["notice_out"], 0.35))
    if a <= 0:
        return
    x0, y0 = NOTICE_XY
    w_, h_ = NOTICE_WH
    # two soft flashes of the frame (no hard on/off)
    flash = 0.0
    for c in (BEATS["notice"] + 0.3, BEATS["notice"] + 0.75):
        flash = max(flash, math.exp(-((t - c) / 0.11) ** 2))
    if flash > 0.01:
        for g, ga in ((10, 0.18), (5, 0.35)):
            rounded(img, (x0 - g, y0 - g, x0 + w_ + g, y0 + h_ + g), 14 + g, outline=INK, width=3, alpha=a * ga * flash)
    paste(img, NOTICE_SPR, (x0, y0), a)
    if flash > 0.01:
        rounded(img, (x0, y0, x0 + w_ - 1, y0 + h_ - 1), 14, outline=INK, width=2, alpha=a * flash)
    # leader to Av. de Almeida Ribeiro, where the card displays the notice
    ax, ay = POS["almeida_ribeiro"]
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    col = (*INK_3, int(255 * a))
    d.line([(ELBOW_X, y0 + h_), (ELBOW_X, ay), (ax - ahpo.DISC_R - 4, ay)], fill=col, width=2, joint="curve")
    d.ellipse((ax - ahpo.DISC_R - 9, ay - 5, ax - ahpo.DISC_R + 1, ay + 5), fill=col)
    img.alpha_composite(lay)


STATEMENT_X, STATEMENT_Y, STATEMENT_W = 1450, 380, 410
STATEMENT_LINES = wrap(STATEMENT, 32, 600, STATEMENT_W)


def draw_statement(img: Image.Image, t: float) -> None:
    k = progress(t, BEATS["statement"], 0.5)
    if k <= 0:
        return
    hgt = len(STATEMENT_LINES) * 42
    rounded(img, (STATEMENT_X - 26, STATEMENT_Y + 4, STATEMENT_X - 21, STATEMENT_Y + 4 + hgt * k), 2, fill=WARNING, alpha=k)
    for i, ln in enumerate(STATEMENT_LINES):
        ki = progress(t, BEATS["statement"] + 0.05 * i, 0.45)
        draw_text(img, (STATEMENT_X, STATEMENT_Y + i * 42 + 12 * (1 - ki)), ln, 32, 600, INK, ki)


def draw_chip(img: Image.Image) -> None:
    """State chip beside Senado's English label (it stays CRITICAL for the whole shot)."""
    x, y = POS["senado_square"]
    lx = x + ahpo.SENADO_R + ahpo.LABEL_DX["senado_square"]
    en_w = text_size(ahpo.LABEL_EN["senado_square"], 22, 500)[0]
    cw = text_size(CHIP, 20, 700)[0] + 20
    x0, y0 = lx + en_w + 14, y + 3
    rounded(img, (x0, y0, x0 + cw, y0 + 28), 14, fill=CRITICAL)
    draw_text(img, (x0 + cw / 2, y0 + 14), CHIP, 20, 700, NAVY, anchor="mm")


# ---------- frame ----------

def draw_frame(t: float) -> Image.Image:
    sim = sim_of(t)
    s_her = ahpo_s(t)
    route_k = progress(t, BEATS["route"], 1.2)
    route = None
    if route_k > 0:
        s0 = s_her + 26
        route = {"s0": s0, "s1": s0 + (MAIN_PATH.length - s0) * route_k, "alpha": 1.0}
    img = SCENE.render(
        t, HOME,
        senado_col=ahpo.senado_colour(t, sim_of),
        senado_dens=ahpo.senado_density_smooth(sim),
        dots_alpha=0.45,                       # background drift dimmed so the walkers on the detour read
        labels={"almeida_ribeiro": 1.0, "senado_square": 1.0, "ruins_st_paul": 1.0},
        pin=(1.0, 0.0),
        ahpo={"p": MAIN_PATH.at(s_her), "alpha": 1.0, "tag": 1 - progress(t, BEATS["tag_out"], 0.3)},
        staff=staff_state(t, s_her),
        route=route,
        detour={"k": progress(t, BEATS["detour"], 0.9), "phase": 38 * t, "alpha": 0.95},
        walkers=walkers(t),
        lane_k=progress(t, BEATS["lane"], 0.9),
        lane_w=30.0,
    ).convert("RGBA")
    draw_chip(img)
    draw_stamp(img, t)
    draw_notice(img, t)
    draw_statement(img, t)
    badge(img, BADGE)
    draw_text(img, (60, 1006), SMALL, 20, 600, INK_2)
    draw_text(img, (60, 1034), SOURCE, 20, 500, INK_3, max_width=1150)
    return img


STILLS = {"stamp": 0.75, "notice": 1.75, "route_open": 3.6, "staff": 4.95, "end": 5.95}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        still(f"{SHOT}_{name}", draw_frame(ts))
    if "--stills" not in sys.argv:
        print(render(SHOT, DURATION, draw_frame))
