"""Assemble the pitch video: shots -> overlays (captions, lower-thirds, badges, callouts) -> one file.

Each shot in docs/video/shotlist.json is built as a clip of exactly its slot length from its
sources (motion graphics in video/build/mg, recordings in video/build/clips), with transparent
overlays composited by ffmpeg at their times. The clips are joined and the narration track is laid
under them: the robot guide track (video/build/guide, timing only) until the team's own takes exist
in video/build/voice/SNN.wav, which are used instead, shot by shot, as soon as they are there.

    .venv/bin/python video/assemble.py                 # -> video/build/cut/pitch_cut.mp4
    .venv/bin/python video/assemble.py --only S08 S10  # rebuild some shots, then re-join

--only also rebuilds any clip written with other colour tags than CLIP_TAGS, so the joined stream
never mixes them. Captions are made from each shot's narration, split into chunks of a few words,
spread over that shot's speech in proportion to their length and moved onto the voice's pauses
(caption_bounds); with the team's takes, check them against the real word timestamps.
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
COLOUR = ["-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
CLIP_TAGS = "yuv420p,tv,bt709,bt709,bt709"  # what colour_tags() reads back from a clip written with COLOUR
VOICE_START = {"S10": 0.8, "S17b": 0.5}  # narration offset into the shot (s); others 0.2
SPEAKER = {  # each member's first voice-over shot in playback order gets a lower-third for 3 s (the team has four members)
    "S01": ("[MEMBER 4]", "M", "Medicine"),
    "S08": ("[MEMBER 3]", "EB", "Engineering and business"),
    "S07": ("[MEMBER 2]", "S", "Science"),
    "S02": ("[MEMBER 1]", "T", "Technology"),
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def colour_tags(path: Path) -> str:
    """'pix_fmt,range,matrix,transfer,primaries' of a file's video stream (CLIP_TAGS for an assembled clip)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=pix_fmt,color_range,color_space,color_transfer,color_primaries", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


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
    for c in chunks:  # a run of one-word sentences shares one caption
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


MARKS, STOPS = (",", ";", ":", ".", "?", "!"), (".", "?", "!", ";", ":")  # a voice pauses after a mark; a stop ends a clause


def pause_mark(word: str) -> bool:
    """Whether a voice pauses after this word: it ends in a punctuation mark ("St." does not count)."""
    return word.endswith(MARKS) and word != "St."


def caption_bounds(chunks: list[str], speech: float, gaps: list[tuple[float, float]]) -> list[float]:
    """Caption switch times, in seconds into the voice file: chunk i is up from bounds[i] to bounds[i + 1].

    Chunks share the speech in proportion to their length. A boundary after a punctuation mark then
    moves to the end of that mark's pause, which is when the next chunk's first word starts:
    - when the take has exactly one pause per mark (the guide voice does), the k-th pause is the
      k-th mark's, so each boundary takes its own pause;
    - otherwise (a real take, with breaths and unpaused commas), after a stop (. ? ! ; :) the
      longest pause within 1 s of the proportional boundary wins (people pause longer at a sentence
      end than at a comma), the nearer one when two are within 10% of each other; after a comma,
      the nearest pause within 0.5 s. The guide voice's pauses are all about 0.2-0.3 s long, so for
      it length cannot tell a stop's pause from a comma's; that is why its pauses are matched by count.
    Silence before the first word and after the last is not a pause."""
    gaps = [g for g in gaps if g[0] > 0.01 and g[1] < speech - 0.01]
    total = sum(len(c) for c in chunks)
    bounds, acc = [0.0], 0.0
    for c in chunks:
        acc += speech * len(c) / total
        bounds.append(acc)
    upto, n = [], 0  # marks up to the end of each chunk
    for c in chunks:
        n += sum(map(pause_mark, c.split()))
        upto.append(n)
    ordinal = len(gaps) == upto[-1] - pause_mark(chunks[-1].split()[-1])
    mid = lambda g: (g[0] + g[1]) / 2  # noqa: E731
    for i in range(1, len(chunks)):
        if not pause_mark(chunks[i - 1].split()[-1]):
            continue  # a break between words: no pause to snap to
        if ordinal and abs(mid(gaps[upto[i - 1] - 1]) - bounds[i]) <= 1.5:
            bounds[i] = gaps[upto[i - 1] - 1][1]
            continue
        stop = chunks[i - 1].endswith(STOPS)
        near = [g for g in gaps if abs(mid(g) - bounds[i]) <= (1.0 if stop else 0.5) and bounds[i - 1] < g[1] < bounds[i + 1]]
        if not near:
            continue
        if stop:
            longest = max(g[1] - g[0] for g in near)
            near = [g for g in near if g[1] - g[0] >= 0.9 * longest]
        bounds[i] = min(near, key=lambda g: abs(mid(g) - bounds[i]))[1]
    return bounds


def caption_overlays(shot: dict) -> list[tuple[Path, float, float]]:
    """[(png, start, end)] for the shot's burned-in captions, timed over its speech by caption_bounds,
    so each caption appears when its first word is spoken, not a few tenths of a second off."""
    chunks = caption_chunks(shot.get("narration", ""))
    v = voice_file(shot["id"])
    if not chunks or not v:
        return []
    start = VOICE_START.get(shot["id"], 0.2)
    slot = shot["end_s"] - shot["start_s"]
    bounds = caption_bounds(chunks, probe_duration(v), pauses(v))
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
    """base: ffmpeg input args producing one video stream; overlays: PNGs shown from a up to (not at) b,
    so a caption ending on the frame where the next one starts does not share that frame with it;
    movs: alpha .mov overlays starting at an offset. Writes exactly `duration` s at 1080p30.

    The sources differ in colour range and tags (screen captures are full-range BT.601 from JPEG
    frames, the phone recording limited-range BT.709, the motion graphics untagged), so each one is
    read into RGB by its own tags, the overlays are blended in RGB, and every clip is written the
    same way: limited ("tv") range yuv420p tagged BT.709 (COLOUR). The clips then join with -c copy
    into one stream with one set of tags, which players that read colour once per file need."""
    args = ["ffmpeg", "-loglevel", "error", "-y", *base]
    filters, last = [], "[0:v]"
    head = (f"{last}{pre_filter + ',' if pre_filter else ''}fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=decrease:in_range=auto:in_color_matrix=auto,format=gbrp,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0B1220,setsar=1,"
            f"tpad=stop_mode=clone:stop_duration={duration},trim=0:{duration},setpts=PTS-STARTPTS[b]")
    filters.append(head)
    last, idx = "[b]", 1
    for mov, offset in movs:
        args += ["-itsoffset", f"{offset}", "-i", str(mov)]
        filters.append(f"{last}[{idx}:v]overlay=0:0:eof_action=pass:format=gbrp[m{idx}]")
        last, idx = f"[m{idx}]", idx + 1
    for p, a, b in overlays:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{duration}", "-i", str(p)]
        filters.append(f"{last}[{idx}:v]overlay=0:0:format=gbrp:enable='gte(t,{a:.3f})*lt(t,{b:.3f})'[o{idx}]")  # [a, b)
        last, idx = f"[o{idx}]", idx + 1
    filters.append(f"{last}scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,"  # the frames' own tags win over -color_*,
                   "setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709[v]")  # so set them on the frames
    args += ["-filter_complex", ";".join(filters), "-map", "[v]", "-t", f"{duration}", "-r", str(FPS),
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", *COLOUR, "-an", str(out)]
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
        need = not args.only or s["id"] in args.only or not clip.exists()
        stale = False
        if not need:  # a kept clip written before the clips shared one set of colour tags, or left unreadable by a killed encode
            try:
                stale = colour_tags(clip) != CLIP_TAGS
            except subprocess.CalledProcessError:
                stale = True
        if need or stale:
            base, overlays, movs, pre = recipes.recipe(s, dur)
            overlays = overlays + caption_overlays(s) + lower_third_overlay(s)
            composite(base, overlays, movs, dur, clip, pre)
            print(f"{s['id']}: {dur:.2f} s -> {clip.name}{' (rebuilt: other colour tags)' if stale and args.only and s['id'] not in args.only else ''}",
                  flush=True)
        clips.append(clip)
    total = shots[-1]["end_s"]
    listing = CUT / "clips.txt"
    listing.write_text("".join(f"file '{c}'\n" for c in clips))
    silent, audio, final = CUT / "video_only.mp4", CUT / "narration.m4a", CUT / "pitch_cut.mp4"
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(silent)])
    mix_audio(shots, total, audio)
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(silent), "-i", str(audio), "-c:v", "copy", "-c:a", "copy", "-shortest", str(final)])
    print(f"{final}: {probe_duration(final):.2f} s, colour {colour_tags(final)}")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "video"))
    main()
