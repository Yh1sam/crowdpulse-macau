# Voice lines for the pitch video

Generated from `docs/video/shotlist.json` (script: `docs/video/script.md`) after the round-2 narration lock (16 Oct 2026) and its review (17 Oct); robot readings are from `video/guide.py` (`video/build/guide/guide.json`, re-run 17 Oct). Record each voice-over line as its own file, named by shot, and put the files in `video/build/voice/` (for example `video/build/voice/S03.wav`, `video/build/voice/S17b.wav`); `video/assemble.py` then uses your take instead of the robot guide track, shot by shot. Shots spoken on camera (S05, the first 4 s of S06, S12, S19) keep the camera's own sound.

How to record (script section 5C): a phone voice memo 15-20 cm from the mouth, a quiet soft-furnished room, standing, 2-3 takes per line, about 140 words per minute. Read numbers as the pronunciation guide says ("point eight six five", "a hundred and twenty-four", "Saint Paul's", "se-NAH-doo"). The robot says "a hundred and twenty-four" in S17 because `video/guide.py` has no rule for 124 yet; say "a hundred and twenty-four". S01's voice starts after its 3 s opening title, so leave the title silent. The research slots in S06 and S17 were filled on 13 Oct; the only bracketed slot left is the S16 Melbourne result, filled after the analysis and recorded separately when it exists.

| shot | speaker | line (verbatim) | slot | robot reading | file |
|---|---|---|---|---|---|
| S01 | [MEMBER 4] | This is Mrs Chan, going to see the Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead. | 13.5 s (voice from 3.0 s, after the title) | 8.3 s | `S01.wav` |
| S02 | [MEMBER 1] | Our phone app counts people on the device. It never sends a picture, only numbers. | 7.0 s | 5.2 s | `S02.wav` |
| S03 | [MEMBER 2] | On our dashboard, with a simulated Golden Week crowd, Senado Square's forecast turns critical, with a confidence score and the reasons why. | 10.0 s | 8.7 s | `S03.wav` |
| S04 | [MEMBER 3] | It recommends a stair-free detour, with notices in Chinese, English and Portuguese. A person decides: approved, and logged. | 9.0 s | 8.3 s | `S04.wav` |
| S05 | ALL | [M1] Technology. [M2] Science. [M3] Engineering and business. [M4] Medicine. [ALL] We are CrowdPulse Macau. | 8.5 s | 6.0 s | camera audio |
| S06 | [MEMBER 4] | This Golden Week, police briefly imposed crowd control at the Ruins on three afternoons. In a crush, victims typically suffocate standing up, from chest compression. | 12.0 s | 10.7 s | `S06.wav` |
| S07 | [MEMBER 4] | Macau's police already run a crowd warning system here, and plan to expand it. We propose movable, numbers-only phones, and forecasts with a confidence score. | 13.0 s | 10.3 s | `S07.wav` |
| S08 | [MEMBER 3] | Privacy is enforced in code. A numbers-only reading: accepted. Add a face-ID field: rejected. Upload an image: refused. | 9.0 s | 8.8 s | `S08.wav` |
| S09 | [MEMBER 3] | Confidence is discounted for unreliable sensors and unusual conditions. Below sixty percent, a person must review it. | 8.0 s | 7.7 s | `S09.wav` |
| S10 | [MEMBER 2] | On held-out simulated days, fifteen-minute forecasts score an F1 of 0.865, against 0.795 for assuming nothing changes, and catch 91 percent of critical minutes, against 79. Forecasts flagged as uncertain are right only about 56 percent of the time; the rest, 97. | 22.0 s (voice from 0.8 s) | 21.0 s | `S10.wav` |
| S11 | [MEMBER 1] | On eleven frames of a public-domain street clip, the open YOLO model in our app counted 97 percent as many nearby people as a careful hand count; across the whole scene, only 27. | 15.0 s | 12.1 s | `S11.wav` |
| S12 | [MEMBER 1] then [MEMBER 2] | [M1] Our first version of this test had a frame-timing bug. [M2] It was caught, fixed, and we published the correction. | 10.0 s | 6.6 s | camera audio |
| S13 | [MEMBER 1] | On two thousand annotated mall frames, the detector steadily under-counted, yet 93 percent of its boxes were people. Twenty labelled frames calibrated that one camera, cutting error from thirteen to about three people per frame. A lead, not proof. | 17.5 s | 15.8 s | `S13.wav` |
| S14 | [MEMBER 3] | In a recorded simulation, approving the redirect left Senado less crowded by the end than doing nothing, but only modestly: it stayed critical. The effect rests on a diversion we assumed, not measured. Our failure case: the crowd built so fast the alert came with it, not before. | 21.5 s | 17.9 s | `S14.wav` |
| S15 | [MEMBER 4] | One click tests another recommendation, at St. Dominic's, on our model of Macau's streets: walkers lose seventeen seconds, wheelchair users thirty. And 24 of our 40 simulated wheelchair users had no step-free route either way. Real barrier, or missing map data? Only a street survey can tell. | 21.0 s | 19.5 s | `S15.wav` |
| S16 | [MEMBER 2] | Because our forecasting results are simulated, we're testing the same method on real counts from 99 Melbourne street sensors: a test announced before its result. [RESULT PENDING - fill after analysis, report honestly whatever it shows] | 18.0 s | 10.1 s | `S16.wav` |
| S17 | [MEMBER 1] | Phones on temporary mounts can serve one festival, then move to the next. The intended user is Macau's police, who run crowd control. The whole chain runs end to end in simulation, with 124 automated tests passing. | 18.5 s | 14.7 s | `S17.wav` |
| S17b | [MEMBER 3] | The approving operator, named in the audit log, and the department running it. Every notice says an AI forecast is involved. | 10.0 s (voice from 0.5 s) | 7.4 s | `S17b.wav` |
| S18 | [MEMBER 4] | Back to Mrs Chan: her main route stays open, with staff beside her. | 6.0 s | 4.8 s | `S18.wav` |
| S19 | [MEMBER 3], [MEMBER 4], [MEMBER 2], [MEMBER 1] | [M3] Next: a supervised street pilot in Macau, with permission. [M4] The AI recommends. [M2] A person decides. [M1] Nothing identifying leaves the phone. | 11.0 s | 9.4 s | camera audio |

Shots per member (four members): [MEMBER 1] S02, S05, S11, S12, S13, S17, S19 · [MEMBER 2] S03, S05, S10, S12, S16, S19 · [MEMBER 3] S04, S05, S08, S09, S14, S17b, S19 · [MEMBER 4] S01, S05, S06, S07, S15, S18, S19

In S05, [MEMBER 3] says "Engineering and business." In S19 the relay runs [MEMBER 3] ("Next…"), [MEMBER 4] ("The AI recommends."), [MEMBER 2], [MEMBER 1].

If a take runs longer than its slot, use the overrun cuts in script section 6 rather than speaking faster; the video is re-timed to your real takes.
