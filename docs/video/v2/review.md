# Full-sequence review and fixes

Reviewed export: `video/build/v2/cut/crowdpulse_v2_reviewed_full_preview_720p.mp4` and matching 1080p master. **4:15 / 255 seconds**, revised from 4:37. All 18 scenes, narration words, team allocation and evidence boundaries remain. Timing and presentation changed; no product feature or validation result was added.

## Defects found and repaired

| In the 4:37 cut | Repair in the reviewed cut |
|---|---|
| N02 ended with 6 seconds after the guide; N07 nearly 7; N13 nearly 9. Several static holds felt like the film had stopped. | Trimmed redundant tails, retaining roughly 1–3 seconds for most spoken scenes. N06 retains a deliberate 4-second product move; N08 retains time to read the recorded explanation. The research question and final line each gain a second. |
| N06's phone entered from an unrelated position, and its recorded screen changed across the N07 boundary. | Dissolve from the existing-system credit into the full composition. Move the phone into N07's exact position, size and first recorded frame before the cut. |
| N07's enlarged readout travelled across the phone before settling on the left; its crop included part of a cut-off footnote. | Expand it into the free space beside the phone. Crop only the complete numerical fields. Keep the same phone/readout composition into N08. |
| N08 hurried between map, reasons, wide dashboard and forecast crops, while the narration named forecasts and confidence before reasons. | Give the scenario switch a full beat, then a measured forecast zoom followed by the explanation detail on “and reasons.” Distinct recorded moments are labelled as detail inserts, rather than implying a continuous simulation clock. |
| N09's changes of approval/audit/notice view were hard cuts with inconsistent framing. | Keep a stable screen frame, enlarge the real approval view and blend into the recorded audit on the spoken name/record clause. Show the notice as a clearly labelled recorded insert. |
| N12's late-warning diagram started about one second after the failure-case sentence. The staff-review screen arrived after “Staff review remains essential.” | Trigger the failure diagram from that sentence's start and the actual review interface from the staff-review sentence. Reveal the probability caveat only when the next sentence introduces it. |
| N13 covered almost the entire actual app with a static comparison for most of its 30 seconds. | Show the recorded SketchFuture interface first, then dissolve to the equal before/after cohorts as the numbers are introduced. Add the map-data/on-site-check takeaway with its sentence. Shorten to 23 seconds. |
| Most scene and internal view boundaries had abrupt visual replacements. | Add restrained 0.3-second scene dissolves and short internal blends. Preserve device/screen aspect ratios and the real UI content. Retime Mrs Chan's closing staff/check movement to the new guide. |

The complete product demonstration remains 53 seconds (N07–N09), compared with 55 previously. It was not shortened into a rapid montage. The presentation now progresses from complete device, to its real numerical readout, to the dashboard, to human review and its recorded result.

## Review method and measured results

- Examined the original cut as a continuous one-second sequence covering **all 277 seconds**, alongside its sentence audio timings. After the fixes, examined **all 255 seconds** of the actual assembled export in the same way.
- Examined **52 additional boundary frames across 13 transitions**: device continuity, readout expansion, phone handoff, scenario switch, forecast and explanation details, approval, audit, notice, privacy evidence, late warning, staff review and cohort comparison. These are sequential-frame and timing checks, not a claim of an uninterrupted human real-time viewing/listening session.
- Compared the finished AAC audio against **all 46 source utterances** by waveform correlation around their expected positions. Minimum correlation **0.949479**; largest measured alignment offset **0.125 ms** at the 8 kHz analysis resolution. This checks correct audio content placement, not pronunciation, human delivery or AI transcription accuracy. Local details: `video/build/v2/qa/reviewed-audio-check.json`.
- All 17 spoken scenes have room for the guide and its final caption. All captions stay inside their scene and the **1,480-pixel** safe width. No narration words or member assignments changed.
- Both exports passed full FFmpeg error-fatal decoding of video and audio with **no decoder errors**. Both contain **7,650 frames at 30 fps**, duration **255.000 seconds**. Master: **1920×1080**; preview: **1280×720**. H.264 limited-range BT.709, AAC stereo at 48 kHz, fast-start MP4.
- Finished audio: **−18.08 LUFS integrated**, **−4.88 dBTP**, **5.2 LU** loudness range. No clipping indicated.
- Rechecked real/simulated labels, fictional self-declared operator disclosure, 24/40 unreachable in **both** plans, offline calibration caveat and pending Melbourne status. No held-out Melbourne data was opened or analysed.
- Python source compilation and Git whitespace checks passed. No app/backend code changed; application test suites were not rerun for this media edit.

Sequential sheets are in `video/build/v2/qa/full-pass-reviewed/`; denser motion sheets are in `video/build/v2/qa/motion-reviewed/`. The original 4:37 exports remain in the cut folder for comparison. The source/rendering changes and updated production documents are version controlled; derived media remains local.

## Remaining production limit

The review still uses the stock Daniel guide voice and clearly labelled team-camera stand-ins. Actual team delivery, pronunciation and camera footage need their own timing review after recording. The visual treatment is substantially more coherent, but those stand-ins cannot demonstrate the presence or vocal performance of the four real presenters. This cut has not been submitted or published.
