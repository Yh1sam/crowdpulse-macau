# CrowdPulse current production guide — 20 October 2026

Current cut: **18 scenes, 4:31 (271 seconds)**. CrowdPulse is the sole product. Scenario simulation is one feature. The wheelchair-user story is an anonymous illustration. Roles match the latest allocation: Sam develops the app/integration/privacy; Thomas covers counting tests, forecasting and evaluation; Ean covers users/workflows/video editing; Curtis covers health/accessibility and route limitations.

21 October allocation update: N06 (product positioning and workflow) is now Sam's narration. Individual scene windows total Sam 57 seconds, Thomas 81 seconds, Ean 56 seconds and Curtis 53 seconds, excluding the three shared lines. Narration text and scene timing are unchanged.

## Outputs and editing

- Reference preview: `video/build/v3/cut/crowdpulse_v3_full_preview_720p.mp4`
- Reference master: `video/build/v3/cut/crowdpulse_v3_full_1080p.mp4`
- **Silent picture master, without burned narration captions:** `video/build/v3/cut/crowdpulse_v3_picture_only_1080p.mp4`
- Editable reference subtitles: `video/build/v3/cut/crowdpulse_v3_guide_captions.srt`
- Recording pack: `video/build/v3/CrowdPulse_錄音包_v3_2026-10-21.zip`
- Ean editing pack: `video/build/v3/CrowdPulse_Ean剪輯包_v3_2026-10-21.zip`

The reference voice remains macOS Daniel, not a member's voice. The lower-right Guide audio label was removed as requested. No real member audio or camera footage has been inserted. Three shared-camera scenes remain as labelled stand-ins: N01 introduction, N04 full question, N17 closing. The 21 October recording instructions allow all four members to record separately in different locations: landscape 1080p/30 fps, eye-level chest-up framing, simple background, original camera audio and 2–3 takes per shared scene. Ean combines them in a four-panel layout, aligns sentence starts and pauses, and uses a clear lead voice with quieter supporting tracks. Individual camera footage for the other scenes is optional. If the team uses only two shared camera segments, Ean can use a CrowdPulse text card plus group voice for N17.

The updated packages include three reference audio clips for N01/N04/N17 under `reference/`. Use [the exact current lines](voice-lines.md), [scene directions](script.md) and [per-person files](../../../video/team-kit/v2-audio-first/). The picture master retains product UI, speaker/role labels, source/simulation notices and camera stand-ins, with no audio stream or burned dialogue captions. Ean should adjust picture holds and SRT timings to the real voices, then replace camera stand-ins with synchronized footage. It is not yet a final submission film.

N15 says the fixed fact that the Melbourne test was pre-registered; pending status stays in the graphic. The test window ends **22 October at 21:00 Hong Kong/Macau time**, after which archive coverage and results still need checking. Record now; a verified result can later be added as a graphic or short additional voice segment. No result is presumed.

## Current product demonstration

N09 uses the actual updated API/UI with explicit seeded synthetic prediction inputs, then scripted field-check request and rejection. Approval is blocked; a request does not verify the route. Both events are shown from the real audit log. A separate draft-notice insert is labelled not published. See [route review policy and tests](../../route-review.md).

N13 presents **CrowdPulse · Scenario simulation**, using the actual branded interface. Its paired cohort still has 24/40 unreachable journeys in each plan. The result is not 24 newly excluded journeys, an actual detour verification or field certification. N12 highlights about one minute of simulated late warning and retains the sampling caveat.

## Reproduction

```sh
.venv/bin/python video/v2_story.py
.venv/bin/python video/pitch_v2.py --guides --stills
.venv/bin/python video/pitch_v2.py --render --workers 3
.venv/bin/python video/pitch_v2.py --assemble
.venv/bin/python video/make_recording_pack.py
```

The renderer decodes source clips without altering them, renders each frame once for both captioned and clean outputs, then assembles separate masters. Guide utterances are cached by text/voice/rate; changing narration requires regenerating timing and affected scenes. Old 4:15 and 4:37 exports remain under `video/build/v2/`. The older unversioned scripts reproduce earlier cuts and do not define the current recording lines.

New source capture recipes are `video/shots/C3_review.json`, `C3_notice.json` and `C3_scenario.json`. `video/seed_review_demo.py` resets only its isolated recording database under `video/build/v3/`; it never reads Melbourne held-out counts. See [current media verification](review-2026-10-20.md).
