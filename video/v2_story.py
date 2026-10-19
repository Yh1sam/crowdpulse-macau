"""Approved 18-scene reconstruction. Exported to versioned production documents.

The older shotlist stays available for reproducing the previous cut and its sourced graphics.
This module defines the new narrative, speakers and evidence boundaries in one place.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "video" / "v2"
PEOPLE = {
    "yeung": {"name": "Yeung Hou Sam", "letters": "ST", "role": "Science & Technology"},
    "wong": {"name": "Wong U Hei", "letters": "SE", "role": "Science & Engineering"},
    "ieong": {"name": "Ieong I Hang", "letters": "B", "role": "Business & Deployment"},
    "ku": {"name": "Ku Seong Lai", "letters": "M", "role": "Health & Accessibility"},
}

ROWS = [
    (4, "all", "Team", "We are CrowdPulse Macau.",
     "Four neutral camera stand-ins with the confirmed names and roles; wordmark settles with the spoken name. Clearly marked as camera placeholders."),
    (21, "ku", "A visitor's view", "My focus is health and accessibility. Imagine Mrs Chan, a fictional wheelchair user visiting the Ruins of Saint Paul's. From inside the crowd, she cannot see what is building ahead. Staff decisions about redirecting people can also affect which routes she can use.",
     "Reuse the sourced Macau schematic, wheelchair-eye-height view and Mrs Chan choreography. ILLUSTRATION stays visible. Introduce the speaker, then let the map and eye-level view carry the story."),
    (17, "ieong", "Why these decisions matter", "We want to help event staff make informed decisions. Why do these decisions matter? They affect people with different mobility needs. This Golden Week, police briefly controlled crowds at the Ruins on three afternoons.",
     "Move from visitor to event staff. Give the spoken question a large focused beat. Show 2/3/4 October 2026 date chips with the police-release citation; do not imply an observed Macau crush injury."),
    (9, "all", "Our question", "Can ordinary phones support crowd forecasts and staff decisions without sending images or identifying passers-by?",
     "All four camera stand-ins remain visible while the full shared question is spoken. Large readable question; no title animation before the last words."),
    (4, "yeung", "CrowdPulse", "CrowdPulse follows the changing rhythm of crowds.",
     "The street graph and crowd rhythm form the wordmark. Pulse refers to crowd changes, not a biometric measurement."),
    (18, "ieong", "A proposed supporting tool", "Macau's Public Security Police Force already runs a crowd warning system. Our proposal is a temporary sensing kit and dashboard for event staff, designed to support existing work during busy events.",
     "Credit the existing police system first. Reveal a phone, dashboard and staff role as a coherent product composition. Proposed support; no partner yet. Preserve public-source wording without superiority claims."),
    (14, "yeung", "Count on the device", "My focus is the phone app and counting tests. Here it counts people from a Toronto test clip in the iPhone Simulator, and sends numerical readings to our server.",
     "Product-style phone reveal, then a magnified crop of the same actual frame's readings. Use only the masked Simulator capture. Smooth movement from full device to numerical readings; no fabricated values. Working prototype / Toronto test clip."),
    (21, "wong", "Inspect the forecast", "My focus is forecasting, system integration and evaluation. The phone's test feed is assigned to Almeida Ribeiro. Here, we switch to the simulated Senado scenario. Staff can inspect forecasts, confidence scores and reasons.",
     "Explicit test-feed/Almeida provenance beat before switching to the simulated Senado recording. Carry the phone/readout composition across the cut. Show the live-map recording, then clearly labelled forecast and explanation details captured at separate moments. Keep the simulated-data label visible; do not imply an uninterrupted clock."),
    (18, "ieong", "Review before acting", "My focus is deployment and how event staff would use the system. An operator reviews each suggestion, approves or rejects it, and enters a name recorded with the decision. Notices come in three languages and disclose AI use.",
     "Recorded operator workflow: suggestion, notices, approval and audit record. Large clean screen frame with measured camera moves. Retain Scripted click and fictional demo-operator disclosure; the name is self-declared, not authenticated."),
    (19, "yeung", "Privacy by design", "First, privacy. Staff need crowd patterns, so we chose to process video locally and send numerical observations. Our server accepts a valid reading, rejects one containing an identity field, and refuses image uploads.",
     "Local processing diagram gives way to the real recorded terminal. Show recorded 202 / 422 / 403 responses at the relevant narration. Do not manufacture shell responses or claim regulatory approval."),
    (18, "yeung", "Test the counts", "On one mall camera, the detector under-counted. After calibrating with twenty labelled frames, held-out error was about three people per frame, versus about five for a fixed guess. This calibration is not yet in the app.",
     "Derived scatter/chart only; no Mall imagery. Compare held-out MAE 3.3 with fixed-count baseline 4.8, static numerals, same scale. One camera / 20 labelled frames / offline calibration / not in app."),
    (25, "wong", "Test the warning time", "Counting accuracy doesn't guarantee warning time. On held-out simulated days, our fifteen-minute model beat the no-change baseline. But a fast simulated surge crossed our alert threshold before a confident warning. Staff review remains essential. Our adjusted confidence score is a review cue, not a calibrated probability.",
     "First hold the synthetic +15 minute F1 .865/.795 comparison; accuracy96.4/94.3 and critical recall91/79 are secondary, against simulated observed labels. Always-SAFE accuracy84.6 is context. Then show the recorded late-warning example and actual review UI. Prototype threshold, not a validated safety limit. No causal improvement claim."),
    (23, "ku", "Check who can use the route", "And what about someone like Mrs Chan? In a full-closure stress test on Macau's mapped streets, twenty-four of forty simulated wheelchair journeys had no mapped step-free route, both before and after the change. We need better map data and on-site checks before treating a modelled route as suitable for real visitors.",
     "Show the actual SketchFuture model capture first, then dissolve to two equal before/after 40-dot cohorts. Both already show24 unreachable; do not animate them as newly excluded by the closure. Full closure / synthetic cohort / mapped routes, not field certification. Keep OSM attribution."),
    (12, "wong", "What the tests taught us", "Our tests showed why prediction quality, warning time and route accessibility need separate checks. A working prototype is the start of that process.",
     "Three familiar elements return: prediction comparison, late-warning timeline, wheelchair route. No second full demo or extra metrics."),
    (13, "ieong", "The next evidence", "Our pre-registered Melbourne forecasting test is pending. We then want a supervised pilot, with permission. Our next milestone is evidence from real operating conditions.",
     "Short roadmap: Melbourne test pending / supervised pilot proposed. No held-out analysis or invented result; no claimed partner or field deployment."),
    (8, "ku", "Back to Mrs Chan", "Back to Mrs Chan: staff would still need to inspect the route and assist her on site.",
     "Return to the same underlying schematic, risk still present. Staff inspect and stand beside her. No green approved route or automatic safety certification."),
    (5, "all", "People decide", "The AI recommends. A person decides.",
     "All four stand-ins share the final line, with names and roles. Clear camera-placeholder label until real footage is supplied."),
    (6, "none", "Credits", "",
     "Wordmark, four confirmed names/roles, code/evidence link, material credits and school/supervisor pending notice. Full six-second hold."),
]


RUNTIME_S = sum(row[0] for row in ROWS)


def scenes() -> list[dict]:
    result, start = [], 0
    for index, (duration, speaker, title, narration, visual) in enumerate(ROWS, 1):
        result.append(dict(id=f"N{index:02d}", start_s=start, end_s=start + duration,
                           speaker=speaker, title=title, narration=narration, visual=visual))
        start += duration
    assert start == RUNTIME_S and len(result) == 18
    return result


def timecode(value: float) -> str:
    return f"{int(value // 60)}:{value % 60:04.1f}"


def export() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    shots = scenes()
    (DOCS / "shotlist.json").write_text(json.dumps(shots, ensure_ascii=False, indent=2) + "\n")
    intro = ("# CrowdPulse Macau — 18-scene reconstruction\n\n"
             f"Approved narrative and speakers; reviewed runtime **{RUNTIME_S // 60}:{RUNTIME_S % 60:02d} ({RUNTIME_S} s)**. "
             "The review uses synthetic guide narration and clearly labelled camera placeholders. "
             "Real voices, camera footage and school/supervisor details remain to be supplied.\n\n")
    roles = "| Speaker | STEMB | Focus |\n|---|---|---|\n" + "".join(
        f"| {p['name']} | {p['letters']} | {p['role']} |\n" for p in PEOPLE.values())
    body = []
    table = ["| Scene | Time | Speaker | Exact narration |", "|---|---|---|---|"]
    for s in shots:
        person = PEOPLE[s["speaker"]]["name"] if s["speaker"] in PEOPLE else s["speaker"].upper()
        slot = f"{timecode(s['start_s'])}–{timecode(s['end_s'])}"
        body.append(f"## {s['id']} · {slot} · {person}\n\n**{s['title']}**\n\n"
                    f"{s['narration'] or '(No narration.)'}\n\n**Visual:** {s['visual']}\n")
        table.append(f"| {s['id']} | {slot} | {person} | {s['narration']} |")
    (DOCS / "script.md").write_text(intro + roles + "\n\n" + "\n".join(body))
    (DOCS / "voice-lines.md").write_text(intro + roles + "\n\n" + "\n".join(table) + "\n")


if __name__ == "__main__":
    export()
