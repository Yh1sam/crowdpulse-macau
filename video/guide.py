"""Make the robot guide track for the pitch video: one audio file per shot, for timing only.

The team records the real narration in their own voices (docs/video/script.md, section 5C); this
track only lets the first cut be timed and checked. Each shot's narration from
docs/video/shotlist.json is spoken by macOS `say -v Daniel -r 155` (about 147 words per minute,
measured in the script), after turning numbers into words the way the script's pronunciation guide
says them and dropping bracketed placeholders and speaker tags. S05 is slowed without changing
pitch so the longer member introductions have time to breathe.

    .venv/bin/python video/guide.py        # writes video/build/guide/SNN.wav and guide.json
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "video" / "build" / "guide"
VOICE, RATE = "Daniel", "155"
TEMPO_BY_SHOT = {"S05": 0.9}
SPOKEN = [  # written -> spoken (script section 5C)
    (r"\bSt\. ", "Saint "), (r"\bF1\b", "F one"), (r"0\.865", "point eight six five"), (r"0\.795", "point seven nine five"),
    (r"\b2019\b", "twenty nineteen"), (r"\b124\b", "a hundred and twenty-four"), (r"\bface-ID\b", "face I D"), (r"\bYOLO\b", "Yo-lo"),
    (r"\bSenado\b", "Se-nah-doo"),
]


def spoken_text(narration: str) -> str:
    text = re.sub(r"\[(?:M\d|ALL)\]\s*", "", narration)          # speaker tags
    text = re.sub(r"\[[^\]]*\]", "", text)                         # placeholders (slots stay silent)
    for pattern, repl in SPOKEN:
        text = re.sub(pattern, repl, text)
    return re.sub(r"\s+", " ", text).strip()


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shots = json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text())
    report = []
    for s in shots:
        text = spoken_text(s.get("narration") or "")
        slot = s["end_s"] - s["start_s"]
        entry = {"id": s["id"], "slot_s": round(slot, 2), "text": text, "speech_s": 0.0}
        if text:
            aiff, wav = OUT / f"{s['id']}.aiff", OUT / f"{s['id']}.wav"
            subprocess.run(["say", "-v", VOICE, "-r", RATE, "-o", str(aiff), text], check=True)
            tempo = TEMPO_BY_SHOT.get(s["id"], 1.0)
            audio_filter = ["-af", f"atempo={tempo}"] if tempo != 1.0 else []
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(aiff), *audio_filter,
                            "-ar", "48000", "-ac", "1", str(wav)], check=True)
            aiff.unlink()
            entry["speech_s"] = round(duration(wav), 2)
        entry["fill"] = round(entry["speech_s"] / slot, 2) if slot else 0
        report.append(entry)
        print(f"{s['id']}: {entry['speech_s']:5.2f} s of speech in a {slot:5.1f} s slot ({entry['fill']:.0%})")
    (OUT / "guide.json").write_text(json.dumps(report, indent=1) + "\n")
    total = sum(e["speech_s"] for e in report)
    print(f"total speech {total:.1f} s over {shots[-1]['end_s']:.1f} s of video")


if __name__ == "__main__":
    main()
