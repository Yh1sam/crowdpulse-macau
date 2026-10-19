# CrowdPulse V2 production guide

The current reconstruction follows the approved 18-scene story and revised four-person allocation. Runtime is **4:37 (277 seconds)**, including six seconds of credits. This is a complete review cut with stock guide narration and labelled camera placeholders, ready for reviewing the sequence and recording the real team takes.

## Local outputs

- Full preview: `video/build/v2/cut/crowdpulse_v2_full_preview_720p.mp4`
- 1080p master: `video/build/v2/cut/crowdpulse_v2_full_1080p.mp4`
- Final-cut review sheets: `video/build/v2/qa/full-cut-review-1.jpg` and `full-cut-review-2.jpg`
- Per-sentence guide timing: `video/build/v2/guide.json`

Derived media is ignored by Git and stays local. The older `docs/video/shotlist.json`, scripts and renderer remain intact for reproducing the previous cut; they are not the V2 narrative source.

## Story and recording

[Script and screen direction](script.md), [exact lines and time windows](voice-lines.md), [machine-readable shot list](shotlist.json).

| Member | Focus | Scenes |
|---|---|---|
| Yeung Hou Sam | Science & Technology: phone, local processing, counting tests | N05, N07, N10, N11 |
| Wong U Hei | Science & Engineering: forecasts, integration and evaluation | N08, N12, N14 |
| Ieong I Hang | Business & Deployment: intended use and operating workflow | N03, N06, N09, N15 |
| Ku Seong Lai | Health & Accessibility: Mrs Chan and route limitations | N02, N13, N16 |
| All four | Shared introduction, full research question and closing | N01, N04, N17 |

The guide is the macOS **Daniel** stock voice, not an imitation of any member. The displayed member names assign the planned narration; they do not identify the guide voice. N01/N04/N17 are neutral camera stand-ins. Record the shared question in full with all four members. Record individual scenes with the exact words and natural pauses; allow timing changes if real takes need more room. School and supervisor details remain pending. No real member recordings have been inserted.

## Rebuild

From the repository root, with the existing Python environment, FFmpeg, macOS `say`, bundled fonts, source clips and experiment figures:

```sh
.venv/bin/python video/v2_story.py
.venv/bin/python video/pitch_v2.py --guides --stills
.venv/bin/python video/pitch_v2.py --render --workers 3
.venv/bin/python video/pitch_v2.py --assemble
```

To rebuild a changed scene, use `--render --only N09 --workers 1`, then assemble again. Guide generation caches sentence audio by text, voice, rate and tempo. Changing narration requires regenerating guides and re-rendering affected scenes because captions are burned in. Replacing audio alone would leave guide captions and visual cues out of sync; real voice/camera integration needs a new timing pass.

The renderer preserves screen aspect ratios, uses bounded sequential video decoding and holds the final frame of a short recording rather than inventing later readings. The phone source is the existing 7.13-second masked excerpt; its final readout is deliberately held and labelled. All original recordings are read-only inputs.

## Product presentation and evidence

N06 introduces the full phone/dashboard/staff composition, then moves the phone into the N07 opening position. N07 moves from the full device to a magnified crop of its actual numerical readout. N08 labels the Almeida Ribeiro test feed before switching to the separate, simulated Senado recording. N09 shows suggestion, recorded approval and audit, followed by a separately labelled notice insert. It does not present an earlier notice capture as a later live event.

| Evidence | Treatment in this cut |
|---|---|
| Simulator counting | Toronto public-domain test clip, pixelated faces; no Macau field-count claim |
| Macau dashboard | Working software with simulated crowd/forecast; source labels stay visible |
| Operator approval | Scripted click; fictional self-declared `demo-operator-1`, no authenticated identity claim |
| Privacy | Recorded server responses 202 / 422 / 403, timed to the spoken clauses |
| Counting calibration | One Mall camera, 20 labelled calibration frames, held-out MAE 3.3 vs 4.8 fixed-count baseline; offline and not yet in the app; derived figures only |
| Forecast quality | Held-out simulated days, +15-minute macro-F1 .865 vs .795; accuracy/recall secondary; always-SAFE accuracy 84.6% visible |
| Late warning | Run A's 14:08:09 threshold crossing and 14:09:08 first confident warning; threshold .70 is not a validated safety limit |
| Accessibility | Full-closure stress test, synthetic 40-journey wheelchair cohort; 24 unreachable both before and after; purple dots mean no mapped step-free route, not newly excluded journeys |
| Melbourne | Pre-registered test pending; no held-out results opened or calculated for this edit |

## Verification — 19 October 2026

- Both exports: **277.000 seconds, 8,310 video frames, 30 fps**. Master 1920×1080; preview 1280×720. H.264, limited-range BT.709; AAC stereo at 48 kHz. Fast-start metadata for playback.
- Both full files passed FFmpeg error-fatal decoding of all video and audio, with no decoder errors. Colour metadata was then explicitly tagged BT.709 without re-encoding picture or audio.
- Guide audio fits all 17 spoken slots. Every caption lies within its scene window and the 1,480-pixel caption-safe width. Credits occupy the final six seconds.
- Measured finished audio: **−18.08 LUFS integrated**, **−4.88 dBTP** peak, 5.0 LU loudness range; no clipping indicated.
- Inspected source-render stills for all scenes, then 24 samples extracted from the assembled 720p export covering all 18 scenes, the phone composition transition, enlarged readout, approval audit, notice insert and server rejection. This is sampled visual QA plus complete technical decoding, not a claim of a separate human viewing/listening session.
- Rechecked caption timing against sentence audio, actual metric files, the before/after cohort semantics, readable crop scaling and preservation of recording aspect ratios. The product captures and guide audio are complete; real team camera/voice and pending submission details remain to be supplied.

The cut has not been submitted or published. Cost approval and other competition submission checks remain separate from producing this preview.
