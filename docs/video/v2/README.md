# CrowdPulse V2 production guide

The current reconstruction follows the approved 18-scene story and revised four-person allocation. After the full-sequence pacing review, runtime is **4:15 (255 seconds)**, including six seconds of credits. This is a complete review cut with stock guide narration and labelled camera placeholders, ready for reviewing the sequence and recording the real team takes.

## Local outputs

- Full preview: `video/build/v2/cut/crowdpulse_v2_reviewed_full_preview_720p.mp4`
- 1080p master: `video/build/v2/cut/crowdpulse_v2_reviewed_full_1080p.mp4`
- Sequential review frames and motion sheets: `video/build/v2/qa/full-pass-reviewed/` and `video/build/v2/qa/motion-reviewed/`
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

N06 introduces the full phone/dashboard/staff composition, then moves the phone into the N07 opening position. N07 moves from the full device to a magnified crop of its actual numerical readout. N08 carries the phone/readout composition across the cut, labels the Almeida Ribeiro test feed, then switches to the simulated Senado recording. Forecast and explanation details are clearly labelled inserts from separate recorded moments. N09 shows suggestion, recorded approval and audit, followed by a separately labelled notice insert. It does not present an earlier notice capture as a later live event.

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

## Review and verification

See [the full-sequence review and fixes](review.md) for the concrete defects, revised timing and verification evidence. The earlier 4:37 files remain in the local cut folder for comparison. The reviewed files use a distinct name to avoid confusing them with that version.

The cut has not been submitted or published. The review still uses stock guide narration and camera placeholders; real team camera/voice recordings and pending submission details remain separate.
