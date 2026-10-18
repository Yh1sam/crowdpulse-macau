"""Per-shot recipes for video/assemble.py: which source each shot uses, how it is framed, and which
overlays sit on it. recipe(shot, duration) -> (ffmpeg input args, [(png, start, end)], [(alpha mov,
offset)], pre-filter). Times are seconds from the start of the shot; re-key them to the team's takes.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw

from assemble import png, probe_duration
from style import (BUILD, INK, INK_2, NAVY, SAFE, WARNING, CRITICAL, badge, chapter_card, draw_text, footer,
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
    # Simulator screen scaled to full height at x 440-937 and raised 16 px (the white strip above its status
    # bar cropped), where the S02 overlay expects it (video/mg/S02.py PHONE): right of the chapter card
    # (x 60-425), and with the app's Stop button ending at y 790, above the lower-third (y 800-890). The
    # source is S02_sim.mp4 from 5.0 s with every head in the app's camera picture mosaicked (video/mask_s02.py).
    masked = CLIPS / "S02_sim_masked.mp4"
    if not masked.exists():
        raise SystemExit("S02 needs video/build/clips/S02_sim_masked.mp4: run video/mask_s02.py (faces must be masked)")
    return (["-i", str(masked)], [], [(OVL / "S02.mov", 0.0)],
            "scale=-2:1080,crop=iw:ih-16:0:16,pad=1920:1080:440:0:color=0x0B1220")


def s08(dur: float):
    """The real terminal session (video/build/clips/S08.mp4, drawn from S08.cast): each command and its code
    appear together (code 0.02-0.06 s after the command, at 1.63 / 3.97 / 5.82 s in the take). Each stamp lands
    on its verb in the guide voice (voice from 0.2 s): 'accepts' 2.85 s, 'rejects' 4.77 s, 'refuses' 7.5 s. So
    that each code shows just before its stamp (the take was timed to the old lines), idle prompt time between
    the commands is cut or repeated. Nothing else changes: every command keeps its response and its latency as
    recorded, and each splice joins two frames of the same screen, so the only difference is the blinking
    cursor's rhythm at the three splices (on 0.7 s once, on or off 0.3 s three times, instead of 0.5 s). The codes
    show at 2.83 / 4.80 / 7.43 s, 0.10-0.12 s before their stamps.
    The take is raised 30 px (its top 30 px are empty navy), so the terminal window (y 170-775) ends 25 px above
    [MEMBER 3]'s lower-third (y 800-890, 0.2-3.2 s; S08 is that member's first voice-over shot).
    On screen (19 Oct declutter): the chapter card, the plain LIVE SOFTWARE badge and three short stamps (a code,
    its verb and at most two words); no footer (the checks' test file is in script.md section 4)."""
    spec("S08", "Badge (top-right): LIVE SOFTWARE (cyan)", "202 accepted · numbers only", "422 rejected · face-ID field",
         "403 refused · image upload")
    take = segments("S08", CLIPS / "S08.mp4", [
        (0.0, 1.4, FULL, FULL),     # 0.0-1.4: the prompt (cursor on 1.0-1.5 s)
        (0.2, 2.3, FULL, FULL),     # 1.4-3.5: the prompt again from 0.2 s (cursor on 0.7 s once); command 1 and 202 at 2.83
        (2.7, 5.0, FULL, FULL),     # 3.5-5.8: 0.4 s of prompt skipped; command 2 and 422 at 4.80
        (4.2, 7.4, FULL, FULL),     # 5.8-9.0: 0.8 s of prompt repeated; command 3, its message and 403 at 7.43
    ])
    ov = [
        (png("S08_card", lambda img: chapter_card(img, "Can it be trusted?")), 0.0, 2.0),
        (png("S08_badge", lambda img: badge(img, "LIVE SOFTWARE")), 0.0, dur),
        (png("S08_s1", lambda img: stamp(img, 300, 311, "202 accepted · numbers only", SAFE)), 2.95, dur),    # "accepts"
        (png("S08_s2", lambda img: stamp(img, 300, 416, "422 rejected · face-ID field", WARNING)), 4.9, dur),  # "rejects"
        (png("S08_s3", lambda img: stamp(img, 300, 556, "403 refused · image upload", CRITICAL)), 7.55, dur),  # "refuses"
    ]
    return ["-i", str(take)], ov, [], "crop=1920:1050:0:30,pad=1920:1080:0:0:color=0x0B1220"


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
    WARNING at 76% confidence), from the cut to it (S03 has no lower-third since 19 Oct: [MEMBER 2]'s is on
    S09). Beats keyed to the guide voice's
    pauses (voice from 0.2 s): 'with a simulated Golden Week crowd' 1.4-3.4 s, 'Senado Square's forecast' about
    3.6-5.5 s, 'turns critical' about 5.7-6.3 s, 'It shows how sure it is' 6.55-8.0 s ('how sure' about
    7.05-7.6 s: the '+5 / +10 / +15 min' and 'how sure' callouts, once the zoom to the rows has settled),
    'and why' 8.2-8.8 s. The 'why' highlight cannot move to 'and why': the capture shows the reasons only
    before Zone detail opens, and cutting back to them after the CRITICAL rows would run the SIM CLOCK
    backwards and pair a WARNING-time reason list with CRITICAL rows; it stays on 'crowd, Senado Square's'.
    On screen (19 Oct declutter): the plain badge (no sub-line: the caption says 'simulated Golden Week crowd'
    and the captured status bar shows the SIM CLOCK), the three callouts the voice names and the map credit.
    Re-key to the real take."""
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
    bx0 = 1860 - text_size("LIVE SOFTWARE · SIMULATED CROWD", 24, 700)[0] - 44  # the badge's left edge (style.badge)
    # the 'why' pill (y0 - 60 to y0 - 10) left of the badge (y 48-94), the box above the caption band
    assert y0 - 60 > 0 and x0 + text_size("why", 28, 700)[0] + 40 < bx0 and y1 < 900, (x0, y0, y1, bx0)
    spec("S03", "Badge (top-right): LIVE SOFTWARE · SIMULATED CROWD |", "Callouts: why · +5 / +10 / +15 min · how sure",
         "Footer: Map © OpenStreetMap contributors")
    hy = to_out(rows, 0, 847)[1] - 25  # the Prediction panel's header line ('Prediction updated …')
    ov = [
        (png("S03_badge", lambda img: badge(img, "LIVE SOFTWARE", "SIMULATED CROWD")), 0.0, dur),
        # from just after the cut to the sidebar crop (2.9 s) to the cut to Zone detail
        (png("S03_why", lambda img: (highlight(img, (x0, y0, x1, y1)), callout(img, x0, y0 - 60, "why"))), 3.0, 4.4),
        # in the Prediction panel's header line, right of "Prediction updated …", clear of the rows' probabilities;
        # on "how sure", as the zoom settles; "how sure" stands over the rows' "…% confidence" chips
        (png("S03_rows", lambda img: (callout(img, 580, hy, "+5 / +10 / +15 min"), callout(img, 900, hy, "how sure"))), 7.3, dur),
        # while the map (or its corner, in the sidebar crop) is on screen
        (png("S03_footer", lambda img: footer(img, "Map © OpenStreetMap contributors")), 0.0, 4.4),
    ]
    return ["-i", str(base)], ov, [], ""


def s04(dur: float):
    """C2b2 (16-17 Oct re-capture, video/shots/C2b2.json): one fresh backend run with the Simulator phone
    joined at Almeida (node-9970c1); 'Deciding as' = demo-operator-1; Senado card #6 created 14:09:50 sim
    (110.8 s into the clip), notice opened 115.1 s, evidence 120.2 s, scroll back to the 'Deciding as' field
    122.5-123.3 s, APPROVE clicked at 126.72 s (14:12:35 sim in the audit log; 7.23 s into S04), Decided list and audit log
    from 136.8 s. Beats are keyed to the guide voice (voice from 0.2 s): 'stair-free detour' 1.1-2.1 s,
    'with notices in Chinese, English and Portuguese' 2.3-5.4 s, 'A person must approve it' 5.6-7.0 s ('approve'
    about 6.3-6.7 s; the scripted click lands at 7.23 s, on 'and we'), 'and we log their name' 7.2-8.4 s
    ('log' about 7.6 s, 'their name' about 7.9-8.4 s); re-key to the real take.
    On screen (19 Oct declutter): the badge, one callout at a time on the words it names ('no stairs' over the
    card's own 'no stairs', the three language names over the opened notice, 'needs a person's approval'), a
    plain highlight on the audit row's name (the page's own 'Audit log' heading names it), and from the click to
    the end the 'Scripted click' note. No English gloss of the notices: the caption says what they are."""
    b2 = CLIPS / "C2b2.mp4"
    spec("S04", "Badge (top-right): LIVE SOFTWARE · SIMULATED CROWD |", "no stairs", "中文 · English · Português",
         "needs a person's approval", "Footer (small, from the APPROVE click to the end of the shot): Scripted click")
    route, notice, ev, appr, log = (335, 231, 1510), (320, 214, 1540), (330, 470, 1060), (300, 40, 1580), (322, 0, 1035)
    base = segments("S04", b2, [
        (111.8, 112.8, FULL, route),   # 0.0-1.0: 'Deciding as' field and the Senado card; ease in to
        (112.8, 114.0, route, route),  # 1.0-2.2: the route line ('no stairs') and the green accessibility line
        (115.4, 118.6, notice, notice),  # 2.2-5.4: zh / en / pt notice, each ending with the AI clause
        (121.2, 122.2, ev, ev),        # 5.4-6.4: buttons and the evidence bullets
        (125.9, 126.9, appr, appr),    # 6.4-7.4: 'Deciding as demo-operator-1' and the scripted APPROVE click (7.23 s)
        (137.5, 139.1, log, log),      # 7.4-9.0: Decided 'approved … by demo-operator-1'; audit log 'demo-operator-1 · intervention_approved'
    ])
    ov = [
        (png("S04_badge", lambda img: badge(img, "LIVE SOFTWARE", "SIMULATED CROWD")), 0.0, dur),
        # "stair-free detour" (1.1-2.1 s): the route line's own "no stairs" boxed, the pill at that line's end,
        # above the green accessibility line; up 1.2 s (2 words: at least 1.1 s)
        (png("S04_c1", lambda img: (highlight(img, (1072, 444, 1184, 484)), callout(img, 1490, 436, "no stairs", size=26))), 1.0, 2.2),
        # "with notices in Chinese, English and Portuguese": right of the opened 'Public notice (…)' line, above the ZH line
        (png("S04_c2", lambda img: callout(img, 1060, 374, "中文 · English · Português")), 2.4, 5.4),
        # beside the button row, right of 'deciding as demo-operator-1' and under the badge (not in the Evidence panel)
        (png("S04_c3a", lambda img: callout(img, 1396, 108, "needs a person's approval")), 5.5, 6.4),
        (png("S04_c3b", lambda img: callout(img, 990, 802, "needs a person's approval")), 6.4, 7.4),
        (png("S04_c4b", lambda img: highlight(img, (450, 722, 1064, 836))), 7.9, dur),             # "their name": demo-operator-1's row
        # from the APPROVE click (the pointer rests on the button from 6.95 s; it presses at 7.23 s) to the end; in the
        # footer slot, a step brighter and larger than a source footer (INK_2, 22 px), as it is a required note
        (png("S04_footer", lambda img: (rounded(img, (46, 1022, 60 + text_size("Scripted click", 22, 600)[0] + 14, 1066), 8, fill=NAVY),
                                        draw_text(img, (60, 1031), "Scripted click", 22, 600, INK_2))), 7.1, dur),
    ]
    return ["-i", str(base)], ov, [], ""


def s09(dur: float):
    # From the cut at 5.0 s (video/mg/S09.py DURATION) to the end: C2a's Zone detail Prediction panel at 14:08:28
    # sim (source 107.0-111.0 s; the panel does not change in that window): +5 min WARNING at 63% confidence,
    # and the +10 min row with the dashboard's own LOW CONFIDENCE — HUMAN REVIEW REQUIRED badge, zoomed (2.3x) so
    # that badge reads without a callout. The picture below source y 1068 (a cut-off 'density' line) is navy, so
    # the caption band sits on navy. On "a person must review it" (7.05 s) a plain highlight frames that badge.
    # 19 Oct declutter: the "Decided / expired" strip and its callouts ("Stronger recommendations replace weaker
    # pending ones", a duplicate LOW CONFIDENCE pill) are gone: neither is spoken, and the strip showed S04's
    # approval before S04 makes it.
    panel = (280, 790, 830)  # source x 280-1110 (the Prediction panel, left of Sensor reliability), y 790-1257 on the extended canvas
    tail = segments("S09_tail", CLIPS / "C2a.mp4", [(107.0, 111.0, panel, panel, 1068)])
    base = concat_clips("S09", [MG / "S09_mg.mp4", tail])
    spec("S09", "Dashboard (from the cut): Badge (top-right): LIVE SOFTWARE · dashboard",
         "a highlight box on the dashboard's own LOW CONFIDENCE — HUMAN REVIEW REQUIRED badge")
    x0, y0 = to_out(panel, 362, 1029); x1, y1 = to_out(panel, 846, 1062)  # the badge in source pixels
    assert y1 + 12 < to_out(panel, 0, 1068)[1], (y1, "the highlight ends above the navy cut")
    ov = [
        (png("S09_live", lambda img: badge(img, "LIVE SOFTWARE", "dashboard")), 5.0, dur),   # from the cut
        (png("S09_hl", lambda img: highlight(img, (x0 - 12, y0 - 12, x1 + 12, y1 + 12))), 7.0, dur),  # "a person must review it"
    ]
    return ["-i", str(base)], ov, [], ""


S12_CUT = 7.0  # = video/mg/S12.py DURATION: the cut to the README insert, as M2's line ends on "correction" (guide voice)


def s12(dur: float):
    # S12 was dropped from the cut on 19 Oct (no shotlist entry, so assemble.py never calls this); kept for reference.
    # README_insert.mp4 (re-captured 17 Oct from the current README.md, video/shots/readme_insert.json):
    # the page settles at 3.4 s with the Correction paragraph at y 171-388, x 528-1384, 30 px below the
    # previous paragraph, so the highlight box has room above and below it; it is 7.6 s long, still from 3.4 s.
    spec("S12", "Badge (top-right): CORRECTED", "Footer: README.md · Correction")
    mg = MG / "S12_mg.mp4"
    assert abs(probe_duration(mg) - S12_CUT) < 0.02, f"{mg} is {probe_duration(mg)} s, not {S12_CUT} s: re-render video/mg/S12.py"
    readme = segments("S12_readme", CLIPS / "README_insert.mp4", [(3.6, round(3.6 + dur - S12_CUT, 3), FULL, FULL)])  # 2.0 s
    base = concat_clips("S12", [mg, readme])
    # The README page is white, so from the cut the footer and the docked evidence legend (S10-S16) sit on a
    # navy band from y 977, in the gap between two text lines (y 950-970 and 985-1007) of the Limitations
    # list below the highlighted paragraph; the S12 motion graphic before the cut docks the same legend.
    ov = [
        (png("S12_hl", lambda img: highlight(img, (506, 150, 1408, 410))), S12_CUT + 0.2, dur),
        (png("S12_badge", lambda img: badge(img, "CORRECTED")), S12_CUT, dur),
        (png("S12_legend", lambda img: legend_docked(img, band_top=977)), S12_CUT, dur),
        (png("S12_footer", lambda img: footer(img, "README.md · Correction")), S12_CUT, dur),
    ]
    return ["-i", str(base)], ov, [], ""


S15_HEADER, S15_HEDGE = "with vs without the closure", "averages over arrivals in both plans"
S15_DOTS = "24 of 40: no step-free route either way"


def s15_panel(img, stage: int) -> None:
    """S15 overlay on a solid panel at the left (SketchFuture's map and cards sit behind it), one idea at a time.
    Stage 0 (the walkers / wheelchair users sentence): the header, the three counters and a one-line hedge that
    the averages cover only those who arrive in both plans. Stages 1-2 ('And 24 of our 40 …'): the counters give
    way to the 40-dot grid of simulated wheelchair users: at stage 1 all 40 dots are wheelchair purple, at stage
    2 the 24 with no step-free route in either plan turn grey (shotlist S15: 'a 40-dot grid in which 24 dots turn
    grey'; the 16 who arrive in both plans stay purple) and its label appears. Numbers: sketchfuture/VERIFICATION.md
    (#721: wheelchair 16/40 arrive in both plans, 24 have no step-free route in either; walkers 40/40, strollers
    28/40; those counts left the screen on 19 Oct and are kept for Q&A), matching the captured plan's walker and
    wheelchair cards (40/40, 16/40, '24 人無可用路線')."""
    purple, grey = (118, 88, 181), (98, 113, 138)
    if stage == 0:
        rounded(img, (40, 170, 900, 520), 22, fill=(11, 18, 32))  # solid: SketchFuture's cards sit behind it
        draw_text(img, (76, 196), S15_HEADER, 26, 600, INK_2)
        for i, (who, val, col) in enumerate([("walkers", "+17 s", (36, 124, 118)), ("wheelchair users", "+30 s", purple), ("stroller users", "+21 s", (206, 103, 68))]):
            y = 250 + i * 70
            rounded(img, (76, y, 96, y + 40), 6, fill=col)
            draw_text(img, (114, y + 2), who, 30, 600, INK)
            draw_text(img, (860, y + 2), val, 34, 800, INK, anchor="ra")
        draw_text(img, (76, 466), S15_HEDGE, 22, 500, INK_2)
        return
    rounded(img, (40, 170, 900, 412), 22, fill=(11, 18, 32))
    d = ImageDraw.Draw(img)
    for k in range(40):
        cx, cy = 96 + (k % 10) * 46, 222 + (k // 10) * 46
        d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=grey if stage == 2 and k >= 16 else purple)
    if stage == 2:
        # the label in three lines, broken after "24 of 40:" (a width wrap would end line 1 on "no")
        head, rest = S15_DOTS.split(": ")
        draw_text(img, (580, 196), head + ":", 40, 800, INK)
        for i, ln in enumerate(("no step-free route", "either way")):
            assert ln in rest and text_size(ln, 28, 700)[0] <= 880 - 580, ln  # inside the panel (x 40-900)
            draw_text(img, (580, 260 + i * 38), ln, 28, 700, INK)


def s15(dur: float):
    """C2c (13 Oct capture): the St. Dominic's card is still until 4.2 s (TEST IN SKETCHFUTURE clicked
    within it), a blank page at 4.23 s, SketchFuture loaded and compared by 5.1 s, then still. Beats keyed to
    the guide voice (from 0.2 s): 'walkers lose seventeen seconds' 6.2 s, 'And 24 of our 40' 10.1 s.
    The picture is letterboxed to 1760x990 on navy, so the footer and the docked evidence legend (S10-S16)
    sit on the navy strip below it, and SketchFuture's own map legend and OpenStreetMap credit, at the
    picture's bottom edge, stay uncovered. On screen (19 Oct declutter): the badge, the counters (header,
    three rows, a six-word hedge) only during their sentence, then the dot grid with one eight-word label; the
    map credit only while SketchFuture's map is on screen; no run number or file path."""
    c2c = CLIPS / "C2c.mp4"
    spec("S15", "MODEL CHECK · synthetic cohort", f"Counter header: {S15_HEADER} |",
         "walkers +17 s · wheelchair users +30 s · stroller users +21 s", f"Small, under the counters: {S15_HEDGE} |",
         f"{S15_DOTS} |", "Footer: Map © OpenStreetMap contributors")
    assert len(S15_HEDGE.split()) <= 6 and len(S15_DOTS.split()) <= 8
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
        # from the cut to SketchFuture's OpenStreetMap map (2.4 s) to the end
        (png("S15_footer", lambda img: solid_footer(img, "Map © OpenStreetMap contributors")), 2.4, dur),
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
