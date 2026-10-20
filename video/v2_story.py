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
    "yeung": {"name": "Yeung Hou Sam", "letters": "ST", "role": "Development & Privacy", "alias": "Sam", "focus_zh": "手機計數、系統整合開發、資料私隱"},
    "wong": {"name": "Wong U Hei", "letters": "SE", "role": "Testing & Forecasting", "alias": "Thomas", "focus_zh": "計數測試、人潮預測、評估、失敗案例"},
    "ieong": {"name": "Ieong I Hang", "letters": "B", "role": "User needs & Video", "alias": "Ean", "focus_zh": "使用者需要、工作人員操作流程、影片剪輯"},
    "ku": {"name": "Ku Seong Lai", "letters": "M", "role": "Health & Accessibility", "alias": "Curtis", "focus_zh": "健康與無障礙、輪椅使用者情境、路線模型限制"},
}

ROWS = [
    (4, 'all', 'Team', 'We are CrowdPulse Macau.',
     'Four neutral camera stand-ins with the confirmed names and roles; wordmark settles with the spoken name. Clearly marked as camera placeholders.'),
    (20, 'ku', "A wheelchair user's view", "My focus is health and accessibility. Imagine a wheelchair user visiting the Ruins of Saint Paul's. From inside the crowd, they cannot see what is building ahead. Staff decisions about redirecting people can also affect which routes they can use.",
     "Anonymous wheelchair-user illustration on the Macau schematic, followed by eye-level silhouettes. Replace the named character tag with Wheelchair user. ILLUSTRATION remains visible; this is not a real person's story."),
    (17, 'ieong', 'Why these decisions matter', 'We want to help event staff make informed decisions. Why do these decisions matter? They affect people with different mobility needs. This Golden Week, police briefly controlled crowds at the Ruins on three afternoons.',
     'Move from visitor to event staff. Give the spoken question a large focused beat. Show 2/3/4 October 2026 date chips with the police-release citation; do not imply an observed Macau crush injury.'),
    (9, 'all', 'Our question', 'Can ordinary phones support crowd forecasts and staff decisions without sending images or identifying passers-by?',
     'All four camera stand-ins remain visible while the full shared question is spoken. Large readable question; no title animation before the last words.'),
    (4, 'yeung', 'CrowdPulse', 'CrowdPulse follows the changing rhythm of crowds.',
     'The street graph and crowd rhythm form the wordmark. Pulse refers to crowd changes, not a biometric measurement.'),
    (20, 'yeung', 'A proposed supporting tool', "Macau's Public Security Police Force already runs a crowd warning system. CrowdPulse explores a portable workflow for event staff: phones send numbers, forecasts show uncertainty, and suggestions stay under review when evidence is missing.",
     'Credit the existing police system first. Reveal a phone, dashboard and staff role as a coherent product composition. Proposed support; no partner yet. Preserve public-source wording without superiority claims.'),
    (14, 'yeung', 'Count on the device', 'My focus is the phone app, system integration and privacy. Here it counts people from a Toronto test clip in the iPhone Simulator, and sends numerical readings to our server.',
     "Product-style phone reveal, then a magnified crop of the same actual frame's readings. Use only the masked Simulator capture. Smooth movement from full device to numerical readings; no fabricated values. Working prototype / Toronto test clip."),
    (21, 'wong', 'Inspect the forecast', "My focus is counting tests, crowd forecasting and evaluation. The phone's test feed is assigned to Almeida Ribeiro. Here, we switch to the simulated Senado scenario. Staff can inspect forecasts, confidence scores and reasons.",
     'Explicit test-feed/Almeida provenance beat before switching to the simulated Senado recording. Carry the phone/readout composition across the cut. Show the live-map recording, then clearly labelled forecast and explanation details captured at separate moments. Keep the simulated-data label visible; do not imply an uninterrupted clock.'),
    (26, 'ieong', 'Review before acting', 'My focus is user needs, staff workflows and video editing. Here, route accessibility is unverified, so CrowdPulse blocks approval. The operator requests an on-site check, then rejects the diversion. Both actions are recorded under a self-declared name. Draft public notices disclose AI use in three languages.',
     'Real updated dashboard with a seeded synthetic recommendation, explicitly labelled verification test. Show the blocked APPROVE control, request a field check, reject the diversion and show both audit events. The request is not a completed inspection. Separate labelled draft-notice insert; no public notice is issued. The demo name is fictional and self-declared.'),
    (19, 'yeung', 'Privacy by design', 'First, privacy. Staff need crowd patterns, so we chose to process video locally and send numerical observations. Our server accepts a valid reading, rejects one containing an identity field, and refuses image uploads.',
     'Local processing diagram gives way to the real recorded terminal. Show recorded 202 / 422 / 403 responses at the relevant narration. Do not manufacture shell responses or claim regulatory approval.'),
    (18, 'wong', 'Test the counts', 'On one mall camera, the detector under-counted. After calibrating with twenty labelled frames, held-out error was about three people per frame, versus about five for a fixed guess. This calibration is not yet in the app.',
     'Derived scatter/chart only; no Mall imagery. Compare held-out MAE 3.3 with fixed-count baseline 4.8, static numerals, same scale. One camera / 20 labelled frames / offline calibration / not in app.'),
    (27, 'wong', 'Test the warning time', "Counting accuracy doesn't guarantee warning time. On held-out simulated days, our fifteen-minute model beat the no-change baseline. But in a fast simulated surge, the first confident warning came about a minute after the alert threshold was crossed. Staff review remains essential. Our adjusted confidence score is a review cue, not a calibrated probability.",
     'Keep the simulated +15-minute scores. Highlight About 1 minute late in the Run A sampled timeline, then show the review UI. Timestamps differ by 59 simulated seconds; sampling is about 30 simulated seconds, so do not imply precise field latency. Prototype threshold is not a safety limit.'),
    (25, 'ku', 'Compare a street-change scenario', 'CrowdPulse also includes scenario simulation, to compare street changes for different mobility needs. In one full-closure stress test, twenty-four of forty simulated wheelchair journeys had no mapped step-free route in either plan. The closure did not create those twenty-four unreachable journeys. Map data and on-site checks still matter.',
     "Present this as CrowdPulse's Scenario simulation feature, with no separate product logo or pitch. Show the actual branded module before the paired 40-dot cohorts. Both have24 unreachable. Explicitly label the unchanged baseline: no newly unreachable journeys in this cohort. Model results do not verify a real alternative route."),
    (15, 'wong', 'What the tests taught us', 'Our tests showed why prediction quality, warning time and route accessibility need separate checks. In CrowdPulse, missing route evidence now blocks approval and leads to a recorded request for an on-site check.',
     'Three familiar elements return: prediction comparison, late-warning timeline, wheelchair route. No second full demo or extra metrics.'),
    (13, 'ieong', 'The next evidence', 'We pre-registered our forecasting test on Melbourne pedestrian counts. We then want a supervised pilot, with permission. Our next milestone is evidence from real operating conditions.',
     'Short roadmap: Melbourne test pending / supervised pilot proposed. No held-out analysis or invented result; no claimed partner or field deployment.'),
    (8, 'ku', 'Return to the wheelchair user', 'For a wheelchair user, staff would still need to inspect the route and provide assistance on site.',
     'Return to the anonymous wheelchair-user illustration, with staff checking the route. No named character, real-person claim or all-clear stamp.'),
    (5, 'all', 'People decide', 'The AI recommends. A person decides.',
     'All four stand-ins share the final line, with names and roles. Clear camera-placeholder label until real footage is supplied.'),
    (6, 'none', 'Credits', '',
     'CrowdPulse wordmark, confirmed names and roles, code/evidence link and material credits. Production notes keep pending school/supervisor details; remove the pending label from the film credits. Guide/camera-placeholder labels stay while the media is still a guide version.'),
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
        f"| {p['name']} ({p['alias']}) | {p['letters']} | {p['focus_zh']} |\n" for p in PEOPLE.values())
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
