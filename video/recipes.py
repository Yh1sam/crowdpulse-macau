"""Per-shot recipes for video/assemble.py: which source each shot uses, how it is framed, and which
overlays sit on it. recipe(shot, duration) -> (ffmpeg input args, [(png, start, end)], [(alpha mov,
offset)], pre-filter). Times are seconds from the start of the shot; re-key them to the team's takes.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw

from assemble import png
from style import (BUILD, INK, NAVY, SAFE, WARNING, CRITICAL, badge, chapter_card, draw_text, footer, rounded, text_size)

MG, CLIPS, OVL = BUILD / "mg", BUILD / "clips", BUILD / "overlays"
MG_SHOTS = {"S01": "S01", "S05": "S05", "S06": "S06", "S07": "S07", "S10": "S10", "S11": "S11", "S13": "S13",
            "S14": "S14", "S16": "S16", "S17": "S17", "S18": "S18", "S19": "S19", "S20": "S20"}


SEG = BUILD / "cut" / "segments"


def segments(name: str, src: Path, parts: list[tuple[float, float, tuple, tuple]]) -> Path:
    """Cuts parts out of a 1920x1080 recording and joins them: each part is (t0, t1, box_from,
    box_to), a box being (x, y, w) in source pixels with a 16:9 height; the view eases from
    box_from to box_to over the part (same box = static crop). Returns the base clip."""
    import subprocess
    SEG.mkdir(parents=True, exist_ok=True)
    out = SEG / f"{name}.mp4"
    chains, labels = [], []
    for i, (t0, t1, (x0, y0, w0), (x1, y1, w1)) in enumerate(parts):
        n = max(1, int(round((t1 - t0) * 30)))
        k = f"(1-cos(PI*min(on/{n},1)))/2"  # eased progress 0 -> 1
        zw = f"({w0}+({w1}-{w0})*{k})"
        chains.append(f"[0:v]trim={t0}:{t1},setpts=PTS-STARTPTS,fps=30,"
                      f"zoompan=z='1920/{zw}':x='{x0}+({x1}-{x0})*{k}':y='{y0}+({y1}-{y0})*{k}':d=1:s=1920x1080:fps=30,setsar=1[p{i}]")
        labels.append(f"[p{i}]")
    graph = ";".join(chains) + f";{''.join(labels)}concat=n={len(parts)}:v=1:a=0[v]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-filter_complex", graph, "-map", "[v]",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


FULL = (0, 0, 1920)


def stamp(img, x: int, y: int, text: str, colour) -> None:
    w, _ = text_size(text, 26, 700)
    rounded(img, (x, y, x + w + 36, y + 46), 12, fill=colour)
    draw_text(img, (x + 18, y + 9), text, 26, 700, NAVY)


def s02(dur: float):
    # Simulator screen scaled to full height at x 383-880, where the S02 overlay expects it
    return (["-ss", "5", "-i", str(CLIPS / "S02_sim.mp4")], [], [(OVL / "S02.mov", 0.0)],
            "scale=-2:1080,pad=1920:1080:383:0:color=0x0B1220")


def s08(dur: float):
    # real terminal session; codes appear ~0.1 s after each command (1.6 / 3.9 / 5.8 s in the take)
    ov = [
        (png("S08_card", lambda img: chapter_card(img, "Can it be trusted?")), 0.0, 2.0),
        (png("S08_badge", lambda img: badge(img, "LIVE SOFTWARE", "recorded live")), 0.0, dur),
        (png("S08_footer", lambda img: footer(img, "same checks in backend/tests/test_api.py · real requests to a fresh backend on localhost:8001")), 0.0, dur),
        (png("S08_s1", lambda img: stamp(img, 300, 341, "202 accepted · numbers only", SAFE)), 1.75, dur),
        (png("S08_s2", lambda img: stamp(img, 300, 446, "422 rejected · extra field face_id (closed schema)", WARNING)), 4.05, dur),
        (png("S08_s3", lambda img: stamp(img, 300, 586, "403 refused · image upload (PRIVACY_MODE on by default)", CRITICAL)), 5.95, dur),
    ]
    return ["-i", str(CLIPS / "S08.mp4")], ov, [], ""


def placeholder(shot: str, what: str, dur: float):
    p = png(f"{shot}_todo", lambda img: (rounded(img, (360, 380, 1560, 700), 24, fill=(20, 31, 52), outline=WARNING, width=4, dash=True),
                                         draw_text(img, (960, 470), f"[{shot}: {what}]", 40, 700, WARNING, anchor="ma", max_width=1100)))
    return ["-f", "lavfi", "-i", f"color=c=0x0B1220:s=1920x1080:r=30:d={dur}"], [(p, 0.0, dur)], [], ""


def concat_clips(name: str, paths: list[Path]) -> Path:
    import subprocess
    SEG.mkdir(parents=True, exist_ok=True)
    out = SEG / f"{name}.mp4"
    ins = sum([["-i", str(x)] for x in paths], [])
    graph = "".join(f"[{i}:v]fps=30,scale=1920:1080,setsar=1[c{i}];" for i in range(len(paths))) + "".join(f"[c{i}]" for i in range(len(paths))) + f"concat=n={len(paths)}:v=1:a=0[v]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", graph, "-map", "[v]", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def callout(img, x: int, y: int, text: str, colour=None, size: int = 28) -> None:
    """A small labelled pill pointing at something in the captured UI."""
    colour = colour or (34, 197, 214)
    w, _ = text_size(text, size, 700)
    rounded(img, (x, y, x + w + 40, y + size + 22), 14, fill=(11, 18, 32), outline=colour, width=3)
    draw_text(img, (x + 20, y + 10), text, size, 700, colour)


def highlight(img, box, colour=None) -> None:
    rounded(img, box, 12, outline=colour or (245, 166, 35), width=5)


def to_out(box, x: float, y: float) -> tuple[int, int]:
    """Source pixel -> output pixel inside a static crop box (x0, y0, w)."""
    x0, y0, w = box
    k = 1920 / w
    return int((x - x0) * k), int((y - y0) * k)


def s03(dur: float):
    c2a = CLIPS / "C2a.mp4"
    side, rows = (1180, 600, 740), (300, 470, 1080)
    base = segments("S03", c2a, [
        (100.4, 101.4, FULL, FULL),                 # Live map, Senado amber
        (101.6, 103.2, FULL, (760, 120, 1160)),     # click Senado; the sidebar fills
        (104.0, 105.2, side, side),                 # forecast rows and the reasons
        (105.5, 106.7, FULL, FULL),                 # Zone detail opens (WARNING)
        (111.6, 112.8, FULL, FULL),                 # the zone turns CRITICAL
        (116.2, 120.0, FULL, rows),                 # forecast rows turn from WARNING to CRITICAL, with confidence
    ])
    x0, y0 = to_out(side, 1385, 715); x1, y1 = to_out(side, 1870, 975)
    ov = [
        (png("S03_badge", lambda img: badge(img, "LIVE SOFTWARE", "SIMULATED CROWD", sub="Simulated Golden Week afternoon · SIM CLOCK, 10× speed")), 0.0, dur),
        (png("S03_why", lambda img: (highlight(img, (x0, y0, x1, min(y1, 1072))), callout(img, x0, max(130, y0 - 74), "why"))), 2.7, 3.8),
        (png("S03_rows", lambda img: (callout(img, 980, 760, "+5 / +10 / +15 min"), callout(img, 980, 840, "confidence"))), 7.6, dur),
        (png("S03_footer", lambda img: footer(img, "Map © OpenStreetMap contributors")), 0.0, 2.6),
    ]
    return ["-i", str(base)], ov, [], ""


def s04(dur: float):
    b2 = CLIPS / "C2b2.mp4"
    route, notice, ev, log = (330, 150, 1150), (260, 460, 1100), (250, 380, 1100), (320, 20, 1100)
    base = segments("S04", b2, [
        (8.0, 10.5, FULL, route),     # route line "no stairs" and the green accessibility note
        (11.6, 13.6, notice, notice), # zh / en / pt notice
        (16.0, 17.2, ev, ev),         # evidence
        (19.0, 20.2, ev, ev),         # APPROVE (scripted click)
        (33.6, 35.7, log, log),       # Decided: approved by operator; audit log: intervention_approved
    ])
    ov = [
        (png("S04_badge", lambda img: badge(img, "LIVE SOFTWARE", "SIMULATED CROWD")), 0.0, dur),
        (png("S04_c1", lambda img: callout(img, 120, 820, "accessibility check: this route avoids stairs")), 1.0, 2.5),
        (png("S04_c2", lambda img: (callout(img, 120, 160, "中文 · English · Português"),
                                     draw_text(img, (120, 236), "zh 「議事亭前地目前非常擁擠…」 (Senado Square is very crowded…)", 26, 600, INK),
                                     draw_text(img, (120, 276), "pt 「Largo do Senado: grande afluência de visitantes…」", 26, 600, INK))), 2.6, 4.5),
        (png("S04_c3", lambda img: callout(img, 120, 160, "needs a person's approval")), 5.7, 6.9),
        (png("S04_c4", lambda img: callout(img, 1300, 760, "audit log")), 6.9, dur),
        (png("S04_footer", lambda img: footer(img, "click scripted for this recording · the approval runs the real code path")), 5.7, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def s09(dur: float):
    rows, dec = (300, 470, 1080), (320, 20, 1100)
    tail = segments("S09_tail", CLIPS / "C2a.mp4", [(107.0, 109.5, rows, rows)])
    tail2 = segments("S09_tail2", CLIPS / "C2b2.mp4", [(33.8, 35.3, dec, dec)])
    base = concat_clips("S09", [MG / "S09_mg.mp4", tail, tail2])
    ov = [
        (png("S09_live", lambda img: badge(img, "LIVE SOFTWARE", "dashboard")), 4.0, dur),
        (png("S09_rows", lambda img: callout(img, 980, 160, "LOW CONFIDENCE — HUMAN REVIEW REQUIRED", (245, 166, 35))), 4.2, 6.5),
        (png("S09_dec", lambda img: callout(img, 120, 900, "Stronger recommendations replace weaker pending ones")), 6.5, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def s12(dur: float):
    readme = segments("S12_readme", CLIPS / "README_insert.mp4", [(2.2, 4.2, FULL, FULL)])
    base = concat_clips("S12", [MG / "S12_mg.mp4", readme])
    ov = [
        (png("S12_hl", lambda img: highlight(img, (510, 4, 1410, 240))), 8.2, dur),
        (png("S12_badge", lambda img: badge(img, "CORRECTED")), 8.0, dur),
        (png("S12_footer", lambda img: footer(img, "README.md · Correction")), 8.0, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def s15_panel(img, t_dots: bool) -> None:
    rounded(img, (40, 170, 900, 860 if t_dots else 520), 22, fill=(11, 18, 32), alpha=0.9)
    draw_text(img, (76, 196), "same 120 simulated people, with vs without the closure", 26, 600, INK)
    for i, (who, val, col) in enumerate([("walkers", "+17 s", (36, 124, 118)), ("wheelchair users", "+30 s", (118, 88, 181)), ("stroller users", "+21 s", (206, 103, 68))]):
        y = 250 + i * 70
        rounded(img, (76, y, 96, y + 40), 6, fill=col)
        draw_text(img, (114, y + 2), who, 30, 600, INK)
        draw_text(img, (860, y + 2), val, 34, 800, INK, anchor="ra")
    draw_text(img, (76, 466), "averages over those who arrive in both plans: walkers 40/40 · wheelchair users 16/40 · stroller users 28/40", 21, 500, (160, 174, 196), max_width=800)
    if t_dots:
        for k in range(40):
            cx, cy = 96 + (k % 10) * 46, 580 + (k // 10) * 46
            grey = k >= 16
            ImageDraw.Draw(img).ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=(98, 113, 138) if grey else (118, 88, 181))
        draw_text(img, (580, 572), "24 of 40 wheelchair users: no step-free route in EITHER plan", 24, 700, INK, max_width=300)
        draw_text(img, (580, 700), "missing map detail or real barriers? Needs a site survey.", 22, 500, (160, 174, 196), max_width=300)


def s15(dur: float):
    c2c = CLIPS / "C2c.mp4"
    card, results = (300, 100, 1300), (1000, 330, 920)
    base = segments("S15", c2c, [
        (1.8, 4.3, card, card),        # St. Dominic's card; TEST IN SKETCHFUTURE clicked
        (4.9, 7.0, FULL, FULL),        # SketchFuture opens the plan and compares
        (7.0, 13.0, FULL, results),    # walker and wheelchair results
        (13.0, 18.8, results, FULL),   # back out to the whole plan
    ])
    ov = [
        (png("S15_badge", lambda img: badge(img, "MODEL CHECK", "synthetic cohort")), 0.0, dur),
        (png("S15_counters", lambda img: s15_panel(img, False)), 6.0, 9.5),
        (png("S15_dots", lambda img: s15_panel(img, True)), 9.5, dur),
        (png("S15_footer", lambda img: footer(img, "Map © OpenStreetMap contributors, ODbL · this plan came from recommendation #7; same plan and results as run #721 in sketchfuture/VERIFICATION.md")), 0.0, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def recipe(shot: dict, dur: float):
    sid = shot["id"]
    if sid in MG_SHOTS:
        return ["-i", str(MG / f"{MG_SHOTS[sid]}.mp4")], [], [], ""
    if sid == "S02":
        return s02(dur)
    if sid == "S08":
        return s08(dur)
    if sid in ("S03", "S04", "S09", "S12", "S15"):
        return {"S03": s03, "S04": s04, "S09": s09, "S12": s12, "S15": s15}[sid](dur)
    return placeholder(sid, "not built", dur)
