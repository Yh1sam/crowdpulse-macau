# Voice lines for the pitch video

Current clarity revision: 19 October 2026. Review cut: **4:22.0**. Narration: **556 written words**, approximately **568 spoken-equivalent words**. Measured robot-guide speech: **215.55 s**. This recording hand-off follows the current shotlist and guide report.

Keep the four-member team and existing delivery. Record each voice-over separately into `video/build/voice/SNN.wav`. The assembler uses those takes instead of the robot guides. The guides are timing references, not final team narration.

Record 2–3 natural takes in a quiet room, 15–20 cm from the microphone. Read numerical values as the pronunciation guide in `script.md` specifies. Voice starts 0.2 s into each shot except S10 (0.8 s) and S17b (0.5 s). Re-time a shot if the real take exceeds its slot; the assembler now stops on overrun.

Camera shots S05, S06 and S19 also need synchronized WAVs after their camera edit. Source-video audio is not automatically included by the assembler. Names, school, supervisor and actual contribution credits remain for the team to complete.

S16 already contains a complete eight-second pending-result statement. Replace it only when a valid pre-registered result exists, then update timing and related captions.

| Shot | Global time | Speaker | Exact narration | Slot | Guide reading / ends at |
|---|---|---|---|---:|---:|
| S01 | 0:00.0–0:12.0 | [MEMBER 4] (VO) | This is Mrs Chan, going to see the Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead. | 12.0 s | 8.28 s / 8.48 s |
| S06 | 0:12.0–0:27.0 | [MEMBER 4] (on camera 0-6.9 s, then VO) | Mrs Chan is made up. The crowds are not. This Golden Week, police briefly imposed crowd control at the Ruins on three afternoons. In a crush, victims typically suffocate standing up, from chest compression. | 15.0 s | 13.51 s / 13.71 s |
| S05 | 0:27.0–0:40.5 | ALL (on camera: one line each, then together) | [M1] I worked on the app. [M2] I worked on the forecasts. [M3] I worked on the server, and how we'd deploy it. [M4] I worked on health and accessibility. [ALL] Together, we are CrowdPulse Macau. | 13.5 s | 10.76 s / 10.96 s |
| S07 | 0:40.5–1:02.5 | [MEMBER 2] (VO) | Macau's police already run a crowd warning system here. We believe crowd safety shouldn't cost privacy, or leave anyone behind. Staff place our phones on temporary mounts: they count on-device and send only numbers to the dashboard. Forecasts show their confidence; an operator reviews each suggested detour. | 22.0 s | 18.81 s / 19.01 s |
| S08 | 1:02.5–1:11.5 | [MEMBER 3] (VO) | We enforce privacy in code. Our server accepts a numbers-only reading, rejects one with a face-ID field, and refuses an image. | 9.0 s | 8.37 s / 8.57 s |
| S09 | 1:11.5–1:22.5 | [MEMBER 4] (VO) | Unreliable or unusual sensor data lowers our confidence score. The adjusted score tells staff when to review a forecast; it isn't a calibrated probability. | 11.0 s | 9.84 s / 10.04 s |
| S02 | 1:22.5–1:29.5 | [MEMBER 1] (VO) | Here's what we built. Our phone app counts people on the device, and sends only numbers. | 7.0 s | 5.42 s / 5.62 s |
| S03 | 1:29.5–1:39.5 | [MEMBER 2] (VO) | On our dashboard, with a simulated Golden Week crowd, Senado Square's forecast turns critical. It shows how sure it is, and why. | 10.0 s | 8.57 s / 8.77 s |
| S04 | 1:39.5–1:48.5 | [MEMBER 3] (VO) | It recommends a stair-free detour, with notices in Chinese, English and Portuguese. A person must approve it, and we log their name. | 9.0 s | 8.20 s / 8.40 s |
| S10 | 1:48.5–2:05.5 | [MEMBER 2] (VO) | On simulated days it had never seen, our fifteen-minute forecasts scored an F1 of 0.865, against 0.795 for assuming nothing changes, and caught 91 percent of critical minutes, against 79. | 17.0 s | 14.64 s / 15.44 s |
| S11 | 2:05.5–2:22.5 | [MEMBER 1] (VO) | Then we tried real footage. On eleven frames of a public-domain street clip, the open YOLO model in our app counted 97 percent as many nearby people as a careful hand count; across the whole scene, only 27. | 17.0 s | 14.00 s / 14.20 s |
| S13 | 2:22.5–2:40.5 | [MEMBER 1] (VO) | On two thousand frames from one mall camera, the detector under-counted. Twenty labelled frames let us calibrate that camera, cutting counting error from thirteen to about three people per frame. A fixed guess scored about five. This calibration is not yet in the app. | 18.0 s | 15.63 s / 15.83 s |
| S14 | 2:40.5–3:01.5 | [MEMBER 3] (VO) | In a recorded simulation, approving the redirect left Senado modestly less crowded, but still above our prototype alert threshold. The diversion was assumed, not measured. Our failure case: the surge crossed that threshold before a confident warning. Staff on the ground stay in charge. | 21.0 s | 17.98 s / 18.18 s |
| S15 | 3:01.5–3:18.5 | [MEMBER 4] (VO) | On Macau's mapped streets, we stress-tested a full corridor closure. Twenty-four of forty simulated wheelchair users had no step-free route in either plan. This isn't a route safety check: staff must inspect the route and assist people on site. | 17.0 s | 14.53 s / 14.73 s |
| S16 | 3:18.5–3:26.5 | [MEMBER 2] (VO) | Our next test uses real Melbourne pedestrian counts under pre-registered rules. Results are still pending. | 8.0 s | 6.48 s / 6.68 s |
| S17 | 3:26.5–3:45.5 | [MEMBER 1] (VO over B-roll) | Phones on temporary mounts can serve one festival, then move to the next. We see Macau's police, who run crowd control, as the intended user. The whole chain runs end to end in simulation, with 124 automated tests passing. | 19.0 s | 15.46 s / 15.66 s |
| S17b | 3:45.5–3:57.5 | [MEMBER 3] (VO) | If it fails, who answers? The person who approved it, named in our log, and the department running it. Every notice says an AI forecast is involved. | 12.0 s | 9.45 s / 9.95 s |
| S18 | 3:57.5–4:04.5 | [MEMBER 4] (VO) | Back to Mrs Chan. The system flags the risk; staff check her route and stay beside her. | 7.0 s | 5.84 s / 6.04 s |
| S19 | 4:04.5–4:16.0 | [MEMBER 3], [MEMBER 4], [MEMBER 2], [MEMBER 1] (on camera, relay) | [M3] Next, we want a supervised street pilot in Macau, with permission. [M4] The AI recommends. [M2] A person decides. [M1] Nothing identifying leaves the phone. | 11.5 s | 9.78 s / 9.98 s |

| Member | Written words |
|---|---:|
| MEMBER 1 | 147 |
| MEMBER 2 | 122 |
| MEMBER 3 | 135 |
| MEMBER 4 | 147 |
| Shared group sentence | 5 |

Q&A-only figures include the model-only 56% / 97% uncertainty comparison and 93% box precision. Do not add them back into the narration. S13 reports one-camera calibration; S15 is a synthetic full-closure stress test. Neither is a field-safety certification.
