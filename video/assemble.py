"""Assemble the pitch video: shots -> overlays (captions, lower-thirds, badges, callouts) -> one file.

Each shot in docs/video/shotlist.json is built as a clip of exactly its slot length from its
sources (motion graphics in video/build/mg, recordings in video/build/clips), with transparent
overlays composited by ffmpeg at their times. The clips are joined and the narration track is laid
under them: the robot guide track (video/build/guide, timing only) until the team's own takes exist
in video/build/voice/SNN.wav, which are used instead, shot by shot, as soon as they are there.

    .venv/bin/python video/assemble.py                 # -> video/build/cut/pitch_cut.mp4
    .venv/bin/python video/assemble.py --only S08 S10  # rebuild some shots, then re-join

Captions are made from each shot's narration, split into chunks of a few words and spread over
that shot's speech in proportion to their length; with the team's takes, re-time them from the
real word timestamps if a chunk drifts.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video" / "mg"))
from style import (W, H, FPS, BUILD, INK, INK_2, NAVY, NAVY_2, WARNING, CYAN, CRITICAL, SAFE, badge, caption, chapter_card,  # noqa: E402
                   draw_text, footer, legend_strip, lower_third, rounded, transparent, text_size)

SHOTLIST = ROOT / "docs" / "video" / "shotlist.json"
CUT = BUILD / "cut"
OV = BUILD / "overlays" / "assembly"
GUIDE, VOICE = BUILD / "guide", BUILD / "voice"
VOICE_START = {"S01": 1.0, "S10": 1.0}  # narration offset into the shot (s); others 0.2
SPEAKER = {  # first VO shot per member gets a lower-third for 3 s
    "S01": ("[MEMBER 4]", "M", "Medicine · health and accessibility"),
    "S02": ("[MEMBER 1]", "T", "Technology · app and detection"),
    "S03": ("[MEMBER 5]", "B", "Business · gap, deployment, cost"),
    "S04": ("[MEMBER 3]", "E", "Engineering · backend and privacy"),
    "S10": ("[MEMBER 2]", "S", "Science · forecasting and statistics"),
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def voice_file(shot: str) -> Path | None:
    for d in (VOICE, GUIDE):
        p = d / f"{shot}.wav"
        if p.exists():
            return p
    return None


WEAK = {"a", "an", "the", "of", "to", "at", "in", "on", "as", "and", "or", "with", "for", "by", "from", "our", "its", "that"}


def caption_chunks(narration: str) -> list[str]:
    """Splits a shot's narration into one-line caption chunks (style.caption: 34 px, 1360 px wide).

    Sentences are kept apart ("St." is not a sentence end). A sentence too wide for one line is
    broken after a comma, semicolon or colon if one sits between 15% and 85% of the way through,
    otherwise between words near the middle, never right after a small word such as "the" or "of"."""
    text = re.sub(r"\[(?:M\d|ALL)\]\s*", "", narration or "")
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    def fits(chunk: str) -> bool:
        return text_size(chunk, 34, 500)[0] <= 1360

    def split(sentence: str) -> list[str]:
        words = sentence.split()
        if fits(sentence) or len(words) < 4:
            return [sentence]
        pos = lambda i: len(" ".join(words[:i]))  # noqa: E731
        n, mid = len(sentence), len(sentence) / 2
        cuts = [i for i in range(1, len(words)) if words[i - 1].endswith((",", ";", ":")) and 0.15 * n <= pos(i) <= 0.85 * n]
        if cuts:
            i = min(cuts, key=lambda k: abs(pos(k) - mid))
        else:
            i = min(range(2, len(words) - 1), key=lambda k: abs(pos(k) - mid) + (1000 if words[k - 1].lower() in WEAK else 0))
        return split(" ".join(words[:i])) + split(" ".join(words[i:]))

    chunks = [c for sent in re.split(r"(?<=[.?!])(?<!St\.)\s+", text) for c in split(sent)]
    merged: list[str] = []
    for c in chunks:  # a run of one-word sentences (the S05 roll call) shares one caption
        if merged and len(c.split()) == 1 and all(len(x.split()) == 1 for x in re.split(r"(?<=\.)\s+", merged[-1])) \
                and fits(f"{merged[-1]} {c}"):
            merged[-1] += " " + c
        else:
            merged.append(c)
    return merged


def png(name: str, draw) -> Path:
    OV.mkdir(parents=True, exist_ok=True)
    img = transparent()
    draw(img)
    path = OV / f"{name}.png"
    img.save(path)
    return path


def pauses(path: Path) -> list[tuple[float, float]]:
    """(start, end) of the pauses in a voice file, from ffmpeg silencedetect."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(starts, ends))


def caption_overlays(shot: dict) -> list[tuple[Path, float, float]]:
    """[(png, start, end)] for the shot's burned-in captions, timed over its speech.

    Chunks share the speech in proportion to their length; a chunk that ends a sentence (or a
    clause ending in ; or :) is then snapped to the nearest pause in the voice file, within 1 s,
    so a sentence's caption appears when it is spoken, not a few tenths of a second early."""
    chunks = caption_chunks(shot.get("narration", ""))
    v = voice_file(shot["id"])
    if not chunks or not v:
        return []
    start = VOICE_START.get(shot["id"], 0.2)
    speech = probe_duration(v)
    slot = shot["end_s"] - shot["start_s"]
    total = sum(len(c) for c in chunks)
    bounds, acc = [0.0], 0.0
    for c in chunks:
        acc += speech * len(c) / total
        bounds.append(acc)
    gaps = pauses(v)
    for i in range(1, len(chunks)):
        if not chunks[i - 1].endswith((".", "?", "!", ";", ":")) or not gaps:
            continue
        near = min(gaps, key=lambda g: abs((g[0] + g[1]) / 2 - bounds[i]))
        if abs((near[0] + near[1]) / 2 - bounds[i]) <= 1.0 and bounds[i - 1] < near[1] < bounds[i + 1]:
            bounds[i] = near[1]
    out = []
    for i, c in enumerate(chunks):
        t, end = start + bounds[i], start + bounds[i + 1] + (0.25 if i == len(chunks) - 1 else 0.0)
        out.append((png(f"{shot['id']}_cap{i:02d}", lambda img, c=c: caption(img, c)), t, min(slot, end)))
    return out


def lower_third_overlay(shot: dict) -> list[tuple[Path, float, float]]:
    if shot["id"] not in SPEAKER:
        return []
    name, letter, role = SPEAKER[shot["id"]]
    start = VOICE_START.get(shot["id"], 0.2)
    return [(png(f"{shot['id']}_lt", lambda img: lower_third(img, name, letter, role)), start, start + 3.0)]


def composite(base: list[str], overlays: list[tuple[Path, float, float]], movs: list[tuple[Path, float]], duration: float, out: Path,
              pre_filter: str = "") -> None:
    """base: ffmpeg input args producing one video stream; overlays: PNGs with enable windows;
    movs: alpha .mov overlays starting at an offset. Writes exactly `duration` s at 1080p30."""
    args = ["ffmpeg", "-loglevel", "error", "-y", *base]
    filters, last = [], "[0:v]"
    head = f"{last}{pre_filter + ',' if pre_filter else ''}fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0B1220,setsar=1,tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration},setpts=PTS-STARTPTS[b]"
    filters.append(head)
    last, idx = "[b]", 1
    for mov, offset in movs:
        args += ["-itsoffset", f"{offset}", "-i", str(mov)]
        filters.append(f"{last}[{idx}:v]overlay=0:0:eof_action=pass[m{idx}]")
        last, idx = f"[m{idx}]", idx + 1
    for p, a, b in overlays:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{duration}", "-i", str(p)]
        filters.append(f"{last}[{idx}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[o{idx}]")
        last, idx = f"[o{idx}]", idx + 1
    args += ["-filter_complex", ";".join(filters), "-map", last, "-t", f"{duration}", "-r", str(FPS),
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-an", str(out)]
    run(args)


def mix_audio(shots: list[dict], total: float, out: Path) -> None:
    args, filters, labels = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=r=48000:cl=mono"], [], ["[0:a]"]
    n = 1
    for s in shots:
        v = voice_file(s["id"])
        if not v:
            continue
        delay = int(round((s["start_s"] + VOICE_START.get(s["id"], 0.2)) * 1000))
        args += ["-i", str(v)]
        filters.append(f"[{n}:a]adelay={delay}:all=1[a{n}]")
        labels.append(f"[a{n}]")
        n += 1
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,atrim=0:{total}[mix]")
    args += ["-filter_complex", ";".join(filters), "-map", "[mix]", "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(out)]
    run(args)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="*", help="rebuild only these shots before joining")
    args = ap.parse_args()
    import recipes  # video/recipes.py: per-shot sources and overlays
    shots = json.loads(SHOTLIST.read_text())
    CUT.mkdir(parents=True, exist_ok=True)
    clips = []
    for s in shots:
        clip = CUT / f"{s['id']}.mp4"
        dur = round(s["end_s"] - s["start_s"], 3)
        if not args.only or s["id"] in args.only or not clip.exists():
            base, overlays, movs, pre = recipes.recipe(s, dur)
            overlays = overlays + caption_overlays(s) + lower_third_overlay(s)
            composite(base, overlays, movs, dur, clip, pre)
            print(f"{s['id']}: {dur:.2f} s -> {clip.name}", flush=True)
        clips.append(clip)
    total = shots[-1]["end_s"]
    listing = CUT / "clips.txt"
    listing.write_text("".join(f"file '{c}'\n" for c in clips))
    silent, audio, final = CUT / "video_only.mp4", CUT / "narration.m4a", CUT / "pitch_cut.mp4"
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(silent)])
    mix_audio(shots, total, audio)
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(silent), "-i", str(audio), "-c:v", "copy", "-c:a", "copy", "-shortest", str(final)])
    print(f"{final}: {probe_duration(final):.2f} s")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "video"))
    main()
