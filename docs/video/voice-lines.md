# Voice lines for the pitch video

Spoken chapter-question revision: 19 October 2026. Checked guide review cut: **4:58.0 (298 s)**. Narration: **620 written words**, approximately **632 spoken-equivalent words**. Guide audio totals **254.19 s**, including deliberate opening-question pauses.

Record each voice-over into `video/build/voice/SNN.wav`; the assembler uses real takes in preference to the robot guides. Camera shots S05, S06 and S19 also need synchronized WAVs after editing: source-video sound is not included automatically. Names, school, supervisor and confirmed contribution credits remain to be supplied.

Record 2–3 natural, clear takes in a quiet room, 15–20 cm from the microphone. Voice starts at **0.2 s in every shot except S17b (0.5 s)**; S10 now uses 0.2 s. The two seconds below 5:00 leave little space for overruns, so time actual takes before locking. The assembler stops if a take exceeds its slot.

**Question delivery:** S06, S08, S02, S10, S14, S16 and S17 speak the opening question, let it own the screen, then answer from about 2.6 s into the shot. The guides place the body at 2.4 s in the WAV. The 84 px central question docks as a persistent 40 px header by 2.4 s (36 px for S02). S02/S08 speaker strips wait until 2.6 s. S07 retains its separate question after police context; S17b's large title stands alone until its first row/footer at 2.6 s. Do not rush or remove a question to fit a take.

**S05 delivery:** preserve two complete sentences per member and all four speaking the full group introduction and research question. Guide-relative cuts: M2 6.07 s, M3 12.80 s, M4 19.93 s and group 28.83 s; core question 31.85–39.92 s; title animation from about 39.95 s; silent hold 41.50–43.50 s. S05 alone uses pitch-preserving 0.9-tempo guide audio; record natural voices and re-key cuts to the actual takes.

**S06 camera interval:** M4's planned visible take is 2.4–9.3 s into S06, or 0:14.4–0:21.3 globally. Record the full line so its question and remaining answer are available as VO.

**S07 delivery:** existing police context → "But how is ours different?" → event staff and a proposed temporary sensing kit → phones and reviewed actions. It supports the existing system; no moral comparison or police-accuracy claim.

**S16:** keep the complete pending-result statement until a valid pre-registered result exists. Any replacement must be retimed and keep the full film below five minutes.

| Shot | Global time | Speaker | Exact narration | Slot | Guide audio / ends at |
|---|---|---|---|---:|---:|
| S01 | 0:00.0–0:12.0 | [MEMBER 4] (VO) | This is Mrs Chan, going to see the Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead. | 12.0 s | 8.28 s / 8.48 s |
| S06 | 0:12.0–0:29.0 | [MEMBER 4] (question VO, on camera 2.4-9.3 s, then VO) | Why does it matter? Mrs Chan is made up. The crowds are not. This Golden Week, police briefly imposed crowd control at the Ruins on three afternoons. In a crush, victims typically suffocate standing up, from chest compression. | 17.0 s | 15.91 s / 16.11 s |
| S05 | 0:29.0–1:12.5 | ALL (on camera: two sentences each, then shared introduction and core question) | [M1] I worked on the phone app. It counts people on the device, so only numbers leave the phone. [M2] I worked on the forecasts. We compare them with simple baselines to see whether they actually add value. [M3] I worked on the server and deployment plan. We built in privacy checks and made sure every approval is logged. [M4] I worked on health and accessibility. We test who might be left behind, including wheelchair users, before discussing a route. [ALL] Together, we are CrowdPulse Macau. Our question: can ordinary phones, sending only numbers, help forecast crowds without identifying anyone? | 43.5 s | 39.72 s / 39.92 s |
| S07 | 1:12.5–1:36.5 | [MEMBER 2] (VO) | Macau's police already run a crowd warning system here. But how is ours different? We propose a temporary sensing kit for event staff, to support the existing system. Staff place the phones; the phones count on-device and send only numbers. On the dashboard, staff review forecasts and suggested detours before acting. | 24.0 s | 20.00 s / 20.20 s |
| S08 | 1:36.5–1:46.5 | [MEMBER 3] (VO) | Can it be trusted? Our server accepts a numbers-only reading, rejects one with a face-ID field, and refuses an image. | 10.0 s | 8.84 s / 9.04 s |
| S09 | 1:46.5–1:57.5 | [MEMBER 4] (VO) | Unreliable or unusual sensor data lowers our confidence score. The adjusted score tells staff when to review a forecast; it isn't a calibrated probability. | 11.0 s | 9.84 s / 10.04 s |
| S02 | 1:57.5–2:05.5 | [MEMBER 1] (VO) | What did we build? Our phone app counts people on the device, and sends only numbers. | 8.0 s | 6.41 s / 6.61 s |
| S03 | 2:05.5–2:15.5 | [MEMBER 2] (VO) | On our dashboard, with a simulated Golden Week crowd, Senado Square's forecast turns critical. It shows how sure it is, and why. | 10.0 s | 8.57 s / 8.77 s |
| S04 | 2:15.5–2:24.5 | [MEMBER 3] (VO) | It recommends a stair-free detour, with notices in Chinese, English and Portuguese. A person must approve it, and we log their name. | 9.0 s | 8.20 s / 8.40 s |
| S10 | 2:24.5–2:42.5 | [MEMBER 2] (VO) | Does it work? On unseen simulated days, our fifteen-minute forecasts scored an F1 of 0.865, against 0.795 for assuming nothing changes, and caught 91 percent of critical minutes, against 79. | 18.0 s | 16.63 s / 16.83 s |
| S11 | 2:42.5–2:59.5 | [MEMBER 1] (VO) | Then we tried real footage. On eleven frames of a public-domain street clip, the open YOLO model in our app counted 97 percent as many nearby people as a careful hand count; across the whole scene, only 27. | 17.0 s | 14.00 s / 14.20 s |
| S13 | 2:59.5–3:17.5 | [MEMBER 1] (VO) | On two thousand frames from one mall camera, the detector under-counted. Twenty labelled frames let us calibrate that camera, cutting counting error from thirteen to about three people per frame. A fixed guess scored about five. This calibration is not yet in the app. | 18.0 s | 15.63 s / 15.83 s |
| S14 | 3:17.5–3:38.5 | [MEMBER 3] (VO) | Does acting help? In a recorded simulation, approving the redirect left Senado modestly less crowded, but still above our prototype alert threshold. The diversion was assumed, not measured. Our failure case: the surge crossed that threshold before a confident warning. Staff on the ground stay in charge. | 21.0 s | 20.38 s / 20.58 s |
| S15 | 3:38.5–3:55.5 | [MEMBER 4] (VO) | On Macau's mapped streets, we stress-tested a full corridor closure. Twenty-four of forty simulated wheelchair users had no step-free route in either plan. This isn't a route safety check: staff must inspect the route and assist people on site. | 17.0 s | 14.53 s / 14.73 s |
| S16 | 3:55.5–4:03.5 | [MEMBER 2] (VO) | What's next? A pre-registered test on real Melbourne pedestrian counts. Results are still pending. | 8.0 s | 7.60 s / 7.80 s |
| S17 | 4:03.5–4:21.5 | [MEMBER 1] (VO over B-roll) | Can it happen? Phones on temporary mounts can serve different festivals. Macau's police are our intended user. The prototype runs end to end in simulation, with 124 automated tests passing. | 18.0 s | 14.58 s / 14.78 s |
| S17b | 4:21.5–4:33.5 | [MEMBER 3] (VO) | If it fails, who answers? The person who approved it, named in our log, and the department running it. Every notice says an AI forecast is involved. | 12.0 s | 9.45 s / 9.95 s |
| S18 | 4:33.5–4:40.5 | [MEMBER 4] (VO) | Back to Mrs Chan. The system flags the risk; staff check her route and stay beside her. | 7.0 s | 5.84 s / 6.04 s |
| S19 | 4:40.5–4:52.0 | [MEMBER 3], [MEMBER 4], [MEMBER 2], [MEMBER 1] (on camera, relay) | [M3] Next, we want a supervised street pilot in Macau, with permission. [M4] The AI recommends. [M2] A person decides. [M1] Nothing identifying leaves the phone. | 11.5 s | 9.78 s / 9.98 s |

| Member | Written words |
|---|---:|
| MEMBER 1 | 151 |
| MEMBER 2 | 138 |
| MEMBER 3 | 147 |
| MEMBER 4 | 165 |
| Shared group introduction and question | 19 |

Keep model-only uncertainty and Mall box-precision figures in Q&A. Calibration is one-camera/offline; the closure check is synthetic; neither certifies a safe route.
