"""Per-shot recipes for video/assemble.py: which source each shot uses, how it is framed, and which
overlays sit on it. recipe(shot, duration) -> (ffmpeg input args, [(png, start, end)], [(alpha mov,
offset)], pre-filter). Times are seconds from the start of the shot; re-key them to the team's takes.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw

from assemble import png
from style import (BUILD, INK, INK_2, NAVY, SAFE, WARNING, CRITICAL, CYAN, badge, chapter_card, draw_text, footer,
                   legend_strip, rounded, text_size, transparent)

MG, CLIPS, OVL = BUILD / "mg", BUILD / "clips", BUILD / "overlays"
MG_SHOTS = {"S01": "S01", "S05": "S05", "S06": "S06", "S07": "S07", "S10": "S10", "S11": "S11", "S13": "S13",
            "S14": "S14", "S16": "S16", "S17": "S17", "S17b": "S17b", "S18": "S18", "S19": "S19", "S20": "S20"}


def solid_footer(img, text: str) -> None:
    """The source footer (style.footer, one line, at most 1150 px) on a solid navy backing, so it stays
    readable over a busy capture."""
    w, _ = text_size(text, 20, 500)
    assert w <= 1150, f"footer is {w} px, over the 1150 px slot: {text}"
    rounded(img, (46, 1026, 60 + w + 14, 1066), 8, fill=NAVY)
    footer(img, text)


def badge_solid_sub(img, kind: str, detail: str, sub: str) -> None:
    """The status badge with its one-line sub-line on a solid navy backing (style.badge's own backing is
    78% opaque, which lets the captured page show through)."""
    badge(img, kind, detail)
    sw, _ = text_size(sub, 20, 500)
    rounded(img, (1860 - sw - 16, 100, 1868, 132), 8, fill=NAVY)
    draw_text(img, (1860 - sw, 106), sub, 20, 500, INK_2)


def legend_docked(img, band_top: int | None = None) -> None:
    """The evidence legend docked bottom-right (style.legend_strip, script section 6: S10-S16) on a solid
    navy backing, so the pills read over a light capture: its own rounded backing, or with band_top a
    full-width navy band from that y down, which also carries the footer."""
    layer = transparent()
    legend_strip(layer)
    x0, y0, x1, y1 = layer.getbbox()
    if band_top is not None:
        assert band_top <= y0 - 6, (band_top, y0)
        rounded(img, (-20, band_top, 1940, 1100), 1, fill=NAVY)
    else:
        rounded(img, (x0 - 10, y0 - 6, x1 + 10, y1 + 6), 12, fill=NAVY)
    img.alpha_composite(layer)


SEG = BUILD / "cut" / "segments"


def spec(sid: str, *texts: str) -> None:
    """Asserts that each on-screen string is in the shot's on_screen_text in docs/video/shotlist.json, so the
    overlays cannot drift from the spec."""
    import json
    from assemble import SHOTLIST
    want = next(x for x in json.loads(SHOTLIST.read_text()) if x["id"] == sid)["on_screen_text"]
    for t in texts:
        assert t in want, f"{sid}: {t!r} is not in the shotlist's on_screen_text"


def segments(name: str, src: Path, parts: list[tuple]) -> Path:
    """Cuts parts out of a 1920x1080 recording and joins them: each part is (t0, t1, box_from,
    box_to), a box being (x, y, w) in source pixels with a 16:9 height; the view eases from
    box_from to box_to over the part (same box = static crop). An optional fifth item, cut_y, turns
    the picture below source y cut_y navy and extends the canvas with navy below and to the right
    (to 2240x1260), so a box may reach past the recording's bottom edge: the picture then ends above
    the caption band on a navy letterbox. Returns the base clip."""
    import subprocess
    SEG.mkdir(parents=True, exist_ok=True)
    out = SEG / f"{name}.mp4"
    chains, labels = [], []
    for i, (t0, t1, (x0, y0, w0), (x1, y1, w1), *opt) in enumerate(parts):
        n = max(1, int(round((t1 - t0) * 30)))
        k = f"(1-cos(PI*min(on/{n},1)))/2"  # eased progress 0 -> 1
        zw = f"({w0}+({w1}-{w0})*{k})"
        pw, pre = 1920, ""
        if opt:
            pw = 2240
            pre = f"crop=1920:{opt[0]}:0:0,pad=2240:1260:0:0:color=0x0B1220,"
            assert y0 + w0 * 9 / 16 <= 1260 and y1 + w1 * 9 / 16 <= 1260, "box runs off the extended canvas"
        chains.append(f"[0:v]trim={t0}:{t1},setpts=PTS-STARTPTS,fps=30,{pre}"
                      f"zoompan=z='{pw}/{zw}':x='{x0}+({x1}-{x0})*{k}':y='{y0}+({y1}-{y0})*{k}':d=1:s=1920x1080:fps=30,setsar=1[p{i}]")
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
    # Simulator screen scaled to full height at x 383-880, where the S02 overlay expects it. The source is
    # S02_sim.mp4 from 5.0 s with every head in the app's camera picture mosaicked (video/mask_s02.py).
    masked = CLIPS / "S02_sim_masked.mp4"
    if not masked.exists():
        raise SystemExit("S02 needs video/build/clips/S02_sim_masked.mp4: run video/mask_s02.py (faces must be masked)")
    return (["-i", str(masked)], [], [(OVL / "S02.mov", 0.0)],
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
    """C2a (13 Oct): Live map until the Senado click (101.5 s); the sidebar fills, the page jumps down at
    103.62 s so the sidebar's forecast rows and reasons are in view, 'open zone detail' at 105.2 s, Zone
    detail (WARNING) from 105.4 s, the zone CRITICAL from about 111 s, the +5 / +10 rows CRITICAL and confident
    from 116.2 s (14:10:05 sim). Zone detail never scrolls, so its own WHY list is never on screen: the
    'why' beat is the sidebar's reason list (the dashboard's Reasons for the first forecast row, +5 min,
    WARNING at 76% confidence), after the lower-third (0.2-3.2 s). Beats keyed to the guide voice's
    pauses (voice from 0.2 s): 'Senado Square's forecast' about 3.6-5.2 s, 'turns critical' about 5.3-6.3 s,
    'with a confidence score and the reasons why' 6.5-8.9 s; re-key to the real take."""
    c2a = CLIPS / "C2a.mp4"
    # side: the sidebar's reasons (source y 735-970) with the +15 row's probability line above them, from
    # just under that row's LOW CONFIDENCE banner (y 603-659), so the badge sits on empty page.
    # rows: the Prediction panel's +5 and +10 rows (source y 874-1066) end at output y 871; the picture
    # below source y 1069 (the +15 row's top edge) is navy, so the caption band (y 920-990) sits on navy.
    side, rows = (1180, 663, 740), (300, 576, 1080)
    base = segments("S03", c2a, [
        (100.4, 101.4, FULL, FULL),                 # 0.0-1.0: Live map, Senado amber
        (101.6, 103.5, FULL, (760, 120, 1160)),     # 1.0-2.9: click Senado; the sidebar fills
        (103.7, 105.2, side, side),                 # 2.9-4.4: forecast rows' probabilities and the reasons
        (105.5, 106.4, FULL, FULL),                 # 4.4-5.3: Zone detail opens (WARNING)
        (111.6, 112.6, FULL, FULL),                 # 5.3-6.3: the zone turns CRITICAL
        (116.2, 117.2, FULL, rows, 1069),           # 6.3-7.3: zoom in to the forecast rows (CRITICAL, with confidence)
        (117.2, 119.9, rows, rows, 1069),           # 7.3-10.0: held still so the callouts sit beside the rows, not on them
    ])
    x0, y0 = to_out(side, 1382, 722); x1, y1 = to_out(side, 1858, 983)
    assert 132 < y0 and y1 < 900, (y0, y1)  # under the badge sub-line, above the caption band
    spec("S03", "LIVE SOFTWARE · SIMULATED CROWD", "Simulated Golden Week afternoon · SIM CLOCK, 10× speed", "+5 / +10 / +15 min",
         "confidence", "why", "Footer: Map © OpenStreetMap contributors")
    hy = to_out(rows, 0, 847)[1] - 25  # the Prediction panel's header line ('Prediction updated …')
    ov = [
        (png("S03_badge", lambda img: badge_solid_sub(img, "LIVE SOFTWARE", "SIMULATED CROWD", "Simulated Golden Week afternoon · SIM CLOCK, 10× speed")), 0.0, dur),
        # from after the lower-third (0.2-3.2 s) to the cut to Zone detail
        (png("S03_why", lambda img: (highlight(img, (x0, y0, x1, y1)), callout(img, x0, y0 - 60, "why"))), 3.3, 4.4),
        # in the Prediction panel's header line, right of "Prediction updated …", clear of the rows' probabilities
        (png("S03_rows", lambda img: (callout(img, 580, hy, "+5 / +10 / +15 min"), callout(img, 900, hy, "confidence"))), 7.3, dur),
        # while the map (or its corner, in the sidebar crop) is on screen
        (png("S03_footer", lambda img: footer(img, "Map © OpenStreetMap contributors")), 0.0, 4.4),
    ]
    return ["-i", str(base)], ov, [], ""


def gloss_panel(img) -> None:
    """S04 notice beat: the languages, an English gloss of the zh and pt notices' openings, and the English
    notice's closing AI clause (backend/app/services/intervention.py AI_NOTICE["en"]; the zh and pt notices
    end with the same clause in their language), so a viewer with the sound off sees that the notice says
    an AI forecast is involved. On a solid panel over the card's title (already shown in the route beat),
    clear of the notice lines and the buttons."""
    rows = [("zh", [("議事亭前地目前非常擁擠…", 600, INK), ("(Senado Square is very crowded…)", 500, INK_2)]),
            ("pt", [("Largo do Senado: grande afluência de visitantes…", 600, INK), ("(Senado Square: many visitors…)", 500, INK_2)]),
            ("en", [("… ends:", 500, INK_2), ("Advice from an AI crowd forecast, approved by staff.", 600, INK)])]
    widths = [text_size(f"{tag}  " + "  ".join(t for t, _, _ in parts), 26, 600)[0] for tag, parts in rows]
    assert max(widths) < 1700, widths
    x0, y0 = 12, 100  # y 100-312, x 12-1908: covers the card's title, summary and route line whole, ends above the green line
    rounded(img, (x0, y0, 1908, 312), 16, fill=NAVY, outline=CYAN, width=3)
    x0 = 40
    draw_text(img, (x0 + 34, y0 + 18), "中文 · English · Português", 28, 700, CYAN)
    for i, (tag, parts) in enumerate(rows):
        y = y0 + 70 + i * 46  # last row's text ends about y 296, above the panel's edge at 312
        draw_text(img, (x0 + 30, y), tag, 26, 700, CYAN)
        tx = x0 + 30 + text_size(tag, 26, 700)[0] + 18
        for text, weight, colour in parts:
            draw_text(img, (tx, y), text, 26, weight, colour)
            tx += text_size(text, 26, weight)[0] + 16


def s04(dur: float):
    """C2b2 (16-17 Oct re-capture, video/shots/C2b2.json): one fresh backend run with the Simulator phone
    joined at Almeida (node-9970c1); 'Deciding as' = demo-operator-1; Senado card #6 created 14:09:50 sim
    (110.8 s into the clip), notice opened 115.1 s, evidence 120.2 s, scroll back to the 'Deciding as' field
    122.5-123.3 s, APPROVE clicked at 126.72 s (14:12:35 sim in the audit log; 7.23 s into S04), Decided list and audit log
    from 136.8 s. Beats are keyed to the guide voice (voice from 0.2 s): 'stair-free detour' ends 2.1 s,
    'notices in Chinese, English and Portuguese' 2.3-5.4 s, 'A person decides' 5.6-6.9 s, 'approved' 7.1 s,
    'and logged' 7.9-8.5 s; re-key to the real take."""
    b2 = CLIPS / "C2b2.mp4"
    spec("S04", "LIVE SOFTWARE · SIMULATED CROWD", "accessibility check: this route avoids stairs", "中文 · English · Português",
         "needs a person's approval", "audit log", "zh 議事亭前地目前非常擁擠… (Senado Square is very crowded…)",
         "pt Largo do Senado: grande afluência de visitantes… (Senado Square: many visitors…)",
         "click scripted for this recording · the approval runs the real code path")
    route, notice, ev, appr, log = (335, 231, 1510), (320, 214, 1540), (330, 470, 1060), (300, 40, 1580), (322, 0, 1035)
    base = segments("S04", b2, [
        (111.8, 113.0, FULL, route),   # 0.0-1.2: 'Deciding as' field and the Senado card; ease in to
        (113.0, 114.0, route, route),  # 1.2-2.2: the route line ('no stairs') and the green accessibility line
        (115.4, 118.6, notice, notice),  # 2.2-5.4: zh / en / pt notice, each ending with the AI clause
        (121.2, 122.2, ev, ev),        # 5.4-6.4: buttons and the evidence bullets
        (125.9, 126.9, appr, appr),    # 6.4-7.4: 'Deciding as demo-operator-1' and the scripted APPROVE click (7.23 s)
        (137.5, 139.1, log, log),      # 7.4-9.0: Decided 'approved … by demo-operator-1'; audit log 'demo-operator-1 · intervention_approved'
    ])
    ov = [
        (png("S04_badge", lambda img: badge(img, "LIVE SOFTWARE", "SIMULATED CROWD")), 0.0, dur),
        (png("S04_c1", lambda img: callout(img, 720, 556, "accessibility check: this route avoids stairs")), 1.2, 2.2),
        (png("S04_c2", gloss_panel), 2.4, 5.4),
        # beside the button row, right of 'deciding as demo-operator-1' and under the badge (not in the Evidence panel)
        (png("S04_c3a", lambda img: callout(img, 1396, 108, "needs a person's approval")), 5.5, 6.4),
        (png("S04_c3b", lambda img: callout(img, 990, 802, "needs a person's approval")), 6.4, 7.4),
        (png("S04_c4", lambda img: (callout(img, 200, 640, "audit log"), highlight(img, (450, 722, 1064, 836)))), 7.5, dur),
        # from the APPROVE click (the pointer rests on the button from 6.95 s; it presses at 7.23 s) to the end
        (png("S04_footer", lambda img: solid_footer(img, "click scripted for this recording · the approval runs the real code path")), 7.1, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def strip(name: str, src: Path, t0: float, t1: float, box: tuple[int, int, int, int], y_out: int) -> Path:
    """Cuts t0-t1 out of a 1920x1080 recording, crops box (x, y, w, h) in source pixels, scales it to the
    full 1920 px width and sets it at y_out on navy (a letterboxed strip, for a panel that is wide and short)."""
    import subprocess
    SEG.mkdir(parents=True, exist_ok=True)
    out = SEG / f"{name}.mp4"
    x, y, w, h = box
    assert 1920 * h / w + y_out <= 1080, "strip runs off the frame"
    vf = (f"trim={t0}:{t1},setpts=PTS-STARTPTS,fps=30,crop={w}:{h}:{x}:{y},scale=1920:-2,"
          f"pad=1920:1080:0:{y_out}:color=0x0B1220,setsar=1")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vf", vf, "-c:v", "libx264", "-crf", "16",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def s09(dur: float):
    # tail2: only the C2b2 'Decided / expired' list (approved #6, then the superseded 'Increase monitoring …',
    # 'Deploy staff …' rows; source y 0-330, above the 'Audit log' heading at y 345), as a strip on navy, so
    # S09 does not repeat S04's closing picture of the same list over the audit log.
    rows = (300, 470, 1080)
    tail = segments("S09_tail", CLIPS / "C2a.mp4", [(107.0, 109.5, rows, rows)])
    tail2 = strip("S09_tail2", CLIPS / "C2b2.mp4", 137.6, 139.1, (316, 0, 1576, 330), 190)
    base = concat_clips("S09", [MG / "S09_mg.mp4", tail, tail2])
    spec("S09", "Stronger recommendations replace weaker pending ones")
    ov = [
        (png("S09_live", lambda img: badge(img, "LIVE SOFTWARE", "dashboard")), 4.0, dur),
        (png("S09_rows", lambda img: callout(img, 980, 160, "LOW CONFIDENCE — HUMAN REVIEW REQUIRED", (245, 166, 35))), 4.2, 6.5),
        (png("S09_dec", lambda img: callout(img, 541, 650, "Stronger recommendations replace weaker pending ones")), 6.5, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def s12(dur: float):
    # README_insert.mp4 (re-captured 17 Oct from the current README.md, video/shots/readme_insert.json):
    # the page settles at 3.4 s with the Correction paragraph at y 171-388, x 528-1384, 30 px below the
    # previous paragraph, so the highlight box has room above and below it.
    spec("S12", "Badge (top-right): CORRECTED", "Footer: README.md · Correction")
    readme = segments("S12_readme", CLIPS / "README_insert.mp4", [(3.6, 5.6, FULL, FULL)])
    base = concat_clips("S12", [MG / "S12_mg.mp4", readme])
    # The README page is white, so from the cut the footer and the docked evidence legend (S10-S16) sit on a
    # navy band from y 977, in the gap between two text lines (y 950-970 and 985-1007) of the Limitations
    # list below the highlighted paragraph; the S12 motion graphic before the cut docks the same legend.
    ov = [
        (png("S12_hl", lambda img: highlight(img, (506, 150, 1408, 410))), 8.2, dur),
        (png("S12_badge", lambda img: badge(img, "CORRECTED")), 8.0, dur),
        (png("S12_legend", lambda img: legend_docked(img, band_top=977)), 8.0, dur),
        (png("S12_footer", lambda img: footer(img, "README.md · Correction")), 8.0, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def s15_panel(img, stage: int) -> None:
    """S15 counters (stage 0, from the walkers line) and the 40-dot grid of simulated wheelchair users: at
    stage 1 all 40 dots are wheelchair purple, at stage 2 the 24 with no step-free route in either plan turn
    grey (shotlist S15: 'a 40-dot grid in which 24 dots turn grey'; the 16 who arrive in both plans stay
    purple) and the dot-grid lines appear. Numbers: sketchfuture/VERIFICATION.md (#721: wheelchair 16/40
    arrive in both plans, 24 have no step-free route in either; walkers 40/40, strollers 28/40), matching
    the captured plan's walker and wheelchair cards (40/40, 16/40, '24 人無可用路線')."""
    purple, grey = (118, 88, 181), (98, 113, 138)
    rounded(img, (40, 170, 900, 808 if stage else 536), 22, fill=(11, 18, 32))  # solid: SketchFuture's cards sit behind it
    draw_text(img, (76, 196), "same 120 simulated people, with vs without the closure", 26, 600, INK)
    for i, (who, val, col) in enumerate([("walkers", "+17 s", (36, 124, 118)), ("wheelchair users", "+30 s", purple), ("stroller users", "+21 s", (206, 103, 68))]):
        y = 250 + i * 70
        rounded(img, (76, y, 96, y + 40), 6, fill=col)
        draw_text(img, (114, y + 2), who, 30, 600, INK)
        draw_text(img, (860, y + 2), val, 34, 800, INK, anchor="ra")
    draw_text(img, (76, 466), "averages over those who arrive in both plans: walkers 40/40 · wheelchair users 16/40 · stroller users 28/40", 21, 500, INK_2, max_width=800)
    if stage:
        d = ImageDraw.Draw(img)
        for k in range(40):
            cx, cy = 96 + (k % 10) * 46, 580 + (k // 10) * 46
            d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=grey if stage == 2 and k >= 16 else purple)
    if stage == 2:
        draw_text(img, (580, 572), "24 of 40 wheelchair users: no step-free route in EITHER plan", 24, 700, INK, max_width=300)
        draw_text(img, (580, 700), "missing map detail or real barriers? Needs a site survey.", 22, 500, INK_2, max_width=300)


def s15(dur: float):
    """C2c (13 Oct capture): the St. Dominic's card is still until 4.2 s (TEST IN SKETCHFUTURE clicked
    within it), a blank page at 4.23 s, SketchFuture loaded and compared by 5.1 s, then still. Beats keyed to
    the guide voice (from 0.2 s): 'walkers lose seventeen seconds' 6.2 s, 'And 24 of our 40' 10.1 s.
    The picture is letterboxed to 1760x990 on navy, so the footer and the docked evidence legend (S10-S16)
    sit on the navy strip below it, and SketchFuture's own map legend and OpenStreetMap credit, at the
    picture's bottom edge, stay uncovered."""
    c2c = CLIPS / "C2c.mp4"
    spec("S15", "MODEL CHECK · synthetic cohort", "same 120 simulated people, with vs without the closure",
         "walkers +17 s · wheelchair users +30 s · stroller users +21 s",
         "averages over those who arrive in both plans: walkers 40/40 · wheelchair users 16/40 · stroller users 28/40",
         "24 of 40 wheelchair users: no step-free route in EITHER plan · missing map detail or real barriers? Needs a site survey.",
         "Footer: Map © OpenStreetMap contributors, ODbL · example run #721, sketchfuture/VERIFICATION.md")
    # card: y 62-765, between the card above and this card's 'Decided / expired' list, which in this 13 Oct
    # capture still shows the pre-'Deciding as' actor 'by operator' (the backend now refuses that name).
    card, results = (300, 62, 1250), (1000, 330, 920)
    base = segments("S15", c2c, [
        (1.8, 4.2, card, card),        # 0.0-2.4: St. Dominic's card; TEST IN SKETCHFUTURE clicked
        (4.9, 7.0, FULL, FULL),        # 2.4-4.5: SketchFuture opens the plan and compares
        (7.0, 13.0, FULL, results),    # 4.5-10.5: walker and wheelchair results
        (13.0, 18.8, results, FULL),   # 10.5-16.3: back out to the whole plan (held to the end)
    ])
    ov = [
        (png("S15_badge", lambda img: badge(img, "MODEL CHECK", "synthetic cohort")), 0.0, dur),
        (png("S15_counters", lambda img: s15_panel(img, 0)), 6.0, 9.9),
        (png("S15_dots40", lambda img: s15_panel(img, 1)), 9.9, 10.6),  # 'And 24 of our 40': the 40 dots, then
        (png("S15_dots", lambda img: s15_panel(img, 2)), 10.6, dur),     # 24 of them turn grey
        (png("S15_footer", lambda img: solid_footer(img, "Map © OpenStreetMap contributors, ODbL · example run #721, sketchfuture/VERIFICATION.md")), 0.0, dur),
        (png("S15_legend", legend_docked), 0.0, dur),
    ]
    return ["-i", str(base)], ov, [], "scale=1760:990,pad=1920:1080:80:0:color=0x0B1220"


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
