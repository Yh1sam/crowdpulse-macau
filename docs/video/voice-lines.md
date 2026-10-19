# Voice lines for the pitch video

Latest introduction and comparison revision: 19 October 2026. Rendered review cut: **4:54.0 (294 s)**. Narration: **624 written words**, approximately **636 spoken-equivalent words**. Measured robot-guide speech: **245.70 s**. This recording hand-off follows the canonical shotlist and guide report.

Keep the four-member team and record each voice-over separately into `video/build/voice/SNN.wav`. The assembler uses those takes instead of the robot guides. The guides are timing references, not final team narration.

Record 2–3 natural takes in a quiet room, 15–20 cm from the microphone. Follow the pronunciation guide in `script.md`. Voice starts 0.2 s into each shot except S10 (0.8 s) and S17b (0.5 s). Re-time any shot that a real take exceeds; the assembler stops on overrun. With only six seconds below 5:00, longer takes need equivalent cuts elsewhere.

**S05 delivery:** each member stays on camera for both complete contribution sentences. Cut between members after the second sentence, with a breath. All four then speak the full introduction and research question together while the group remains visible. The guide's cuts are M2 6.07 s, M3 12.80 s, M4 19.93 s and group 28.83 s; the core question runs 31.85–39.92 s. Begin the title animation only after it finishes (about 39.95 s), and preserve the 41.50–43.50 s silent hold. S05's guide alone uses pitch-preserving 0.9 tempo; the team records naturally.

**S07 delivery:** credit the police context first, then give "But how is ours different?" its own central spoken beat. Introduce event staff and the proposed temporary sensing kit before phones, as support for the existing system. There is no opening corner chapter card or moral comparison.

Camera shots S05, S06 and S19 need synchronized WAVs after their camera edit; source-video audio is not included automatically. Names, school, supervisor and actual contribution credits remain for the team to complete.

S16 is a complete eight-second pending-result statement. Replace it only when a valid pre-registered result exists, then update timings and captions and keep the full cut under five minutes.

| Shot | Global time | Speaker | Exact narration | Slot | Guide reading / ends at |
|---|---|---|---|---:|---:|
| S01 | 0:00.0–0:12.0 | [MEMBER 4] (VO) | This is Mrs Chan, going to see the Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead. | 12.0 s | 8.28 s / 8.48 s |
| S06 | 0:12.0–0:27.0 | [MEMBER 4] (on camera 0-6.9 s, then VO) | Mrs Chan is made up. The crowds are not. This Golden Week, police briefly imposed crowd control at the Ruins on three afternoons. In a crush, victims typically suffocate standing up, from chest compression. | 15.0 s | 13.51 s / 13.71 s |
| S05 | 0:27.0–1:10.5 | ALL (on camera: two sentences each, then shared introduction and core question) | [M1] I worked on the phone app. It counts people on the device, so only numbers leave the phone. [M2] I worked on the forecasts. We compare them with simple baselines to see whether they actually add value. [M3] I worked on the server and deployment plan. We built in privacy checks and made sure every approval is logged. [M4] I worked on health and accessibility. We test who might be left behind, including wheelchair users, before discussing a route. [ALL] Together, we are CrowdPulse Macau. Our question: can ordinary phones, sending only numbers, help forecast crowds without identifying anyone? | 43.5 s | 39.72 s / 39.92 s |
| S07 | 1:10.5–1:34.5 | [MEMBER 2] (VO) | Macau's police already run a crowd warning system here. But how is ours different? We propose a temporary sensing kit for event staff, to support the existing system. Staff place the phones; the phones count on-device and send only numbers. On the dashboard, staff review forecasts and suggested detours before acting. | 24.0 s | 20.00 s / 20.20 s |
| S08 | 1:34.5–1:43.5 | [MEMBER 3] (VO) | We enforce privacy in code. Our server accepts a numbers-only reading, rejects one with a face-ID field, and refuses an image. | 9.0 s | 8.37 s / 8.57 s |
| S09 | 1:43.5–1:54.5 | [MEMBER 4] (VO) | Unreliable or unusual sensor data lowers our confidence score. The adjusted score tells staff when to review a forecast; it isn't a calibrated probability. | 11.0 s | 9.84 s / 10.04 s |
| S02 | 1:54.5–2:01.5 | [MEMBER 1] (VO) | Here's what we built. Our phone app counts people on the device, and sends only numbers. | 7.0 s | 5.42 s / 5.62 s |
| S03 | 2:01.5–2:11.5 | [MEMBER 2] (VO) | On our dashboard, with a simulated Golden Week crowd, Senado Square's forecast turns critical. It shows how sure it is, and why. | 10.0 s | 8.57 s / 8.77 s |
| S04 | 2:11.5–2:20.5 | [MEMBER 3] (VO) | It recommends a stair-free detour, with notices in Chinese, English and Portuguese. A person must approve it, and we log their name. | 9.0 s | 8.20 s / 8.40 s |
| S10 | 2:20.5–2:37.5 | [MEMBER 2] (VO) | On simulated days it had never seen, our fifteen-minute forecasts scored an F1 of 0.865, against 0.795 for assuming nothing changes, and caught 91 percent of critical minutes, against 79. | 17.0 s | 14.64 s / 15.44 s |
| S11 | 2:37.5–2:54.5 | [MEMBER 1] (VO) | Then we tried real footage. On eleven frames of a public-domain street clip, the open YOLO model in our app counted 97 percent as many nearby people as a careful hand count; across the whole scene, only 27. | 17.0 s | 14.00 s / 14.20 s |
| S13 | 2:54.5–3:12.5 | [MEMBER 1] (VO) | On two thousand frames from one mall camera, the detector under-counted. Twenty labelled frames let us calibrate that camera, cutting counting error from thirteen to about three people per frame. A fixed guess scored about five. This calibration is not yet in the app. | 18.0 s | 15.63 s / 15.83 s |
| S14 | 3:12.5–3:33.5 | [MEMBER 3] (VO) | In a recorded simulation, approving the redirect left Senado modestly less crowded, but still above our prototype alert threshold. The diversion was assumed, not measured. Our failure case: the surge crossed that threshold before a confident warning. Staff on the ground stay in charge. | 21.0 s | 17.98 s / 18.18 s |
| S15 | 3:33.5–3:50.5 | [MEMBER 4] (VO) | On Macau's mapped streets, we stress-tested a full corridor closure. Twenty-four of forty simulated wheelchair users had no step-free route in either plan. This isn't a route safety check: staff must inspect the route and assist people on site. | 17.0 s | 14.53 s / 14.73 s |
| S16 | 3:50.5–3:58.5 | [MEMBER 2] (VO) | Our next test uses real Melbourne pedestrian counts under pre-registered rules. Results are still pending. | 8.0 s | 6.48 s / 6.68 s |
| S17 | 3:58.5–4:17.5 | [MEMBER 1] (VO over B-roll) | Phones on temporary mounts can serve one festival, then move to the next. We see Macau's police, who run crowd control, as the intended user. The whole chain runs end to end in simulation, with 124 automated tests passing. | 19.0 s | 15.46 s / 15.66 s |
| S17b | 4:17.5–4:29.5 | [MEMBER 3] (VO) | If it fails, who answers? The person who approved it, named in our log, and the department running it. Every notice says an AI forecast is involved. | 12.0 s | 9.45 s / 9.95 s |
| S18 | 4:29.5–4:36.5 | [MEMBER 4] (VO) | Back to Mrs Chan. The system flags the risk; staff check her route and stay beside her. | 7.0 s | 5.84 s / 6.04 s |
| S19 | 4:36.5–4:48.0 | [MEMBER 3], [MEMBER 4], [MEMBER 2], [MEMBER 1] (on camera, relay) | [M3] Next, we want a supervised street pilot in Macau, with permission. [M4] The AI recommends. [M2] A person decides. [M1] Nothing identifying leaves the phone. | 11.5 s | 9.78 s / 9.98 s |

| Member | Written words |
|---|---:|
| MEMBER 1 | 160 |
| MEMBER 2 | 139 |
| MEMBER 3 | 145 |
| MEMBER 4 | 161 |
| Shared group introduction and question | 19 |

Q&A-only figures include the model-only 56% / 97% uncertainty comparison and 93% box precision. Do not add them back into the narration. S13 reports one-camera calibration; S15 is a synthetic full-closure stress test. Neither is a field-safety certification.
