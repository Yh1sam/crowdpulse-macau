# Voice lines for the pitch video

Generated from `docs/video/shotlist.json` (script: `docs/video/script.md`). Record each voice-over line as its own file, named by shot, and put the files in `video/build/voice/` (for example `video/build/voice/S03.wav`); `video/assemble.py` then uses your take instead of the robot guide track, shot by shot. Shots spoken on camera (S05, the first 4 s of S06, S12, S19) keep the camera's own sound.

How to record (script section 5C): a phone voice memo 15-20 cm from the mouth, a quiet soft-furnished room, standing, 2-3 takes per line, about 140 words per minute. Read numbers as the pronunciation guide says ("point eight six five", "twenty nineteen", "a hundred and four", "Saint Paul's", "se-NAH-doo"). Bracketed slots are filled after the research is done; record them separately when they exist.

| shot | speaker | line (verbatim) | slot | robot reading | file |
|---|---|---|---|---|---|
| S01 | [MEMBER 4] | This is Ah Po, going to see the Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead. | 11.5 s | 8.0 s | `S01.wav` |
| S02 | [MEMBER 1] | Our phone app counts people on the device. It never sends a picture, only numbers. | 7.0 s | 5.2 s | `S02.wav` |
| S03 | [MEMBER 5] | On our dashboard, with a simulated Golden Week crowd, Senado Square's forecast turns critical, with a confidence score and the reasons why. | 10.0 s | 8.7 s | `S03.wav` |
| S04 | [MEMBER 3] | It recommends a stair-free detour, with notices in Chinese, English and Portuguese. A person decides: approved, and logged. | 9.0 s | 8.3 s | `S04.wav` |
| S05 | ALL | [M1] Technology. [M2] Science. [M3] Engineering. [M4] Medicine. [M5] Business. [ALL] We are CrowdPulse Macau. | 8.5 s | 6.3 s | camera audio |
| S06 | [MEMBER 4] | Every Golden Week, the Ruins of St. Paul's and Senado Square become dangerously crowded. [TEAM TO RESEARCH - MEDICINE: one sentence, at most 12 words, from a cited peer-reviewed source, on how a crowd crush injures the body] | 12.0 s | 5.6 s | `S06.wav` |
| S07 | [MEMBER 5] | In 2019, Macau's tourism office announced attraction forecasts, hours to days ahead. We forecast the next five to fifteen minutes, street by street, from phones staff place temporarily. | 13.0 s | 13.0 s | `S07.wav` |
| S08 | [MEMBER 3] | Privacy is enforced in code. A numbers-only reading: accepted. Add a face-ID field: rejected. Upload an image: refused. | 9.0 s | 8.8 s | `S08.wav` |
| S09 | [MEMBER 3] | Confidence is discounted for unreliable sensors and unusual conditions. Below sixty percent, a person must review it. | 8.0 s | 7.7 s | `S09.wav` |
| S10 | [MEMBER 2] | On held-out simulated days, fifteen-minute forecasts score an F1 of 0.865, against 0.795 for assuming nothing changes, and catch 91 percent of critical minutes, against 79. Forecasts flagged as uncertain are right only about 56 percent of the time; the rest, 97. | 22.0 s | 21.0 s | `S10.wav` |
| S11 | [MEMBER 1] | On eleven frames of a public-domain street clip, the open YOLO model in our app counted 97 percent as many nearby people as a careful hand count; Apple's detector, 55. In the densest frames, 82; across the whole scene, only 27. | 18.0 s | 17.1 s | `S11.wav` |
| S12 | [MEMBER 1] then [MEMBER 2] | [M1] Our first version of this test had a frame-timing bug. [M2] It was caught, fixed, and we published the correction. | 10.0 s | 6.6 s | camera audio |
| S13 | [MEMBER 1] | Eleven frames is small, so we tested two thousand annotated mall frames. The detector counted only 59 percent, but 93 percent of its boxes were people: a steady under-count. Twenty labelled frames calibrated that one camera, cutting error from thirteen to about three people per frame. A lead, not proof. | 22.0 s | 20.3 s | `S13.wav` |
| S14 | [MEMBER 3] | In a recorded simulation, approving the redirect left Senado less crowded by the end than doing nothing, but only modestly: it stayed critical. The effect rests on a diversion we assumed, not measured, and the crowd built so fast the alert came with it, not before. | 20.5 s | 16.6 s | `S14.wav` |
| S15 | [MEMBER 4] | One click tests another recommendation, at St. Dominic's, on our model of Macau's streets: walkers lose seventeen seconds, wheelchair users thirty. And 24 of our 40 simulated wheelchair users had no step-free route either way. Real barrier, or missing map data? Only a street survey can tell. | 21.0 s | 19.5 s | `S15.wav` |
| S16 | [MEMBER 2] | Because our forecasting results are simulated, we're testing them on real counts from 99 Melbourne street sensors: a test announced before its result. [RESULT PENDING - fill after analysis, report honestly whatever it shows] | 17.0 s | 9.4 s | `S16.wav` |
| S17 | [MEMBER 5] | Phones on temporary mounts can serve one festival, then move to the next. [TEAM TO RESEARCH - BUSINESS: at most 10 words, sources on screen: cost of a phone kit vs a fixed counting camera] The whole chain runs end to end in simulation, with 104 automated tests passing. | 18.0 s | 10.2 s | `S17.wav` |
| S18 | [MEMBER 4] | Back to Ah Po: her main route stays open, with staff beside her. | 6.0 s | 4.5 s | `S18.wav` |
| S19 | [MEMBER 5], [MEMBER 3], [MEMBER 2], [MEMBER 1] | [M5] Next: a supervised street pilot in Macau, with permission. [M3] The AI recommends. [M2] A person decides. [M1] Nothing identifying leaves the phone. | 11.0 s | 9.4 s | camera audio |

Shots per member: [MEMBER 1] S02, S05, S11, S12, S13, S19 · [MEMBER 2] S05, S10, S12, S16, S19 · [MEMBER 3] S04, S05, S08, S09, S14, S19 · [MEMBER 4] S01, S05, S06, S15, S18 · [MEMBER 5] S03, S05, S07, S17, S19

If a take runs longer than its slot, use the overrun cuts in script section 6 rather than speaking faster; the video is re-timed to your real takes.
