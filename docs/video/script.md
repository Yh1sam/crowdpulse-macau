# CrowdPulse Macau: The Next Fifteen Minutes, Street by Street
Round-one pitch video · Imperial College London Hackathon Hong Kong & Macau 2026 · High School track · Challenge 2(c) Responsible AI

**Runtime:** 4:19.5 (259.5 s) at the 140 wpm planning rate. The target is 3:45-4:20 and the hard limits are 3:00-5:00. That leaves only 0.5 s of slack, so the cut is re-timed from the real takes, and a locked cut of up to 4:45 is accepted against the 5:00 hard limit (section 6, "Runtime control").

**Word count:**

| what is counted | words |
|---|---|
| Verbatim narration written out (speaker tags and placeholders excluded) | 493 |
| Reserved slot words: medicine ≤12, Melbourne result ≤15, business ≤10 | 37 |
| Final narration | ≈530 |
| Spoken equivalent, with numbers read aloud ("point eight six five") | ≈541 |

At 140 words per minute, ≈541 words take 3:52 of speech. The other ≈28 s are visual-only beats: the title and its 2 s hold, the roll-call cuts, the terminal stamps, the evidence legend, the correction graphic, the relay hand-offs and the 6 s end card.

**Guide-voice check:** `say -v Daniel -r 155` reads the 504 spoken-equivalent words (slots excluded) in about 205.3 s, which is about 147 wpm. (Measured shot by shot in the second review; S12's reworded line, re-measured in the third review, added 0.1 s; S11's reworded line, re-measured in this revision, adds 0.3 s: 16.7 → 17.0 s.) Every shot's guide reading fits inside its slot, but the evidence shots are tight:
- S07 is full (13.0 of 13.0 s; 29 spoken words, 28 written), S08 almost full (8.75 of 9.0 s) and S01 nearly full (24 words in the 10.5 s after the 1 s title, 0.98 at 140 wpm; guide 7.95 s).
- Eight shots (S07, S10, S11, S13-S17) run at 0.95-0.98 of their slots at 140 wpm.
- Read at about 130 wpm, the cut would run about 4:37: over the 4:20 target, still under 5:00.
- No content is cut in advance. A timed read-through before the voice shoot decides whether cuts 5 and 2 go in first (section 6, "Runtime control", gives the decision and the reason).
- The overrun plan in section 6 names the cut that absorbs each tight shot. Mark it in the script before the voice shoot.

**Built from:**
- **Spine:** the judges' top-ranked "demo" draft: working product first, then the why, then responsible design, then about 50% evidence, then feasibility.
- **From the "rubric" draft:** chapter question cards, status badges with source footers, on-screen definitions, the pre-announced Melbourne test, the limit chips and the "never say" list.
- **From the "story" draft:** the Ah Po bookend, the one-word STEMB roll call, the 40-dot grid, the plain-English lines and the rule that Senado never turns green.
- **Fact-checks:** every must-fix and should-fix from the three fact-checks, the final review, the second review (18 findings), the third review (11 findings) and the fourth review (17 findings, this revision) is applied. The appendix lists them, plus the options not taken and why.

---

## 1. Concept, and why it should score well

**Show it working, then prove it honestly.**

**Opening.** A 10-second illustrative moment, clearly labelled as fiction: Ah Po, a wheelchair user, heads to see the Ruins of St. Paul's and can only see people's backs. The real software then runs the whole loop in 26 seconds:
- the iOS app, in the iPhone Simulator, counts people on a public-domain clip;
- only numbers leave it;
- Senado Square's forecast turns CRITICAL, with a confidence score and reasons;
- the system suggests a stair-free detour with notices in Chinese, English and Portuguese;
- the recommendation waits for a person's approval (the APPROVE click is scripted for this recording, and a small footer says so), and the audit log records it.

**Middle.** A one-word STEMB roll call introduces the team. The video then:
- states the problem;
- credits Macau's 2019 hours-to-days forecasts and claims only the gap (the next 5-15 minutes, street by street);
- proves privacy live (202, then 422, then 403);
- explains the confidence gate.

About half the runtime is evidence. Every number wears a status badge (SIMULATED, REAL DATA, MODEL CHECK, PENDING, CORRECTED) and a source footer, and every limit is spoken:
- forecasting is synthetic;
- the detector under-counts, and calibration is one camera, tested post hoc;
- in the simulation, approval left Senado only modestly less crowded by the end, and it stayed critical (on screen: 32 vs 31 minutes above CRITICAL, final pair of runs); the effect rests on a diversion we assumed, not measured (on screen: routes into Senado made 30% less attractive for 20 minutes), and there was no live early warning;
- 24 of 40 simulated wheelchair users had no step-free route;
- the real-data test is announced before its result.

**Close.** Back to Ah Po, with Senado still red, then a relay tagline from the team.

**How it maps to the judging criteria:**

| criterion | how the video earns it |
|---|---|
| Feasibility | Visible before any claim is made. |
| Innovation | Framed as a gap next to a credited existing system. |
| Scientific rigour | Baselines, a positive control, a pre-announced real-data test and a public correction. |
| Responsible AI (the challenge brief) | Concrete: privacy enforced in code, a confidence gate, human approval, accessibility and three languages. Strangers' faces are pixelated on screen too. |
| Interdisciplinarity / best STEMB integration | Each speaker's discipline is lit on screen, and an accessibility thread links Medicine and Engineering. |
| Social impact (Macau) | Specific to Macau: its places, its languages, its reduced-mobility visitors. |
| Teamwork | Shown through balanced speaking time (77-121 written words per member), an on-camera correction by two members (both on camera for both lines, S12) and a relay close. |

---

## 2. Structure

| # | section (chapter card, top-left, 2 s) | time | shots | purpose | criteria |
|---|---|---|---|---|---|
| 1 | Hook: Ah Po (no card) | 0:00-0:11.5 | S01 | Human stakes in Macau, reduced mobility, why ground staff cannot see what is building. Labelled illustrative. | Creativity, social impact (Macau), presentation, Medicine |
| 2 | Cold open: it works (no card) | 0:11.5-0:37.5 | S02-S04 | Real software runs the full loop: phone, numbers only, CRITICAL forecast with confidence and reasons, stair-free detour, zh/en/pt notice, APPROVE needs a person (click scripted in this recording, footer says so), audit log. | Feasibility, innovation, Responsible AI, presentation |
| 3 | Team + title | 0:37.5-0:46.0 | S05 | One-word STEMB roll call with props; research question on the title card, held 2 s in silence. | Teamwork, interdisciplinarity |
| 4 | Why does it matter? | 0:46.0-0:58.0 | S06 | The proposal's premise, plus a cited medical mechanism. | Real-world impact, Medicine |
| 5 | What is new? | 0:58.0-1:11.0 | S07 | Credits the 2019 tourism-office forecasts; claims only the 5-15 min, street-level gap; shows how the system works. | Innovation, Business |
| 6 | Can it be trusted? | 1:11.0-1:28.0 | S08-S09 | Privacy enforced in code, recorded live (202 / 422 / 403); confidence gate and human review. | Responsible AI, rigour, Engineering |
| 7 | Does it work? | 1:28.0-2:40.0 | S10-S13 | Synthetic forecasting against a baseline; the gate checked against accuracy; real footage; the public correction; the 2,000-frame benchmark and calibration as a lead. | Scientific rigour, honesty, teamwork, Science, Technology |
| 8 | Does acting help? | 2:40.0-3:21.5 | S14-S15 | Recorded simulation with three spoken limits; SketchFuture accessibility check with a finding against ourselves. | Impact with honest limits, Engineering × Medicine |
| 9 | What's next? | 3:21.5-3:38.5 | S16 | Melbourne real-data test, announced before its result. | Rigour, feasibility |
| 10 | Can it happen? | 3:38.5-3:56.5 | S17 | Movable kit vs fixed cameras, sourced cost, runs end to end in simulation, 104 tests, licence, roadmap. | Feasibility, Business |
| 11 | Close | 3:56.5-4:19.5 | S18-S20 | Ah Po callback (Senado stays red), relay tagline, credits (end card held 6 s). | Social impact, teamwork, presentation |

The evidence block S10-S16 runs from 1:28 to 3:38.5: 130.5 s, about 50% of the runtime.

### Team roles (suggested; names unknown)

| member | discipline | owns in the project (suggested) | speaks in | written words: 5 members / 4 members |
|---|---|---|---|---|
| [MEMBER 1] | **T** Technology | iOS sensor app, on-device YOLO11n detection, video and Mall benchmarks, the frame-timing fix | S02, S11, S12, S13, S19 | 121 / 121 |
| [MEMBER 2] | **S** Science | simulator, forecasting vs persistence baseline, confidence-gating statistics, Melbourne test | S10, S12, S16, S19 | 77 + 15-word slot / 99 + 15 |
| [MEMBER 3] | **E** Engineering | backend, privacy enforcement, confidence pipeline, dashboard, end-to-end simulation run | S04, S08, S09, S14, S19 | 102 / 138 + 10 |
| [MEMBER 4] | **M** Medicine (health and accessibility) | crowd-injury mechanism (cited), reduced-mobility needs, stair penalty, SketchFuture walker / wheelchair / stroller profiles, the Ah Po story | S01, S06, S15, S18 | 98 + 12 / 126 + 12 |
| [MEMBER 5] (optional) | **B** Business | gap vs existing systems, product demo, deployment model, cost, licence, pilot | S03, S07, S17, S19 | 86 + 10 / – |

- **Roll call:** ALL speak 9 words (one word each, then "We are CrowdPulse Macau" together).
- **Four-member team:**
  - S03 goes to [MEMBER 2].
  - S07 goes to [MEMBER 4].
  - S17 and the S19 "Next" line go to [MEMBER 3].
  - In S05, [MEMBER 3] says "Engineering and business."
  - The team still spans all five STEMB disciplines.
- **Lower-thirds:** a S T E M B strip in every lower-third lights the speaker's letter. The lower-third slot carries only the speaker's name and strip; shot context lines go in the badge sub-line or the footer.

---

## 3. Shot-by-shot storyboard

**Production key:**
- **MG:** motion graphics (Python/Pillow frames encoded by ffmpeg).
- **UI:** screen capture of the running dashboard or SketchFuture.
- **iOS:** iPhone Simulator capture.
- **TERM:** live terminal recording.
- **FIG:** an existing repo figure animated with ffmpeg zoompan or masks.
- **CAM:** filmed by the team.

Status badges sit top-right (with an optional one-line sub-line under the pill), chapter cards top-left, the evidence legend in a thin strip at bottom-right (S10-S16), source footers bottom-left (slot table in section 6). In the evidence shots (S10-S15) the on-screen column lists only the required lines: the spoken number and its status. Secondary figures stay off screen (section 6, "On-screen text load").

| shot | time | speaker | narration (verbatim) | visual | on-screen text | how produced |
|---|---|---|---|---|---|---|
| S01 | 0:00.0-0:11.5 | [MEMBER 4] (VO) | This is Ah Po, going to see the Ruins of St. Paul's. From her wheelchair, she sees only backs, not the crowd building ahead. | Beats follow the words (140 wpm, voice from 1 s; re-key each move to the word timestamps of the real take):<br>0-1 s: kinetic title on navy.<br>1-6 s ("This is Ah Po, going to see the Ruins of St. Paul's"): top-down schematic of the 7 zones and 7 street links, with the St. Paul's steps hatched. Ah Po's wheelchair icon, with a small "Ah Po" tag, moves north from Almeida Ribeiro towards a pin at Company of Jesus Square (the square below the Ruins); the labels appear. Senado's disc is amber.<br>6-9 s ("From her wheelchair, she sees only backs"): the camera drops to her seated eye height: her wheelchair's armrest in the foreground, a wall of grey silhouettes swaying ahead.<br>9-11.5 s ("not the crowd building ahead"): crane back up to the map; Senado's disc goes amber to red.<br>Senado's colour is driven by the recorded true_density across the two map beats; the dots are illustrative. If cut 2 is applied, the crane-up runs silent in the shot's last ≈0.5 s. | "Macau · Golden Week"<br>Small: "Illustrative story. The people are fictional; the map is a schematic of our zone model; Senado's colour follows our recorded simulation."<br>Labels: 大三巴牌坊 Ruins of St. Paul's · 議事亭前地 Senado Square · 新馬路 Av. de Almeida Ribeiro<br>Pin: "view of the Ruins from the square below"<br>Tag on her icon: "Ah Po"<br>Badge: ILLUSTRATION | MG from shared/zones.json (lat/lon, edges, has_stairs) and experiments/results/simulation_run/A_timeline.csv (senado_square true_density, 13:53-14:09). Never put Ah Po on the steps. |
| S02 | 0:11.5-0:18.5 | [MEMBER 1] (VO) | Our phone app counts people on the device. It never sends a picture, only numbers. | The CrowdPulse Sensor app (Video mode and YOLO11n set on Setup, Start pressed on the Live tab) on the CC0 Yonge & Dundas clip: green boxes, ticking counters, gentle push-in. Recognisable near-field faces pixelated in post (boxes stay visible).<br>On "It never sends a picture" (≈14.9-17.0 s at 140 wpm from 11.5 s): the numbers peel into a payload card that slides to a server icon. On "only numbers" (≈17.0-17.9 s): a photo icon tries to follow and bounces off a shield, and "HTTP 403" lands; hold to the cut at 18.5 s. Key all three animations to the word timestamps of the real take. If the 403 cannot hold for at least 1 s, move 0.5 s from S04 to S02 (S02 0:11.5-0:19.0, S03 0:19.0-0:29.0, S04 0:29.0-0:37.5) and update this storyboard, the structure table and the JSON together. | Badge: LIVE SOFTWARE · TEST CLIP<br>"iOS app running in the iPhone Simulator on a Mac · YOLO11n on the device · public-domain (CC0) street clip, Toronto, not Macau"<br>Payload card with the real key names (values from your own Debug-tab capture), e.g. "person_count 11 · estimated_density 0.27 · flow_direction_deg 116 · vision_confidence 0.91 · latitude / longitude · heading_deg"<br>"sensor_id = a random node label for a temporary sensing position, not a person or a device serial"<br>Shield: "image upload → HTTP 403" | iOS: `xcrun simctl io booted recordVideo --codec=h264 S02_sim.mp4`, recorded during the C2 run, with the app posting to the C2 backend on :8000 (section 6, ios_capture, "Which backend"). Fallback: simulation_run/ios_app_video_mode_30s.mp4. MG overlay. Face pixelation per section 6. |
| S03 | 0:18.5-0:28.5 | [MEMBER 5] (VO) | On our dashboard, with a simulated Golden Week crowd, Senado Square's forecast turns critical, with a confidence score and the reasons why. | 1 s on the Live map (OSM tiles, Senado amber: WARNING at ≈14:08). The pointer clicks the Senado marker (the sidebar fills), then "open zone detail →": Zone detail at SIM CLOCK ≈14:08-14:10.<br>The density line crosses the dashed CRITICAL line, and the +5/+10/+15 rows turn CRITICAL (Senado turns red here, not on the map): first flagged LOW CONFIDENCE, then a confident row only if the capture shows one (a jump cut inside Zone detail is allowed). Cut on whatever the capture actually shows; never stage or composite rows or colours.<br>A highlight box traces the "WHY (+15 MIN → CRITICAL)" bullets. | Badge: LIVE SOFTWARE · SIMULATED CROWD<br>Badge sub-line: "Simulated Golden Week afternoon · SIM CLOCK, 10× speed"<br>Lower-third: "[MEMBER 5] · B · Business", B lit (four-member team: [MEMBER 2], S lit)<br>Callouts: +5 / +10 / +15 min · confidence · why<br>Footer: "Map © OpenStreetMap contributors" | UI, capture C2a (see section 6 for the marker steps). Fallback: A05_zone_senado_critical_forecast.png with zoompan. |
| S04 | 0:28.5-0:37.5 | [MEMBER 3] (VO) | It recommends a stair-free detour, with notices in Chinese, English and Portuguese. A person decides: approved, and logged. | Newest "Redirect part of … flow around Senado Square" card.<br>Zoom 1: the route line ("no stairs") and the green ♿ line ("Chosen route avoids stairs and steep sections … staff escort on the main route").<br>Zoom 2: expand "Public notice (中文 / English / Português)".<br>Click VIEW EVIDENCE (the zoom stays above the panel's "Assumed effect:" line unless that note is corrected first, 5A item 7), then APPROVE at ≈0:35; the capture's visible pointer stands for the click (no hand insert), and the footer says the click is scripted. Cut to the audit log row at ≈0:36.5. | Badge: LIVE SOFTWARE · SIMULATED CROWD<br>Callouts: "accessibility check: this route avoids stairs" · "中文 · English · Português" · "needs a person's approval" · "audit log"<br>Glossed excerpts: zh "議事亭前地目前非常擁擠…" (Senado Square is very crowded…) · pt "Largo do Senado: grande afluência de visitantes…"<br>Footer (small, from the APPROVE click to the end of the shot): "click scripted for this recording · the approval runs the real code path" | UI, capture C2b. Fallback: A07_intervention_evidence.png (cropped above its old "Assumed effect:" line, section 6) and A08_after_approval_audit.png; prefer the live capture. If the captured card says "includes stairs", narrate "a detour scored to avoid stairs". A hand insert is allowed only with a member's real click (macOS screen-recording take, section 5D). |
| S05 | 0:37.5-0:46.0 | ALL, on camera | [M1] Technology. [M2] Science. [M3] Engineering. [M4] Medicine. [M5] Business. [ALL] We are CrowdPulse Macau. | Five ≈0.8 s head-and-shoulders cuts, identical framing, hard cuts on the beat. Each member holds a prop from their own work:<br>- [M1] a phone on a clamp: the app on its screen (Setup tab, no street clip) only if the app was really installed on that phone (docs/testing.md §6.1, Xcode signing with an Apple ID); otherwise the screen is off. Nothing in the shot suggests a field run;<br>- [M2] printed F1 chart;<br>- [M3] laptop with the server log;<br>- [M4] printed step-free route map;<br>- [M5] blank cost panel or AGPL / deployment diagram (no figures).<br>Then a group shot (≈2.5 s, "We are CrowdPulse Macau"); the zone graph collapses into the wordmark.<br>Then a 2 s silent hold on the title card, so the research question can be read (it appears with the wordmark and stays ≈4 s in all). | Lower-thirds: "[MEMBER n] · S/T/E/M/B · role", with the STEMB strip.<br>Title: "CrowdPulse Macau"<br>Sub: "Our question: can ordinary phones, sending only numbers, help forecast crowds without identifying anyone?"<br>"Responsible AI · Challenge 2(c)" | CAM (phone on tripod) + MG title. Deliberate visual beat (9 words in 8.5 s, including the 2 s silent title hold). |
| S06 | 0:46.0-0:58.0 | [MEMBER 4] (on camera 0-4 s, then VO) | Every Golden Week, the Ruins of St. Paul's and Senado Square become dangerously crowded. [TEAM TO RESEARCH - MEDICINE: one sentence, at most 12 words, from a cited peer-reviewed source, on how a crowd crush injures the body] | Medium shot of M4. Then the zone schematic, with dots piling up at Senado (illustration). During the medical sentence: a simple body-outline diagram from shapes, annotated only with the sourced mechanism. Nothing graphic. | Card: "Why does it matter?"<br>Badge (from 4 s, over the schematic and the body diagram): ILLUSTRATION<br>Footer: "[TEAM TO RESEARCH: cited source for Golden Week crowding at the Ruins / Senado Square]"<br>Citation: "[TEAM TO RESEARCH: medical source, year]" | CAM + MG |
| S07 | 0:58.0-1:11.0 | [MEMBER 5] (VO) | In 2019, Macau's tourism office announced attraction forecasts, hours to days ahead. We forecast the next five to fifteen minutes, street by street, from phones staff place temporarily. | A log-scale time axis: grey ticks "4 h · 24 h · 7 days" light up above 20 attraction pins.<br>The camera dives into the first sliver of the axis, which becomes "+5 · +10 · +15 min" over the 7-zone graph.<br>Phone icons drop onto corners; number packets flow to a server; each zone gets three forecast chips. | Card: "What is new?"<br>"Announced 2019: 20 attractions, 4 h / 24 h / 7 days ahead · still running today? Not confirmed."<br>Footer: "Macao SAR Government news, 30 Apr 2019, gov.mo/en/?p=111714"<br>"CrowdPulse: next 5-15 min · street by street · temporary phones · privacy by design" | MG. Tight (guide fills 13.0 of 13.0 s): overrun → cut 4. |
| S08 | 1:11.0-1:20.0 | [MEMBER 3] (VO) | Privacy is enforced in code. A numbers-only reading: accepted. Add a face-ID field: rejected. Upload an image: refused. | Live terminal (≥28 pt, dark) against a separate fresh backend:<br>(1) valid observation → 202;<br>(2) the same JSON + `"face_id":"abc"` → 422;<br>(3) multipart JPEG → 403 with "PRIVACY_MODE: media uploads are not accepted. Send numerical metadata only."<br>Each code stamps on as it is spoken. | Card: "Can it be trusted?"<br>Badge: "LIVE SOFTWARE · recorded live" (cyan)<br>"202 accepted · numbers only" / "422 rejected · extra field face_id (closed schema)" / "403 refused · image upload (PRIVACY_MODE on by default)"<br>Footer: "same checks in backend/tests/test_api.py" | TERM, recorded live: a real shell session captured byte for byte with its timing and drawn frame by frame, never retyped (section 6). Deliberate visual beat (18 words in 9.0 s; guide 8.75 s). 0.5 s of stamp hold is already given back; cut 1 can take up to 0.5 s more if the real take allows. |
| S09 | 1:20.0-1:28.0 | [MEMBER 3] (VO) | Confidence is discounted for unreliable sensors and unusual conditions. Below sixty percent, a person must review it. | The equation builds term by term, and a gauge needle drops under 0.60.<br>Cut to real dashboard rows with "LOW CONFIDENCE — HUMAN REVIEW REQUIRED" and the footer "model confidence …% × reliability factor → effective …%".<br>Then the "Decided / expired" list with "Increase monitoring" and "superseded" tags. | "effective confidence = model probability × sensor-reliability factor × unusual-data (OOD) factor"<br>"Below 0.60 → LOW CONFIDENCE — HUMAN REVIEW REQUIRED · only 'increase monitoring' is recommended"<br>"Stronger recommendations replace weaker pending ones"<br>Footer: "sensor-reliability factor = 0.4 + 0.6 × reliability (backend/app/services/prediction.py) · threshold in shared/config.json" | MG + UI crops from C2a (zone detail) and C2b (Decided / expired list). Fallback: A05 and A07 screenshots (A07 cropped to its Decided / expired list, never showing its old "Assumed effect:" line). |
| S10 | 1:28.0-1:50.0 | [MEMBER 2] (VO) | On held-out simulated days, fifteen-minute forecasts score an F1 of 0.865, against 0.795 for assuming nothing changes, and catch 91 percent of critical minutes, against 79. Forecasts flagged as uncertain are right only about 56 percent of the time; the rest, 97. | 0-1.5 s: the evidence legend. Five badges appear centre-screen, then shrink into a thin strip at bottom-right, above the footer row, and stay there through S16. The narration starts at about 1.0 s, over the docking legend.<br>Grouped macro-F1 bars, model vs "no change": +5 min 0.887 vs 0.849, +10 min 0.876 vs 0.827, +15 min 0.865 vs 0.795, the +15 pair highlighted. No gap labels: the bars and their 3-decimal values carry the point.<br>Then "91% vs 79%". Then flagged vs the rest. | Card: "Does it work? Every result is labelled."<br>Badge: SIMULATED (pinned)<br>Axis: "macro-F1 (0-1): how well SAFE, WARNING and CRITICAL are all predicted"<br>Bar legend: "model" / "no change: the level stays as it is now"<br>Big numbers: "91% vs 79% of critical minutes caught (+15 min)"<br>Bars: "flagged as uncertain: right 56% · the rest: 97% (+15 min)"<br>Footer: "ml/models/metrics.json · 14 simulated days, split by day: 9 train / 2 validate / 3 test"<br>Kept off screen (Q&A, 5F): recall 0.908 vs 0.792 at 3 decimals; flagged share and accuracy across horizons; the stress day. | MG from ml/models/metrics.json at 3 decimals. If gap labels are ever restored, use +3.7 / +4.9 / +7.0 with the footnote "gaps from unrounded values, ml/models/metrics.json", never gaps worked out from the rounded bars. Do not use model_comparison.png: it has 2 decimals and four models. |
| S11 | 1:50.0-2:08.0 | [MEMBER 1] (VO) | On eleven frames of a public-domain street clip, the open YOLO model in our app counted 97 percent as many nearby people as a careful hand count; Apple's detector, 55. In the densest frames, 82; across the whole scene, only 27. | 0-8 s: detector_overlay.png split into its two panels (the same CC0 frame with Apple's, then YOLO11n's boxes). Recognisable faces mosaicked in Pillow before any zoom, boxes left visible. Each panel fitted to 16:9 on navy (no stretching), slow push-in, wipe from Apple to YOLO11n at ≈3.5 s.<br>8-18 s: three bar pairs titled "count vs hand count", Apple → YOLO11n: within ≈20 m 55% → 97%; densest frames 61% → 82%; whole wide scene 9% → 27%. | Badge: "REAL DATA · 11 hand-counted frames · indicative, not a benchmark"<br>Panel labels: "Apple's built-in detector" / "YOLO11n (Ultralytics), open model on the device"<br>Bar title: "count vs hand count = detector count ÷ hand count, summed over the frames in each group (not the share of individuals detected)"<br>Small, under the densest pair: "2 frames with ≥10 nearby people"<br>"nearby = within ~20 m · YOLO11n error 1.5 people per frame"<br>Credit: "'Diagonal crosswalk at Yonge & Dundas in Toronto', Raysonho, Wikimedia Commons, CC0 · faces pixelated by us"<br>Footer: experiments/results/video/summary.md | FIG (per-panel crop, mosaic, pad, zoompan, xfade; commands in section 6) + MG bars. Tight (41 words in 18.0 s, 0.98 at 140 wpm; guide 17.0 s): overrun → cut 3. Say "as we did by hand" (same 5 words) only if a team member really made the 11 hand counts (5E, 5F). |
| S12 | 2:08.0-2:18.0 | [MEMBER 1] then [MEMBER 2], on camera together | [M1] Our first version of this test had a frame-timing bug. [M2] It was caught, fixed, and we published the correction. | 0-8 s: the two members at a laptop showing the mosaicked S11 panel stills (never the raw clip), framed in the left half of the picture. Both stay on camera for both lines (at 140 wpm M1 speaks ≈0-4.3 s, M2 ≈4.6-8.5 s), so each is seen saying their line.<br>≈1.5-8 s, split screen: the timing MG as a Pillow inset in the right half, in three quick beats: a hand-count label at time t; the frame actually compared (sampled 2.4 s after the label) shown in red, then the correct frame aligned in green; then the dashed far-kerb line drops in (no extra tag).<br>8-10 s: the README "Correction" paragraph, rendered and captured (section 6, "S12 README insert"), with a highlight box drawn in post (it carries the full wording). Cut to it on M2's word "correction"; re-key the cut to the real take. | Badge: CORRECTED<br>Overlay (≈12 words, under the inset): "v1 compared hand counts with frames 2.4 s off → fixed; near field redefined, recounted"<br>Footer: "README.md · Correction" | CAM (members filmed in the left half, 5D) + MG inset + README insert (README.md rendered with pandoc and recorded with capture.py; fallback: a Pillow-typeset excerpt labelled "README.md · Correction (excerpt)"; section 6). Label any hand-counting "re-enacted" if filmed now. M2's line as written is true whoever spotted the bug. Only if a team member really spotted it (5E, 5F) may M2 say instead "We found it, fixed it, and published the correction." (also 9 words). Never "ourselves" otherwise. |
| S13 | 2:18.0-2:40.0 | [MEMBER 1] (VO) | Eleven frames is small, so we tested two thousand annotated mall frames. The detector counted only 59 percent, but 93 percent of its boxes were people: a steady under-count. Twenty labelled frames calibrated that one camera, cutting error from thirteen to about three people per frame. A lead, not proof. | mall_count_scatter.png (a chart only, placed at up to 1.5× on a light card; the orange Apple cloud dimmed with a Pillow mask and the blue cloud labelled "YOLO11n, the app default"): the YOLO11n point cloud sits below the dashed "perfect count" line.<br>Near / middle / far bars: 78 / 64 / 42%, titled "recall: share of people detected".<br>A schematic "true ≈ a × detected + b", then a counter "13.4 → 3.3 people per frame" with a "20 labelled frames" tag. | Badge: "REAL DATA · Mall research benchmark · charts only"<br>"count vs annotated count: 59% · 93% of boxes are people"<br>Bar title: "recall: share of people detected · near / middle / far"<br>"Calibration: post-hoc · one camera · held-out frames 801-2000 · not yet in the app"<br>Footer: "experiments/results/mall/summary.md · Mall dataset: Chen, Loy, Gong & Xiang, BMVC 2012"<br>Kept off screen (Q&A, 5F): 13-53 people per frame; count correlation 0.80; overall recall 55%; ≈6-8 ms per frame on a Mac. | FIG + MG. **Never any Mall imagery.** Tight (50 words in 22.0 s, 0.97 at 140 wpm): overrun → cut 5. |
| S14 | 2:40.0-3:00.5 | [MEMBER 3] (VO) | In a recorded simulation, approving the redirect left Senado less crowded by the end than doing nothing, but only modestly: it stayed critical. The effect rests on a diversion we assumed, not measured, and the crowd built so fast the alert came with it, not before. | Line chart from the A and B timelines (Senado true density, 13:53-14:40): blue = approved, orange = no action, dotted CRITICAL line at 0.70. Both cross it ≈14:08-14:09 and never drop back below.<br>Markers, all from run A and labelled "run A": first CRITICAL forecast (14:08:30, 21 s after the true crossing at 14:08:09), redirect recommended (14:09:08), "approval (scripted operator), 14:14". A light band marks the assumed effect window, 14:14-14:34; the 14:40 end values come after it.<br>End labels: "this pair 0.75 vs 0.82"; faint "earlier pair 0.73 vs 0.87".<br>One chip slides in as the assumed effect is spoken. "It stayed critical" has no chip: the narration, the end labels and the CRITICAL line carry it.<br>From the third limit ("and the crowd built so fast…", ≈14 s at 140 wpm; key to the real take) to the end: a clock panel slides in beside the chart (the chart stays visible): crowd build-up ≈3 min vs a 5-15 min forecast horizon, with its label.<br>Senado never turns green. | Card: "Does acting help?"<br>Badge: "SIMULATED · recorded end-to-end run, 29 Sep 2026" (amber)<br>Under the chart: "At 14:40 · approved 0.75 vs no action 0.82 (earlier pair 0.73 vs 0.87) · this pair: 32 vs 31 min above CRITICAL"<br>Axis: "relative density index, not people per m²"<br>Chip: "Assumed: routes into Senado made 30% less attractive for 20 min (prototype setting, not measured)"<br>Clock panel: "crowd build-up ≈3 min" / "forecast horizon 5-15 min"; label: "First CRITICAL forecast within ~1 min of the crossing: no early warning · 5-15 min skill shown offline, on simulated days only"<br>Footer: experiments/results/simulation_run/README.md | MG from A_timeline.csv / B_timeline.csv / A_events.json. Fallback: FIG simulation_run_timeline.png, top panel. The forecast marker must be run A's: run B's first CRITICAL forecast (48%, flagged for review) came 74 s before its crossing (5F). Tight (46 words in 20.5 s, 0.96 at 140 wpm): overrun → cut 6. The run A marker reads "approval (scripted operator)": the recorded runs' operator was a script driving the dashboard (simulation_run/README.md), so never label it as a person. |
| S15 | 3:00.5-3:21.5 | [MEMBER 4] (VO) | One click tests another recommendation, at St. Dominic's, on our model of Macau's streets: walkers lose seventeen seconds, wheelchair users thirty. And 24 of our 40 simulated wheelchair users had no step-free route either way. Real barrier, or missing map data? Only a street survey can tell. | The card titled "Redirect part of southbound flow around St. Dominic's Square" (title visible; do not zoom on its route text). Click TEST IN SKETCHFUTURE. Unless the box's caveat is corrected first (5A item 7), frame the title, then the button, with the crop's bottom edge just under the button row, so the grey "Model check, not evidence: … assumed 30% diversion" line below it cannot be read.<br>SketchFuture opens (Traditional Chinese UI) with the plan "CrowdPulse #…：封閉大三巴街↔板樟堂前地通道" and the closed segments red on the OSM street map.<br>Comparison cards appear for 一般行人 (walkers), 輪椅使用者 (wheelchair users) and 推嬰兒車者 (stroller users).<br>Counters tick to +17 / +30 / +21 s, and 24 of 40 dots turn grey. | Badge: "MODEL CHECK · synthetic cohort"<br>Counter header: "same 120 simulated people, with vs without the closure"<br>"walkers +17 s · wheelchair users +30 s · stroller users +21 s"<br>Small, under the counters: "averages over those who arrive in both plans: walkers 40/40 · wheelchair users 16/40 · stroller users 28/40"<br>Dot grid: "24 of 40 wheelchair users: no step-free route in EITHER plan · missing map detail or real barriers? Needs a site survey."<br>Footer: "Map © OpenStreetMap contributors, ODbL · example run #721, sketchfuture/VERIFICATION.md"<br>Kept off screen (Q&A, 5F): 575 nodes / 692 segments; "full closure = worst case of a partial redirect". | UI (dashboard + SketchFuture on :4173), capture C2b, or C2c if C2b cannot reach the card before it expires (section 6, "Timing"), + MG overlays. Narrate and caption the captured numbers if they differ from #721. The old 30% caveat must never be readable (section 6, "Rules while recording"). |
| S16 | 3:21.5-3:38.5 | [MEMBER 2] (VO) | Because our forecasting results are simulated, we're testing them on real counts from 99 Melbourne street sensors: a test announced before its result. [RESULT PENDING - fill after analysis, report honestly whatever it shows] | Dots at the lat/lon of only the location_ids present in the minute archive (99 on 12 Oct; not all 134 rows of sensors.csv), no basemap, each pulsing with its real archived counts. A calendar strip fills from 12 Oct.<br>Then the result panel: a PENDING stamp until the analysis exists, then a two-bar chart (model vs "no change", +15 min, Melbourne held-out days) showing whatever was found. | Card: "What's next?"<br>Badge: PENDING (switch to REAL DATA only after the analysis)<br>"City of Melbourne pedestrian counts · per minute · 99 sensors · CC BY · archived hourly since 12 Oct 2026"<br>"Not Macau: counts people crossing a line, not camera density. Tests the method, not accuracy in Macau."<br>**Only if committed before the analysis:** "Count → SAFE / WARNING / CRITICAL mapping fixed on [DATE], before any result · experiments/datasets/melbourne/README.md (commit [HASH])". Otherwise delete this line.<br>"[RESULT PENDING - fill after analysis, report honestly whatever it shows]" | MG from experiments/datasets/melbourne/ (read-only). Result chart added after the analysis (≈22 Oct). |
| S17 | 3:38.5-3:56.5 | [MEMBER 5] (VO over B-roll) | Phones on temporary mounts can serve one festival, then move to the next. [TEAM TO RESEARCH - BUSINESS: at most 10 words, sources on screen: cost of a phone kit vs a fixed counting camera] The whole chain runs end to end in simulation, with 104 automated tests passing. | A phone-on-clamp icon hops between festival dates while a pole camera stays bolted in place.<br>Cost panel, empty until sourced.<br>3 s team B-roll: `.venv/bin/python -m pytest -q` showing "49 passed".<br>Counters 49 · 15 · 27 · 13 → 104, then a roadmap arrow. | Card: "Can it happen?"<br>Cost: "[TEAM TO RESEARCH: phone kit vs fixed counting camera, with sources]"<br>"Intended operators: event staff, tourism or police operations rooms (no partner yet)"<br>"Python 49 · dashboard 15 · SketchFuture 27 · iOS 13 = 104 automated tests · a fresh clone runs from the README"<br>"Open source, AGPL-3.0; a closed-source or App Store build needs an Ultralytics licence or another detector"<br>Roadmap: "Prototype (end to end in simulation) → Melbourne real-data check → school counting experiment (protocol written) → supervised street pilot" | MG + CAM B-roll |
| S18 | 3:56.5-4:02.5 | [MEMBER 4] (VO) | Back to Ah Po: her main route stays open, with staff beside her. | Same map and framing as S01. An APPROVED stamp lands. A staff icon (hi-vis vest) joins Ah Po on the main route north. Grey walkers take the dashed step-free detour from the approved card (run A: Rua dos Ervanários → Rua da Tercena → Rua de S. Paulo lower). A small zh/en/pt notice flashes. **Senado stays red (CRITICAL; run A ended at 0.75), its colour driven from A_timeline.csv as in S01.** | "Illustrative story"<br>"Every redirect recommendation includes keeping the main route open, with staff, for reduced-mobility visitors" | MG (S01 assets) |
| S19 | 4:02.5-4:13.5 | [MEMBER 5], [MEMBER 3], [MEMBER 2], [MEMBER 1], on camera relay | [M5] Next: a supervised street pilot in Macau, with permission. [M3] The AI recommends. [M2] A person decides. [M1] Nothing identifying leaves the phone. | Wide shot of the whole team in the S05 set, each speaker in turn, M4 in frame, then all together (last ≈1 s). Allow ≈0.3-0.5 s for each of the three hand-offs. | "Next: supervised street pilot, only with permission from [TEAM TO RESEARCH: the responsible Macau authority]"<br>"The AI recommends. A person decides." | CAM + MG text. 20 words + 3 hand-offs + 1 s together in 11.0 s (guide 9.4 s without hand-offs). |
| S20 | 4:13.5-4:19.5 | none | (none) | End card on navy, held 6 s so the grid and credits can be read: wordmark, full STEMB strip, who-built-what grid, evidence legend, credits. | "CrowdPulse Macau · [SCHOOL] · Supervisor: [NAME] · Imperial College London Hackathon Hong Kong & Macau 2026 · Challenge 2(c) Responsible AI"<br>"Who built what: [TEAM TO FILL]"<br>"Simulated = our simulator · Real = CC0 video, Mall benchmark · Model check = SketchFuture · Pending = Melbourne"<br>Credits: 'Diagonal crosswalk at Yonge & Dundas in Toronto', Raysonho @ Open Grid Scheduler / Grid Engine, Wikimedia Commons, CC0 · faces pixelated by us · Map data © OpenStreetMap contributors, ODbL · Pedestrian counts © City of Melbourne, CC BY · Mall dataset: Chen, Loy, Gong & Xiang, BMVC 2012 (charts only) · YOLO11 © Ultralytics, AGPL-3.0 · CrowdPulse code AGPL-3.0 · fonts: Geist, Noto Sans TC (SIL OFL)<br>[optional: AI-assistance line per the organisers' reply] | MG |

**Shots by production method:**
- MG-led: S01, S06, S07, S09, S10, S14, S16, S17, S18, S20, plus all overlays.
- UI: S03, S04, S15, plus the 2 s README insert in S12.
- iOS: S02.
- TERM: S08 (a real terminal session, recorded byte for byte with its timing by `video/record_terminal.py` and drawn frame by frame; nothing retyped).
- FIG: S11, S13.
- CAM: S05, S06 opening, S12, S17 B-roll, S19.

---

## 4. Claims and sources (every spoken claim)

| shot | claim as spoken | status | source in the repo |
|---|---|---|---|
| S01 | Ah Po, a wheelchair user going to see the Ruins; the crowd building ahead | **Illustrative, labelled fictional.** Only Senado's colour is data. | Colour: experiments/results/simulation_run/A_timeline.csv (senado_square true_density). Destination step-free in the zone model: shared/zones.json (Senado → St. Dominic's → Rua de S. Paulo → Company of Jesus Square, all has_stairs false). |
| S02 | The app counts people on the device and never sends a picture, only numbers | Real code (shown in the Simulator) | docs/privacy.md (sensor_id: "a temporary sensing position, not a person or a device serial"; the iOS app generates it once per install); ios/CrowdPulseSensor (PersonDetector.swift, VisionProcessor.swift; payload keys in Sources/Models/SensorObservation.swift); backend/app/main.py (403 for media); backend/tests/test_api.py |
| S03 | Simulated Golden Week crowd; Senado's forecast turns critical with a confidence score and reasons | Live software, simulated crowd | README.md Demo section; simulation_run/A05_zone_senado_critical_forecast.png; A_timeline.csv (Senado WARNING at 14:07-14:08; 14:09:08: all three rows CRITICAL, +5 low-confidence at 0.516, +10 / +15 at 0.638 / 0.686); backend/app/services/engine.py (the map colours a zone by its current state or a confident forecast, whichever is worse, so Senado is amber on the map at ≈14:08); shared/config.json (horizons 5/10/15) |
| S04 | Stair-free detour; notices in Chinese, English, Portuguese; it needs a person's approval; it is logged | Real code | backend/app/services/intervention.py: notice templates (zh/en/pt); note "Chosen route avoids stairs and steep sections"; staff escort on the main route. Audit log in A07_intervention_evidence.png (card #5 "no stairs") and A08. shared/config.json stairs_penalty 0.5. In capture C2b the click is scripted (capture.py), and the footer says so; the approval step itself is the real code path. |
| S06 | "Every Golden Week, the Ruins of St. Paul's and Senado Square become dangerously crowded." | Proposal wording; **source still needed** | docs/proposal.md. [TEAM TO RESEARCH: cited source] |
| S06 | How a crowd crush injures the body | **Placeholder** | [TEAM TO RESEARCH: peer-reviewed medical source] |
| S07 | In 2019, Macau's tourism office announced attraction forecasts, hours to days ahead | Public record; whether it still runs is unconfirmed | docs/proposal.md source table → gov.mo/en/?p=111714 (20 attractions; 4 h, 24 h, 7 days) |
| S07 | We forecast the next 5-15 minutes, street by street, from phones staff place temporarily | Design (prototype) | shared/config.json forecast_horizons_min [5,10,15]; shared/zones.json; docs/deployment.md (operational model) |
| S08 | Numbers-only reading accepted; face-ID field rejected; image upload refused | Real, tested | backend/tests/test_api.py; docs/testing.md §5 (422, 403); backend/app/main.py ("PRIVACY_MODE: media uploads are not accepted…"); 202 for valid readings: simulation_run/README.md |
| S09 | Confidence discounted for unreliable sensors and unusual conditions; below 60% a person must review | Real code / config | backend/app/services/prediction.py line 146 (sensor-reliability factor = 0.4 + 0.6 × reliability; effective = model confidence × that factor × OOD multiplier); shared/config.json (low_confidence_threshold 0.6, ood_confidence_multiplier 0.7); dashboard/src/app/zones/[id]/page.tsx (model confidence × reliability factor → effective); dashboard/src/components/Badges.tsx |
| S10 | Held-out simulated days; +15 min F1 0.865 vs 0.795 for "nothing changes" | **Synthetic** | ml/models/metrics.json: per_horizon.h15 test f1_macro 0.8650 vs persistence 0.795; split_days 9 / 2 / 3 |
| S10 | Catch 91% of critical minutes, against 79 | **Synthetic** | ml/models/metrics.json h15 CRITICAL recall 0.908 vs persistence 0.792 (per zone-minute, 60 s bins: shared/config.json bin_seconds) |
| S10 | Flagged forecasts right about 56% of the time; the rest 97% | **Synthetic** | ml/models/metrics.json h15 confidence_gating: accuracy_flagged 0.565, accuracy_confident 0.969. All horizons: flagged 1.35-1.66%, right 0.557-0.571 vs 0.969-0.976. |
| S11 | 11 hand-counted frames of a public-domain clip; YOLO counted 97% as many nearby people as a careful hand count; Apple 55; densest frames 82; whole scene 27 (all count ratios). Says nothing about who counted. | **Real data, indicative** (one clip, 11 frames) | experiments/results/video/summary.md ("found" = sum of detector counts ÷ sum of hand counts, a count ratio that can exceed 100%, not the share of individuals detected; near 97% vs 55%; whole-frame 27%, both over all 11 frames; dense 82% over only the 2 frames with ≥10 nearby people, experiments/video_eval.py `dense = near_count >= 10`); hand counts: experiments/datasets/video/ground_truth.csv, committed only in 391da20 and 3abcd7a, both with an AI co-author line; the repo does not record who made the counts (5E, 5F); clip licence: THIRD_PARTY_NOTICES.md (CC0) |
| S12 | First version had a frame-timing bug; it was caught, fixed, and the correction published ("we found it" only if a team member did) | Real | README.md "Correction" paragraph (hand counts attached to the wrong video times: ffmpeg's sampler took the frame 2.4 s after the label; the near-field definition was not one the detectors could be scored against; now pixel-exact alignment and a stated geometric near-field rule; Apple's figures moved from 34% / 8% to the corrected 55% / 9%); docs/hackathon-notes.md ("hand counts attached to times 2.4 s early"); commit 3abcd7a ("near field redefined geometrically and recounted"). Who spotted the bug is not recorded in the repo. |
| S13 | 2,000 annotated mall frames; counted 59% (a count ratio, as in S11); 93% of boxes were people; 20 labelled frames cut error from 13 to about 3 per frame; one camera | **Real data, post-hoc, one camera** | experiments/results/mall/summary.md: count ratio 59%, true recall 55% (78% near / 64% middle / 42% far), precision 93%, held-out frames 801-2000, raw MAE 13.42 → 3.33 with 20 frames |
| S14 | Approving the redirect left Senado less crowded by the end than doing nothing, only modestly; it stayed critical; the effect rests on an assumed diversion, not measured; the alert came with the crowd | **Simulated** (two recorded pairs of runs) | experiments/results/simulation_run/README.md: 14:40 end values 0.75 vs 0.82, earlier pair 0.73 vs 0.87; 32 vs 31 min above CRITICAL in the final pair (time above CRITICAL not shortened; the README gives no minutes figure for the earlier pair, only that Senado stayed above CRITICAL in both); the run A operator was a script driving the dashboard (README "operator" row); on approval the simulator makes routes into Senado 30% less attractive for 20 minutes (14:14-14:34 in run A), so its inflow falls by less than 30%; "No early warning in this scenario": the first CRITICAL forecast came within about a minute of the true crossing, 21 s after it in run A (14:08:30 vs 14:08:09) and 74 s before it in run B (at 48% confidence, flagged for review); the first confident CRITICAL forecast came after the crossing in both runs (14:09:08 vs 14:08:09; 14:13:14 vs 14:09:20). Code: backend/app/services/engine.py (approval calls apply_redirect with 1 − inflow_reduction for 20 min); ml/synthetic/simulator.py (that multiplier scales the route-choice weight towards the zone); backend/app/services/intervention.py (assumed-effect note: the forecast what-if scales the zone's inflow by 0.70); shared/config.json assumed_redirect_inflow_reduction 0.3. A prototype setting, not measured. |
| S15 | One click tests another recommendation at St. Dominic's; walkers +17 s, wheelchair users +30 s | **Model check** | sketchfuture/VERIFICATION.md (run #721, "Redirect part of southbound flow around St. Dominic's Square"; averages over people who arrive in both plans: walkers 40/40, wheelchair users 16/40, stroller users 28/40); dashboard/src/components/SketchFutureCheck.tsx (its grey caveat still says "the assumed 30% diversion", lines 22 and 34: outdated wording, kept off screen or corrected first, 5A item 7) |
| S15 | 24 of our 40 simulated wheelchair users had no step-free route either way; cause unknown | **Model check, synthetic cohort** | sketchfuture/VERIFICATION.md ("24 have no step-free route … in either"); sketchfuture/MODEL.md (demand is synthetic; missing topology can make journeys model-unreachable; wheelchair maximum slope 5%, stairs excluded); README.md (575 nodes, 692 segments) |
| S16 | Forecasting results are simulated; testing on real counts from 99 Melbourne sensors; announced before its result | **Real data, analysis pending** | experiments/datasets/melbourne/README.md (the count-to-level mapping must still be stated before looking at results); 99 distinct location_ids in minute/2026-10-11 and 2026-10-12 (checked 12 Oct; sensors.csv lists 134); docs/proposal.md ("Next: testing forecasts on real pedestrian-sensor data"). On-screen mapping line only with the team's dated commit. |
| S16 | [RESULT PENDING] | **Pending** | To be filled from the team's analysis (≈22 Oct) |
| S17 | Phones on temporary mounts can serve one festival, then move to the next | Design intent, not field-tested | docs/deployment.md, "Operational model" section only (not its illustrative cost table) |
| S17 | Cost of a phone kit vs a fixed camera | **Placeholder** | [TEAM TO RESEARCH, with sources] |
| S17 | The whole chain runs end to end in simulation | Real (simulation) | experiments/results/simulation_run/README.md |
| S17 | 104 automated tests passing | Real | docs/testing.md (49 Python + 15 dashboard + 27 SketchFuture + 13 iOS) |
| S18 | Her main route stays open, with staff | Real code (recommendation content; staff carry it out if the operator approves) | backend/app/services/intervention.py ("Keep the main route open with staff for reduced-mobility visitors"; "staff escort on the main route is part of this recommendation"); A07 screenshot |
| S19 | Next: a supervised street pilot in Macau, with permission | Plan | docs/proposal.md ("then a street pilot"); [TEAM TO RESEARCH: authority] |
| S19 | The AI recommends. A person decides. | Real code | Interventions page ("The system recommends; you decide."); approve/reject audit log |
| S19 | Nothing identifying leaves the phone | Real code | docs/privacy.md; closed schema (extra="forbid"); sensor_id is a random node label for a temporary sensing position, not a person or a device serial (the iOS app generates it once per install) |

**Numbers shown on screen only:**

| figure | source |
|---|---|
| 0.887 / 0.876 / 0.865 vs 0.849 / 0.827 / 0.795 (no gap labels; if restored: +3.7 / +4.9 / +7.0 from the unrounded values); 9 / 2 / 3 days | ml/models/metrics.json |
| sensor-reliability factor 0.4 + 0.6 × reliability | backend/app/services/prediction.py line 146 |
| 1.5 people per frame; 61% / 9% (Apple); ~20 m; "count vs hand count" definition; densest = the 2 frames with ≥10 nearby people | video/summary.md; experiments/video_eval.py (`dense = near_count >= 10`); experiments/datasets/video/ground_truth.csv |
| 78 / 64 / 42% (recall); frames 801-2000 | mall/summary.md |
| 14:14 approval (scripted operator); 14:14-14:34 assumed effect window; crossings at 14:08 and 14:09; run A's first CRITICAL forecast 14:08:30, within ~1 min of the crossing; 32 vs 31 minutes above CRITICAL (final pair only); 30% less attractive for 20 min | simulation_run/README.md, A_timeline.csv / B_timeline.csv, A_events.json |
| 120 people; +21 s strollers; arrive in both plans 40/40, 16/40, 28/40 | VERIFICATION.md |
| 49 / 15 / 27 / 13 | docs/testing.md |
| Payload person_count 11 / estimated_density 0.27 / flow_direction_deg 116 / vision_confidence 0.91 | ios_app_debug_payload.png, or the team's own capture; key names from SensorObservation.swift |
| 2.4 s | README.md Correction |

**Kept off screen (secondary; prepared as Q&A answers in 5F, sources unchanged):** recall 0.908 vs 0.792; flagged 1.4-1.7% of forecasts, right 56-57% vs 97-98% across horizons; stress day F1 0.857 / 0.832 / 0.814 and unusual-data flags 11-12% vs 0.6-0.7% (ml/models/metrics.json) · 13-53 people per frame, count correlation 0.80, overall recall 55% (mall/summary.md) · YOLO11n 6-8 ms per frame on a Mac, 6.0 and 7.7 ms (mall/summary.md, video/summary.md) · 575 nodes / 692 segments (README.md).

---

## 5. For the team to do

### A. Fill before recording (never ship bracketed text)

1. **Names.** [MEMBER 1]..[MEMBER 5], [SCHOOL], the supervisor, and the who-built-what grid. List only what each person really did.
2. **S06 premise source** [TEAM TO RESEARCH]. A citable news report or government notice about Golden Week crowding or crowd-control measures at the Ruins or Senado Square, shown as a footer. The wording matches the submitted proposal, so keep it. If no source turns up, say "very crowded" in the video.
3. **S06 medical sentence** [TEAM TO RESEARCH]. At most 12 words, from a peer-reviewed medical or public-health source, with the citation on screen.
   - Research hint only, not a claim: search the literature for the crowd-crush injury mechanism ("compressive asphyxia").
   - No injury or death counts unless they are cited.
   - If it is not sourced by 21 Oct, delete the slot (about −5 s).
4. **S17 cost sentence** [TEAM TO RESEARCH]. At most 10 words: a phone kit against a fixed counting camera installation, with sources on screen.
   - Do not use docs/deployment.md's cost table: it is labelled illustrative assumptions.
   - If it cannot be sourced, delete the slot (about −4 s).
5. **S19 pilot authority** [TEAM TO RESEARCH]. Which Macau body would have to permit a supervised street pilot (on screen only).
6. **Optional.** Check whether the 2019 tourism-office visitor-flow app still runs. If you confirm it, replace "still running today? Not confirmed."
7. **Old 30% wording inside the dashboard: done.** Both strings were corrected in commit 8f3c8ca, with README.md line 106 and the dashboard test (the SketchFuture box now says "the extreme case of the assumed partial redirect"; the assumed-effect note is the single accurate sentence quoted below). Rebuild the dashboard before capturing. For the record, the two strings were:
   - S15: the SketchFuture box on the St. Dominic's card, directly under TEST IN SKETCHFUTURE, says "Model check, not evidence: a full closure is the extreme case of the assumed 30% diversion" (dashboard/src/components/SketchFutureCheck.tsx, lines 22 and 34).
   - S04: the VIEW EVIDENCE panel prints the raw assumed effect. Its note (backend/app/services/intervention.py line 144) opens "Assumed effect (configurable prototype assumption, not validated): 30% less inbound flow." The sentence after that clause is already correct: "The forecast what-if scales the zone's inflow by 0.70; the live simulation makes routes into the zone 30% less attractive for 20 min, so its inflow falls by less."
   - **Preferred fix (code, outside this script):** change line 22 so that line 34 reads "the extreme case of the assumed partial redirect" (the wording of the comment in dashboard/src/lib/sketchfuture.ts). In the line-144 note, delete only the clause "30% less inbound flow." so the note becomes one sentence: "Assumed effect (configurable prototype assumption, not validated): the forecast what-if scales the zone's inflow by 0.70; the live simulation makes routes into the zone 30% less attractive for 20 min, so its inflow falls by less." Do not add a new opening such as "routes into the zone 30% less attractive for 20 min" or "forecast what-if: inflow ×0.70": the note already says both, and the panel would print them twice. No test asserts this note. Update the assertion in dashboard/src/__tests__/sketchfuture.test.tsx (line 67), run all the tests (the total must stay 104), fix README.md line 106 in the same commit, then rebuild the dashboard.
   - **If the code is not changed:** neither line may be readable on screen. Frame them out as in section 6, "Rules while recording", and check every frame of the rehearsal capture.

### B. The Melbourne result slot (S16)

- Keep "[RESULT PENDING - fill after analysis, report honestly whatever it shows]" until the analysis is done (expected ≈22 Oct).
- **Before running the analysis:** write the count-to-level mapping (e.g. counts per minute relative to each sensor's own busy-hour level) into experiments/datasets/melbourne/README.md with its date, and commit it. The S16 mapping line cites that file, date and commit. If the mapping is not committed before the analysis, delete the mapping line and do not say "with the method fixed before we looked".
- Recount the distinct location_ids in the analysed window, and use that number in the voice, the caption and the dot map.
- **If finished:** change the first sentence to "Because our forecasting results are simulated, we tested them on real counts from [N] Melbourne street sensors, with the method fixed before we looked." (only with the dated commit; otherwise end at "sensors"). Then add at most 15 words: the +15 min macro-F1 of the model against "nothing changes", whichever is higher.
  - If the model does not beat the baseline, say so, plus one clause on what you will change.
  - Switch the badge to REAL DATA.
- **If not finished by 23 Oct:** fill the slot with "The analysis is still running; we will publish the result, whatever it shows." (13 words).
- The S19 "Next" line names only the street pilot, so it stays true either way.

### C. Voices: record your own

- Each member records only their own lines, as separate files (S02.wav …):
  - a phone voice memo, 15-20 cm from the mouth;
  - in a quiet, soft-furnished room;
  - 2-3 takes per line, standing, smiling slightly.
- Speak at about 140 wpm. Then replace the robot guide track with your takes and re-time each shot to the real voice.
- **Pronunciation guide:**

| written | say it as |
|---|---|
| F1 | "F one" |
| 0.865 / 0.795 | "point eight six five" / "point seven nine five" |
| 2019 | "twenty nineteen" |
| 104 | "a hundred and four" |
| St. | "Saint" |
| Senado | "se-NAH-doo" |
| YOLO | "YO-lo" |
| Ah Po (阿婆) | in Cantonese |

- Judges score teamwork, so no synthetic voice in the final cut.

### D. On-camera shots to film

All filmed in landscape, 1080p30, on a phone on a tripod, with the same plain background and window light.

| shot | what to film |
|---|---|
| S05 | Five identical head-and-shoulders shots, each member holding their prop, plus one group shot. [MEMBER 1]'s phone shows the app only if it was really installed on that phone (docs/testing.md §6.1); otherwise its screen is off. |
| S06 | 4 s of [MEMBER 4]. |
| S12 | [MEMBER 1] and [MEMBER 2] at a laptop showing the mosaicked S11 stills (never the raw clip), framed in the left half of the picture so the timing graphic can sit in the right half. Both say their lines in one take, on camera, about 10 s. |
| S17 | 3 s of a real `pytest` run. |
| S19 | The relay, as a wide shot. |
| S04 (optional, only with a real click) | Only if a member clicks APPROVE themselves in the macOS screen-recording take of the Senado card: a 1 s insert of that member's hand, filmed during that same click. Never cut a hand over the scripted C2 click. |

- Get everyone's consent to appear. The supervisor may appear, silent.
- Never show a prop with invented numbers.

### E. AI-assistance disclosure

The repository holds no record of the organisers' reply on AI tools (docs/ and the README searched). Before submitting:
- Re-read that reply, and follow it exactly.
- If disclosure is required or allowed, a one-line statement on the end card or in the submission form fits a Responsible AI entry. Adjust it to what is true, for example: "We used AI assistants for parts of the code, figures and script drafting; every number was checked by the team against our repository."
- The fix for the S12 timing bug (commit 3abcd7a) carries an AI co-author line, and the repo does not record who spotted the bug. Make sure the disclosure line covers it.
- The 11 video hand counts behind S11 (experiments/datasets/video/ground_truth.csv) were committed only in 391da20 and 3abcd7a, both with an AI co-author line, and the repo does not record who made them. S11 therefore says "as a careful hand count", which describes the method, not the person. If no team member made the counts, the disclosure line must cover them too (e.g. "… for parts of the code, the 11-frame video counts, figures and script drafting …"). Only if a team member really made them may S11 say "as we did by hand" (same 5 words); fill the 5F answer first.
- S12's M2 line is therefore written as "It was caught, fixed, and we published the correction.", which is true either way. Switch to "We found it, fixed it, and published the correction." (same 9 words) only if a team member really spotted the bug, and fill the 5F answer first. Never say "we found it" or "we found it ourselves" otherwise.
- Whatever the answer, every member should be able to explain every claim in their own words. Judges may ask at the Grand Final.

### F. One-sentence answers to prepare (Q&A)

- **Why does the St. Dominic's card send people towards Senado?** Routes are scored by length, stairs and capacity, not by the destination's state, so the operator decides.
- **Why no early warning in the live run?** The scripted crowd builds in about 3 minutes; the 5-15 minute skill is measured offline on simulated days. The first CRITICAL forecast came within about a minute of the true crossing: 21 s after it in run A, and 74 s before it in run B, but at 48% confidence and flagged for review. The first confident CRITICAL forecast came after the crossing in both runs. So there was no early warning in this scenario.
- **What exactly is the 30%?** A prototype setting, not measured: on approval the live simulation makes routes into the zone 30% less attractive for 20 minutes (14:14-14:34 in run A), so its inflow falls by less than 30%; the forecast what-if recalculation scales the zone's inflow by 0.7. (Earlier docs said "30% of inbound flow diverts" and the previous script "30 percent of the incoming flow diverts", which the live simulation never did (the forecast what-if does scale inflow by 0.7, and the dashboard shows "inflow ×0.7"); commits be83d39 and 8f3c8ca corrected the docs and the last three places that carried the old wording: README.md line 106 ("assumed 30% diversion"), the dashboard's SketchFuture box (dashboard/src/components/SketchFutureCheck.tsx, lines 22 and 34: "the extreme case of the assumed 30% diversion"), and the first clause of the evidence panel's assumed-effect note ("…not validated): 30% less inbound flow.", backend/app/services/intervention.py line 144; the sentence after it is correct). See 5A item 7. Answer from the code, as here.)
- **Did approving the redirect help?** Only modestly: Senado ended less crowded (0.75 vs 0.82; earlier pair 0.73 vs 0.87), but in the final pair its time above CRITICAL was not shortened (32 vs 31 minutes; no minutes figure was recorded for the earlier pair), and in both pairs it stayed above CRITICAL. Two pairs of runs with an assumed effect and a scripted operator, so it is not evidence of a real-world effect.
- **Is calibration in the app?** Not yet: it was a post-hoc test on one camera, proposed as an installation step.
- **Is the 97% a benchmark?** No: 11 frames from one clip, which is why we ran 2,000 frames.
- **Does 97% mean it found 97% of the people?** No: it is a count ratio (detector count ÷ hand count, summed over 11 frames), so misses and false boxes can cancel. Per-person recall was measured only on the Mall benchmark: 55% overall (78% near / 64% middle / 42% far), with 93% of boxes being people and a count ratio of 59%.
- **Secondary figures kept off screen:**
  - +15 min CRITICAL recall 0.908 vs 0.792 (per zone-minute).
  - Flagged for review: 1.4-1.7% of forecasts across horizons, right 56-57% vs 97-98% for the rest.
  - Stress day (rain + closure + surge): F1 0.857 / 0.832 / 0.814; the unusual-data check flags 11-12% of inputs vs 0.6-0.7% on normal days.
  - Mall: 13-53 people per frame; count correlation 0.80. YOLO11n speed: about 6-8 ms per frame on a Mac; phone speed not yet measured.
  - SketchFuture map: 575 nodes, 692 segments; a full closure is the worst case of a partial redirect.
- **Who did what (fill with the true account, consistent with the AI-assistance line and the who-built-what grid):**
  - **How was the timing bug found?** [TEAM TO FILL. It decides S12's M2 line (5E).]
  - **Who made the 11 hand counts on the street clip?** [TEAM TO FILL. The repo does not record it (ground_truth.csv was committed only in 391da20 and 3abcd7a, both with an AI co-author line). It decides whether S11 may say "as we did by hand" instead of "as a careful hand count" (5E).]
- **Who clicked APPROVE in the demo?** The capture was scripted to keep timing exact, and the on-screen footer says so; the approval step and the audit log are the real code path.

### G. Timeline (deadline 25 Oct, 23:59 HKT)

| dates | work |
|---|---|
| 13-15 Oct | Research slots and names (fonts downloaded; the two dashboard strings of 5A item 7 and the capture.py changes are done, 8f3c8ca); rebuild the dashboard; rehearse the full C2a + C2b capture sequence once, with the Simulator app joined, and write the measured times into section 6, "Timing"; timed read-through of the whole script (section 6, "Runtime control"); commit the dated Melbourne mapping before any analysis |
| 15-18 Oct | All MG renders and UI / iOS / terminal captures; face mosaics for S02, S11, S12 |
| 18-20 Oct | Voice and camera shoots (overrun cuts marked in the script first) |
| 21 Oct | Rough cut on real voices |
| ≈22-23 Oct | Melbourne result into S16 |
| 24 Oct | Lock, export, watch on a phone with sound off |
| 25 Oct | Upload with a buffer |

---

## 6. Production notes per visual type

### Global look and tools

- **Canvas:** 1920×1080 at 30 fps. Navy background (#0B1220), off-white text (#E6EDF7). Dashboard colour meanings: SAFE green, WARNING amber, CRITICAL red (#E5484D).
- **Fixed slots (no element shares a corner):**

| element | slot on the 1920×1080 canvas |
|---|---|
| Chapter card (2 s, over the picture, no added runtime) | top-left, x 60, y 48 |
| Status badge (pill) | top-right, right edge at x 1860, y 48 |
| Badge sub-line (optional, one short line, small) | top-right, right-aligned under the pill, y 96-120 |
| Lower-third with STEMB strip (speaker name only) | left, y 800-890 |
| Burned-in caption | bottom-centre, y 920-990, at most 1400 px wide |
| Evidence legend (S10-S16) | thin strip, bottom-right, y 1000-1024, at most 620 px wide |
| Source footer (small monospace) | bottom-left, y 1032-1060, at most 1150 px wide |

  On UI captures, check that the top-right badge does not cover the SIM CLOCK or a value the narration names; if it does, drop the badge just below the dashboard's status bar for that shot.
- **Badges:** SIMULATED (amber), REAL DATA (green), MODEL CHECK (purple), PENDING (grey, dashed), CORRECTED (white outline), LIVE SOFTWARE (cyan), ILLUSTRATION (grey). No other badge text: S08 is LIVE SOFTWARE, and S14 is SIMULATED (one of the five legend badges, like every shot from S10 to S16).
- **STEMB strip:** in every lower-third, lighting the speaker's letter.
- **Faces:** CC0 covers copyright, not the likeness of the people in the clip. Mosaic every recognisable stranger's face in S02, S11 and S12 (Pillow mosaic on the head region: shrink by about 10× with BOX, enlarge with NEAREST), keeping the detection boxes visible.
- **Fonts:** Geist (Latin) and Noto Sans TC (Chinese), both SIL OFL, are in `video/build/fonts/` with their licence files (git-ignored). Both are variable fonts: set the weight with Pillow's `set_variation_by_axes`. The end card credits "fonts: Geist, Noto Sans TC (SIL OFL)".
- **Tools present:**
  - Pillow 12.3.0 in `.venv`.
  - The installed ffmpeg **has no `subtitles` or `drawtext` filter**. It does have overlay, zoompan, xfade, crop, scale, setpts, gblur, boxblur, loudnorm and afftdn. So every caption, badge and lower-third is a transparent Pillow PNG composited with `overlay=...:enable='between(t,a,b)'`.
- **Guide track:** one file per shot, made with `say -v Daniel -r 155 -o guide/S10.aiff "<spoken text>"`. Write the numbers as words, as in the pronunciation guide. Measured on this script, it runs at about 147 wpm and every shot fits. Do not time with `-r 140` (about 126 wpm with this voice).

### motion_graphic (S01, S05 title, S06, S07, S09, S10, S14, S16, S17, S18, S20, all overlays)

- **Method:** one Python script per shot, sharing a style module. It writes PNG frames with cubic ease-in-out; encode with `ffmpeg -framerate 30 -i f_%05d.png -c:v libx264 -crf 18 -pix_fmt yuv420p SNN.mp4`. Keep scripts and renders in the team's video folder (`video/build/` is already git-ignored).
- **Data-driven shots read the repo files directly:**

| shot | data source |
|---|---|
| S01 / S18 | zones.json lat/lon (simple linear projection), edges, has_stairs; Senado colour from A_timeline.csv |
| S10 | metrics.json (bars at 3 decimals; no gap labels) |
| S14 | A_timeline.csv / B_timeline.csv (zone == senado_square, true_density) and A_events.json; effect window 14:14-14:34 and 32 vs 31 minutes from simulation_run/README.md |
| S16 | minute/*.csv.gz, filtering sensors.csv to the ids present |

- **Shot rules:**
  - S01 and S18: draw icons as Pillow shapes, and keep the "Illustrative story" label visible.
  - S10: the legend appears centre-screen, then docks as the bottom-right strip; it never sits top-left.
  - S14: Senado is never drawn green, the two recorded pairs are labelled separately, and the assumed effect window (14:14-14:34) is shaded so the 14:40 values visibly come after it.
  - S17: the cost panel stays empty until sourced.

### ui_capture (S03, S04, S09 crops, S15, the S12 README insert)

**Setup (capture C2: one fresh backend run, recorded as two capture.py runs against it, C2a then C2b).** Start the backend last. The moment it starts, it primes the live simulation to 13:53 and runs it at 10×, so every real minute spent after that costs about 10 simulated minutes.

1. Build the dashboard once in advance (about 1 real minute; rebuild after any dashboard change, e.g. 5A item 7), then start the production build on :3100, so no Next.js dev badge appears (the commands in experiments/results/simulation_run/README.md):

   ```
   cd dashboard && node node_modules/next/dist/bin/next build           # once, in advance
   cd dashboard && node node_modules/next/dist/bin/next start -p 3100   # then, in its own terminal
   ```

2. Start SketchFuture: `cd sketchfuture && npm run dev` (:4173).
3. Keep the Mac awake (`caffeinate`).
4. Start the iOS app in the Simulator, as in runs A and B (ios_capture steps 1-3): location Avenida de Almeida Ribeiro, Mode Video, Detector YOLO11n, Backend URL `http://localhost:8000` (the app's default), Start on the Live tab. It buffers until the backend is up, then joins at Almeida as a second sensor there. Runs A and B, whose timing table this plan relies on, were recorded with this phone joined (simulation_run/README.md), so every C2 run, C2c included, has it joined too. (`CROWDPULSE_PHONE_NODE` is read only by the run_sim.py recorder; C2 does not need it.) S02 is recorded in this run (ios_capture, "Which backend").
5. Start the backend last, on a new database file for every run (e.g. video_run_2.db for the second), and launch the C2a capture.py run within a few seconds (`.venv/bin/python video/capture.py <C2a shot file> --port 9333 --out video/build/clips/C2a.mp4`):

   ```
   CROWDPULSE_DATABASE_URL=sqlite:///video_run.db CROWDPULSE_CORS_ORIGINS=http://localhost:3100 CROWDPULSE_SIM_ACCELERATION=10 .venv/bin/uvicorn backend.app.main:app --port 8000
   ```

**Timing:**
- At 10× speed, read the simulated times in the README timing table (experiments/results/simulation_run/README.md; its columns are run A and run B, both in simulated Macau time). One real second is about 10 simulated seconds, counted from 13:53 at backend start. The Senado redirect appears at ≈14:09-14:11, about 1.6-1.8 real minutes after start. In run A the St. Dominic's redirect card was pending from ≈14:06 to ≈14:26 sim.
- Each capture.py run starts Chrome with a fresh temporary profile, so tiles cached in an earlier run are gone. Only the S03 map moment needs warm tiles, so C2a, launched within a few seconds of the backend (setup step 5), opens on the Live map (`http://localhost:3100/map`) and stays there until ≈14:08 sim. Expect Senado amber (WARNING) on the map then, as in run A; it turns red on Zone detail when the rows go CRITICAL (≈14:09). Cut on whatever colour the capture shows.
- **When C2b can start.** C2a's recording ends at ≈14:11-14:12 sim (≈113 real seconds after the backend starts). capture.py then encodes the clip with ffmpeg (libx264, CRF 18, 1080p, ≈110 s of footage), and today it shuts its Chrome down only after that encode. Both runs also use the fixed DevTools port 9333, so a C2b launched early would attach to C2a's Chrome and be killed by C2a's cleanup.
  - **With the capture.py change** (section 6, "Recorder": `--port`, Chrome closed before the encode), launch C2b on `--port 9334` as soon as C2a prints that recording has stopped: C2b starts at ≈14:12 sim, its APPROVE click lands at ≈14:14 (as in run A) and its St. Dominic's click at ≈14:16-14:17. C2a's encode then runs while C2b records, so check C2b's rehearsal footage for dropped frames (if any, start the encode with `nice`).
  - **Without it,** C2b must wait for C2a's encode, which takes roughly 20-60 real seconds (3-10 simulated minutes). C2b then starts at ≈14:15-14:21 sim, APPROVE lands at ≈14:17-14:23, and the St. Dominic's step, about 25-30 real seconds (4-5 sim min) after C2b starts, at ≈14:19-14:26. That card was created at 14:06:29 in run A, and recommendations expire 20 minutes after creation (`INTERVENTION_TTL_MIN = 20`, backend/app/services/engine.py), so it would be gone at about 14:26.
  - **Rehearsal result (fill in):** C2a recording ended at [__] sim · encode took [__] real s · C2b started at [__] sim · APPROVE at [__] · St. Dominic's click at [__] · St. Dominic's card created at [__].
  - **Decision rule:** if the rehearsal puts the St. Dominic's click later than ≈14:20 sim, or the capture.py change is not made, plan S15 as its own C2c from the start (below) and keep C2b for S04 and the S09 lists only (drop its last five steps, from `wait_for '#stdom-sf'` on).
- C2a's final wait stays at about 20 s (to ≈14:11 sim): S03 needs about 8 s of Zone detail. A confident row appears in that window only if the run produces one (run A: 14:09:08; run B's first confident CRITICAL forecast came at 14:13:14), so S03's picture shows one only if the capture does; the narration does not depend on it.

**Recorder:** `video/capture.py` (committed, 8f3c8ca) drives headless Chrome over DevTools, draws a visible pointer, writes frames to disk as they arrive (so a failed step keeps the footage recorded so far) and encodes 1080p at a constant frame rate. Shot files are JSON with navigate / wait / click / click_text / scroll / scroll_to / eval / wait_for steps. `wait_for` polls for a CSS selector until it exists (deadline at least 120 s), so it can wait for things that appear at a run-dependent time.

**capture.py changes made (8f3c8ca):** a `--port` flag (default 9333) for the DevTools port, Chrome shut down as soon as the last step ends and before the ffmpeg encode, and a "recording stopped" line. C2b can therefore start on `--port 9334` as soon as C2a prints that line, while C2a is still encoding ("Timing" above).

**Tagging pattern.** The elements to click have no ids, and some appear only at a run-dependent time. A one-shot `eval` tags nothing if the element is not there yet, and a polling `eval` would hit capture.py's 30 s DevTools timeout. So each run first installs a non-blocking `eval` that starts a `setInterval` tagger (it returns at once and keeps tagging every 0.5 s, also after client-side navigation), then uses `wait_for` on the tag before clicking it. A `navigate` step reloads the page and clears the tagger, so install it again after any `navigate`.

**C2a (S03, S09 zone-detail crop):** shot `url` = `http://localhost:3100/map`. Clicking a zone marker on /map only fills the sidebar; the sidebar's "open zone detail →" link opens Zone detail. The Senado marker is an unlabelled `div.cp-zone-marker`.

```
{"eval": "setInterval(() => { const m = [...document.querySelectorAll('.cp-zone-marker')].find(e => e.textContent.includes('Senado Square')); if (m) m.id = 'senado-marker'; }, 500)"}
{"wait_for": "#senado-marker"}
{"wait": 80}
{"click": "#senado-marker"}
{"wait": 1}
{"click_text": "open zone detail"}
{"wait": 20}
```

Set the first `wait` in the rehearsal so the click lands at ≈14:08 sim (about 90 real seconds after the backend starts), and the last so Zone detail runs to ≈14:11 sim. (Or `{"navigate": "http://localhost:3100/zones/senado_square"}` if the click misses.)

**C2b (S04, S09 lists, S15):** shot `url` = `http://localhost:3100/interventions`; launch with `.venv/bin/python video/capture.py <C2b shot file> --port 9334 --out video/build/clips/C2b.mp4` at the time given in "Timing". `click_text "APPROVE"` would hit the first card on the page, which may belong to another zone (in run A it was Rua de S. Paulo, #6), and `click_text "Public notice"` likewise opens the first card's notice. So the tagger finds the pending card whose `h3` title includes "around Senado Square" and tags that card, its notice, its VIEW EVIDENCE and APPROVE buttons, and the "Decided / expired" and "Audit log" headings. It also tags the St. Dominic's card's TEST IN SKETCHFUTURE link and removes its `target=_blank`, so SketchFuture loads in the recorded tab. Before the click, an `eval` centres that link in the viewport, so the card title stays in frame above it (`scroll_to` would align the link to the top edge and push the title out).

```
{"eval": "setInterval(() => { const card = t => [...document.querySelectorAll('h3')].find(h => h.textContent.includes(t))?.parentElement; const s = card('around Senado Square'); if (s) { s.id = 'senado-card'; const b = t => [...s.querySelectorAll('button')].find(x => x.textContent.trim() === t); if (b('APPROVE')) b('APPROVE').id = 'senado-approve'; if (b('VIEW EVIDENCE')) b('VIEW EVIDENCE').id = 'senado-evidence'; const n = s.querySelector('summary'); if (n) n.id = 'senado-notice'; } const d = card('around St. Dominic'); const a = d && d.querySelector('[data-testid=sketchfuture-link]'); if (a) { a.id = 'stdom-sf'; a.removeAttribute('target'); } const h2 = t => [...document.querySelectorAll('h2')].find(h => h.textContent.includes(t)); if (h2('Decided')) h2('Decided').id = 'decided'; if (h2('Audit log')) h2('Audit log').id = 'audit-log'; }, 500)"}
{"wait_for": "#senado-approve"}
{"scroll_to": "#senado-card"}
{"wait": 3}
{"click": "#senado-notice"}
{"wait": 3}
{"click": "#senado-evidence"}
{"wait": 2}
{"click": "#senado-approve"}
{"wait": 2}
{"scroll_to": "#decided"}
{"wait": 2}
{"scroll_to": "#audit-log"}
{"wait": 3}
{"wait_for": "#stdom-sf"}
{"eval": "document.querySelector('#stdom-sf').scrollIntoView({behavior: 'smooth', block: 'center'})"}
{"wait": 2}
{"click": "#stdom-sf"}
{"wait": 15}
```

Rehearse the full C2a + C2b sequence once before the real take, and fill in the rehearsal line under "Timing". If the St. Dominic's card has gone by the time C2b reaches it (the `wait_for` then times out and the footage so far is kept), or the decision rule under "Timing" applies, record S15 alone as **C2c**: a fresh backend run (new database, the Simulator app joined, setup steps 4-5), with a C2c shot file on /interventions that holds the same tagger and only the last five C2b steps (`wait_for '#stdom-sf'`, the centring `eval`, `wait 2`, `click '#stdom-sf'`, `wait 15`), launched within a few seconds of its backend. The `wait_for` then returns when the card appears (≈14:06:30 sim in run A, ≈80 real s, inside the 120 s deadline), so the click lands at ≈14:07-14:15 sim, well before the card expires. If C2a or C2b fails part-way, keep its footage and re-record only the missing part against a fresh backend.

macOS screen recording at 125% browser zoom is the fallback. It is also the only route in which a member really clicks APPROVE (see 5D).

**Rules while recording:**
- Act on the newest card: superseded or expired cards answer 409.
- S03: forecast rows can flip back (run A: +5 back to WARNING at 14:09:46, all three WARNING at 14:11:02 when the reading dipped). Cut on what the capture shows; never stage or composite rows.
- S04: check that the captured card says "Chosen route avoids stairs and steep sections" (it did in run A).
- S15: the Senado card cannot be tested, because the Almeida corridors are outside SketchFuture's map. Use the St. Dominic's card and check its plan title. If no St. Dominic's redirect appears, restart the run. SketchFuture is seeded, so #721's numbers should reproduce; narrate and caption whatever is captured, including the arrive-in-both counts.
- Old 30% wording (only if the code was not corrected first, 5A item 7):
  - S04: during the evidence beat, keep the zoom on the buttons, the rationale bullets and the "Current forecast" row, with its bottom edge above the panel's "Assumed effect:" line.
  - S15: zoom on the card title, then pan to the TEST IN SKETCHFUTURE button, keeping the crop's bottom edge just under the button row. The box's description and its grey "Model check, not evidence: … assumed 30% diversion" line sit below the button. One wide frame of the whole card would show them, so use the pan, or a letterboxed crop on navy.
  - Never show either line readable, in motion or in a still.
- Keep the OSM attribution visible on every map shot.

### S12 README insert (2 s)

Show the README's Correction paragraph as the real file, rendered, not retyped:
1. Render it once: `pandoc README.md -s --metadata pagetitle=README.md -o video/build/README.html` (pandoc is installed; `video/build/` is git-ignored).
2. Record it with capture.py. The shot `url` is `file://<absolute repo path>/video/build/README.html`, and no backend is needed:

```
{"eval": "[...document.querySelectorAll('p')].find(p => p.textContent.startsWith('Correction:')).id = 'correction'"}
{"scroll_to": "#correction"}
{"wait": 4}
```

3. Draw the highlight box in post (a Pillow PNG, like the S03 WHY highlight). The footer reads "README.md · Correction".

**Fallback:** a Pillow-typeset verbatim excerpt of the paragraph, with the footer "README.md · Correction (excerpt)". This is a labelled document excerpt, not a recorded result, so typesetting is allowed here; S08 stays recorded live.

### ios_capture (S02)

1. Build and run the app from Xcode (Cmd-R) on the booted simulator. Or from the command line:
   - `cd ios/CrowdPulseSensor && xcodebuild build -project CrowdPulseSensor.xcodeproj -scheme CrowdPulseSensor -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -derivedDataPath <a build folder outside the repo>`
   - `xcrun simctl install booted <that folder>/Build/Products/Debug-iphonesimulator/CrowdPulseSensor.app` (check the .app name in that folder)
   - `xcrun simctl launch booted org.crowdpulse.sensor`
   - (docs/testing.md §1 only runs the tests; it does not launch the app for recording.)
2. Set the location: `xcrun simctl location booted set 22.19282,113.53925`.
3. In the app: on the Setup tab set Mode → Video and Detector → YOLO11n, and leave Backend URL at `http://localhost:8000`; then press Start on the Live tab. Uploads show HTTP 202 once the C2 backend is up (see "Which backend" below).
4. Record during C2a's map wait, when nothing is clicked: once the Live tab shows HTTP 202, run `xcrun simctl io booted recordVideo --codec=h264 S02_sim.mp4` (the documented `--codec=<codec>` form) for about 30 s, then stop it with Ctrl-C well before C2a's click (≈90 real s after the backend starts), so it adds no load during the S03 moment.
5. Screenshot the Debug tab ("Last observation (exact payload)") for the payload card after C2b, while the app is still running, and copy its key names exactly (`flow_direction_deg`, `heading_deg`, `latitude` / `longitude`).

**Which backend (decision):** reproduce runs A and B. During C2 the app posts to the C2 backend on :8000 and joins at Almeida Ribeiro (ui_capture setup step 4), and S02 is recorded in that same run. Its readings are re-timed onto the simulated clock (docs/testing.md §6.2), as they were in runs A and B, so the README timing table stays the reference for C2. Never point the app at the S08 privacy backend (:8001), and never run the app against a second backend while C2 runs. If S02 must be re-shot outside C2, use a separate backend with no simulation (`CROWDPULSE_LIVE_SIM=false CROWDPULSE_DATABASE_URL=sqlite:///phone_demo.db .venv/bin/uvicorn backend.app.main:app --port 8000`), started only when no C2 backend is running, so the app's default Backend URL still matches.

**Fallback:** ios_app_video_mode_30s.mp4. Its payload values then get the label "example payload · test run, 29 Sep 2026".

**Captions and faces:**
- The caption must say iPhone Simulator: no physical-phone run is documented.
- Near-field faces can be identifiable; pixelate them. Keep the push-in modest. For moving video, pixelate the head band only for the seconds a face is recognisable, e.g. `ffmpeg -i S02_sim.mp4 -filter_complex "[0:v]split[base][c];[c]crop=W:H:X:Y,scale=iw/12:ih/12,scale=W:H:flags=neighbor[pix];[base][pix]overlay=X:Y:enable='between(t,T1,T2)'" -c:v libx264 -crf 18 -pix_fmt yuv420p S02_pix.mp4`, with W, H, X, Y measured on the recording. Keep the band tight to the heads so the boxes below stay readable.

### terminal (S08)

**Use a separate backend, so the test reading never joins the C2 run:**

```
CROWDPULSE_DATABASE_URL=sqlite:///privacy_demo.db CROWDPULSE_LIVE_SIM=false .venv/bin/uvicorn backend.app.main:app --port 8001
```

**Prepare the inputs:**
- `obs.json`: the observation JSON from docs/testing.md §5 without `face_id`, with a fresh UTC timestamp (`date -u +%Y-%m-%dT%H:%M:%SZ`).
- `obs_face.json`: the same JSON plus `"face_id":"abc"`.
- `frame.jpg`: a blank generated image with no people.

**Commands:**
- `curl -s -o /dev/null -w "%{http_code}\n" -H 'content-type: application/json' -d @obs.json localhost:8001/sensor/observation` → 202
- the same command with `@obs_face.json` → 422
- `curl -s -w "\n%{http_code}\n" -F "file=@frame.jpg;type=image/jpeg" localhost:8001/sensor/observation` → 403, plus the PRIVACY_MODE message

**Recording:** dry-run all three codes first, then record with `video/record_terminal.py`. It runs the three commands in a real shell inside a pseudo-terminal, typing them at a human pace, and saves every output byte with its time (an asciinema-style cast); its renderer then draws that stream frame by frame as a dark monospace terminal (28 pt or larger) at 30 fps, 1920×1080. Nothing is retyped or edited: the status codes and the PRIVACY_MODE message on screen are the bytes the backend returned. This replaces a desktop screen recording, which could catch other windows and needs a Screen Recording permission. Never typeset this shot by hand.

### figure (S11, S13; fallbacks for S03, S04, S09, S14)

- **S11:** `experiments/results/video/detector_overlay.png` is 1950×615: two panels side by side (about 3.2:1) with titles above. Never run zoompan on the whole image: mapping it onto 16:9 squeezes the people. Instead:
  1. **Pillow prep (`S11_prep.py`):** mosaic every recognisable face (e.g. the man at the centre of both panels; the frame is the same in both, so measure head boxes once and shift them by the panel offset). Keep each mosaic inside the head, under the green box's top edge, so the boxes stay visible. Then crop each panel's picture area (about x 28-958 and x 992-1922, y 68-592; measure the exact edges once) and save `S11_apple.png` and `S11_yolo.png` (each about 930×525, close to 16:9). The panel titles are replaced by Pillow labels ("Apple's built-in detector" / "YOLO11n (Ultralytics), open model on the device").
  2. **Per panel, fit to 16:9 then push in:** `ffmpeg -i S11_apple.png -vf "scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2:color=0x0B1220,zoompan=z='min(zoom+0.0004,1.06)':d=135:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30" -frames:v 135 -pix_fmt yuv420p S11_apple.mp4` (same for `S11_yolo`).
  3. **Wipe:** `ffmpeg -i S11_apple.mp4 -i S11_yolo.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=1:offset=3.5,format=yuv420p" -c:v libx264 -crf 18 S11_fig.mp4` (8 s), followed by 10 s of Pillow bars redrawn from summary.md, titled "count vs hand count".
- **S12 laptop screen:** show `S11_apple.png` / `S11_yolo.png` (already mosaicked). If the clip itself is needed, use `ios/CrowdPulseSensor/Resources/sample_crowd.mp4` (the tracked 640×360 CC0 transcode) and mosaic in post; the `experiments/datasets/video/yonge_dundas_*_10fps.mp4` files are git-ignored and exist only locally.
- **S13:** `experiments/results/mall/mall_count_scatter.png` and `mall_count_timeline.png` are charts with no dataset imagery; **never** show a Mall frame.
- **S14 fallback:** the top panel of `simulation_run_timeline.png` (it shows only the final pair; label the earlier pair as text).
- **A07 fallback (S04, S09):** prefer the live C2b capture. `A07_intervention_evidence.png` (1440×1789) was taken before commit be83d39, and its evidence panel's "Assumed effect:" line (at about y 836) still says "Assumes 30% of inbound flow diverts". If A07 is used:
  - for S04, crop with the bottom edge just under the "Current forecast" row (about y 805; measure once). The frame then keeps the route, the ♿ line, the notices, the evidence bullets and the forecast row. If a crop cannot be used, mask that line with a plain box;
  - for S09, crop to the Decided / expired list (about y 1170-1320).
- **Never** use `model_comparison.png` for the spoken numbers.

### team_footage (S05, S06, S12, S17 B-roll, S19)

- **Camera:** phone on a tripod, landscape, 1080p30, locked exposure, eye level. S12: frame the two members in the left half; the right half carries the timing inset.
- **Set:** same background for S05 and S19, window light from the side.
- **Sound:** record clean voice separately as a backup.
- **Pacing:** hard cuts on the beat for the roll call (about 0.8 s each).
- **Props:** only real artefacts; no figures that are not in section 4. A phone shows the app only if the app was really installed on it (docs/testing.md §6.1); otherwise its screen is off. No prop implies a field run.
- **Screens in shot:** any screen showing the street clip shows the mosaicked stills only.

### Audio, captions and assembly

- **Clean the voices:** `ffmpeg -i in.m4a -af "highpass=f=80,afftdn,loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 SNN.wav`.
- **Music:** none, or a quiet synthesized pad (ffmpeg `aevalsrc` or numpy) about 28 dB under the voice. No third-party music.
- **Captions:** burned-in English on every line, rendered as Pillow PNGs from the narration column with timings taken from the real takes, in the bottom-centre caption slot. Chinese and Portuguese UI text gets a small English gloss.
- **Assembly:**
  1. Render each shot to its exact duration.
  2. Composite the overlays.
  3. Join with the concat demuxer, using `xfade` only at chapter turns.
  4. Export H.264 (CRF 18, yuv420p) with AAC 48 kHz at about −16 LUFS.
- **Final check:** on a phone, with sound off: every badge, footer and caption must be readable, and no element overlaps another in any corner.

### On-screen text load (evidence shots)

Each beat shows only its required lines: the spoken number and its status. Secondary figures stay off screen, ready as Q&A answers (5F) and in the cited source files.

| shot | required on screen | secondary (kept off screen) |
|---|---|---|
| S10 | SIMULATED badge; macro-F1 bars at 3 decimals with a one-line axis definition and the "no change" legend; "91% vs 79% of critical minutes"; "flagged: right 56% · the rest: 97%"; footer with the 9 / 2 / 3-day split | gap labels (dropped); recall 0.908 vs 0.792; flagged share and accuracy across horizons; the stress-day strip |
| S11 | REAL DATA badge; panel labels; "count vs hand count" bars with their one-line definition (summed over the frames in each group) and the densest pair's "2 frames with ≥10 nearby people" tag; nearby definition and error; CC0 credit; footer | the separate "YOLO11n = Ultralytics' open pretrained model" line (folded into the panel label) |
| S13 | REAL DATA badge; "count vs annotated count: 59% · 93% of boxes are people"; recall bars by distance; the calibration counter with "post-hoc · one camera · held-out frames 801-2000 · not yet in the app"; footer with the dataset citation | 13-53 people per frame; count correlation 0.80; overall recall 55%; YOLO11n speed on a Mac |
| S14 | SIMULATED badge; the chart with its run A markers, end labels, effect band and the 14:40 line (end densities for both pairs; 32 vs 31 minutes above CRITICAL for this pair only); one limit chip (the assumed effect); the clock panel with its merged label (no early warning · skill shown offline); footer | the "Senado stayed above CRITICAL" chip (dropped: the narration, the end labels and the CRITICAL line carry it); the "Crowd built in ~3 min … no early warning" chip (merged into the clock label); "two pairs of runs" (dropped: "earlier pair" says it); the old free-standing "5-15 min skill" line (already the clock label) |
| S15 | MODEL CHECK badge; counter header; the three counters; the arrive-in-both line (stroller 28/40 appears only here); the 24-of-40 line; footer with OSM attribution | 575 nodes / 692 segments; "full closure = worst case of a partial redirect"; the duplicate stroller line (removed) |

### Runtime control after the real voices

**Decision (third review): no content is cut in advance.**
- **The problem.** At the 140 wpm planning rate the cut runs 4:19.5, only 0.5 s under the 4:20 target. Eight shots already fill 0.95-0.98 of their length, and at 130 wpm the cut runs about 4:37, still above 4:20 after cuts 1-6.
- **Considered and not taken.** Applying cuts 5 and 2 in advance would give about 4:16.5. Cut 2 removes "not the crowd building ahead", the line that sets up the next-fifteen-minutes idea, and cut 5 removes the stated reason for the 2,000-frame benchmark. Both would weaken the video more than 3 s of slack would help it.

**What the team does instead:**
1. **Read-through (13-15 Oct).** Each member reads their lines at natural pace against a stopwatch. Add the visual-only beats (27.6 s). If the total is over 4:35, apply cuts 5 and 2 to the script before recording, and re-measure.
2. **After the voice shoot,** re-time every shot from the real takes (5C).
3. **Over 4:20:** apply cuts 1-6 below, in order, skipping any already applied.
4. **The 4:20 target is soft; the 5:00 limit is not.** A locked cut of up to 4:45 is accepted. Expected outcomes:
   - at 130 wpm: about 4:37 before the cuts, about 4:28 after them;
   - at 120 wpm: about 4:58 before, about 4:49 after.
5. **Still over 4:45:** re-record the slowest takes a little faster rather than cut any never-cut item.

**Overrun plan (mark these in the script before the voice shoot):**

| shot | fill at 140 wpm | if the real take overruns |
|---|---|---|
| S01 | 24 words in the 10.5 s after the 1 s title (0.98; guide 7.95 s) | Cut 2 (−2 s). |
| S05 | 9 words in 8.5 s, including the 2 s silent title hold | Deliberate roll-call and title beat; no change. |
| S08 | 18 words in 9.0 s (0.86; guide 8.75 s) | Deliberate stamp beats; cut 1 can take up to 0.5 s more of stamp hold. |
| S07 | 29 spoken words (28 written) in 13.0 s (0.96; guide 13.0 s) | Cut 4 (−2.5 s). |
| S11 | 41 words in 18.0 s (0.98; guide 17.0 s) | Cut 3 (−2 s). |
| S13 | 50 words in 22.0 s (0.97) | Cut 5 (−1 s). |
| S10, S14 | S10: 49 spoken words in 22.0 s (0.95). S14: 46 words in 20.5 s (0.96). | S10: start the narration over the docking legend. S14: cut 6 (shorter clock hold); never cut its limits. |
| S15, S16, S17 | 0.95-0.96 | S15: never cut the 24-of-40 sentence; borrow up to 0.5 s from S04 (0.86), unless S04 has already lent 0.5 s to S02 (S04 lends at most 0.5 s in all; S02's 403 hold comes first). S16: keep the result slot at most 15 words. S17: drop the cost slot if unsourced. |
| S19 | 20 words + 3 hand-offs (≈0.3-0.5 s each) + 1 s together in 11.0 s (guide 9.4 s without hand-offs) | Drop the separate all-together second (−1 s; the wide shot already holds everyone). Never cut a line. |

**If over 4:20, cut in this order:**
1. S08: up to 0.5 s more of stamp hold, only if the real take leaves room (the codes still land as spoken).
2. S01: drop ", not the crowd building ahead" (−2 s).
3. S11: drop "Apple's detector, 55" (it stays on screen; −2 s).
4. S07: drop ", from phones staff place temporarily" (S17 still says it; −2.5 s).
5. S13: "Eleven frames is small, so we tested" → "We also tested" (−1 s).
6. S14: end the shot sooner after the last word, trimming the clock panel's tail hold (−1 s; the panel already enters with the last spoken limit).

**Never cut:** S08's 202 / 422 / 403, S12 (the correction), S14's limits, S15's 24-of-40 sentence, S05's 2 s title hold, or S20's 6 s hold.

**If under 3:45 (e.g. slots dropped), add back:**
- S09: ", and only closer monitoring is suggested" (+2.5 s).
- S11: "within twenty metres" (+1 s).
- S14, after "it stayed critical": "It ended at 0.75 or below, against 0.82 or more." (+5 s).

### Never say or show

- "early warning in real time", "head start", "prevents crushes", "saves lives", "accurate in Macau", "people per square metre"
- "never sees faces" (say "nothing identifying leaves the phone")
- "our model" for YOLO11n
- a blanket "detours avoid stairs"
- "critical periods" (say "minutes")
- "this phone" without the Simulator caption
- calling the 97% a benchmark, or "found 97 percent of people" (the 11-frame figures are count ratios: detector count ÷ hand count)
- "as we did by hand" or "we counted by hand" unless a team member really made the 11 hand counts (S11 says "as a careful hand count"; 5E, 5F)
- presenting calibration as built into the app
- crediting the Senado detour with the SketchFuture result
- stating "a map-data gap" as the cause of 24 of 40
- "for the day" (battery life is unmeasured)
- Senado turning green
- a recognisable stranger's face (mosaic near-field faces in S02, S11 and S12; CC0 covers copyright, not likeness)
- a hand on a mouse over the scripted C2 APPROVE click, or that click without its "click scripted for this recording" footer
- "operator approves" (or any label implying a person) on S14's run A approval marker: the recorded runs' operator was a script (label it "approval (scripted operator), 14:14")
- 32 vs 31 minutes above CRITICAL as if it held for both pairs of runs (it is the final pair only)
- a phone prop showing the app unless the app was really installed on that phone, or anything implying a physical-phone field run
- "30 percent of the flow diverts" (the setting makes routes into the zone 30% less attractive for 20 minutes, so inflow falls by less)
- the same old wording inside the software, readable on screen: the SketchFuture box's "a full closure is the extreme case of the assumed 30% diversion" (SketchFutureCheck.tsx), the evidence note's first clause "…not validated): 30% less inbound flow." (intervention.py line 144), or A07's "Assumes 30% of inbound flow diverts" (correct the code first, 5A item 7, or keep them out of frame)
- "approving beat doing nothing" or "it shortened the time above CRITICAL" (32 vs 31 minutes; say "left Senado less crowded by the end, but only modestly")
- a badge outside the badge list (e.g. "SIMULATION RUN", "REAL · running code")
- staged or composited forecast rows
- "we found it" or "we found it ourselves" unless a team member really found the bug (S12 is written as "It was caught, fixed, …")
- "mapping fixed before looking" / "method fixed before we looked" without the dated Melbourne commit
- Mall imagery
- stock footage or copyrighted music
- Macau footage the team did not film itself
- any cost, injury count, battery life, phone speed or user-feedback number
- any predicted Melbourne result

---

## Appendix: what changed from the three drafts (fact-check fixes applied)

**Wording fixes:**

| issue in the drafts | fix in this script |
|---|---|
| S12 / S19 credited the Senado detour with SketchFuture's St. Dominic's result (#721) | The narration names "another recommendation, at St. Dominic's", the card title is shown, and S14 says "approving the redirect". |
| The cause of 24 of 40 was asserted as a map-data gap | The cause is left open: "Real barrier, or missing map data? Only a street survey can tell." |
| "never sees her face" | "Nothing identifying leaves the phone"; the payload footnote explains sensor_id. |
| "Our fix: label twenty frames per phone" | Calibration is "one camera … a lead, not proof", plus "post-hoc · not yet in the app" on screen. |
| "head start"; "full afternoon"; "30 percent of people" | Removed; the timeline is labelled 13:53-14:40. The interim "30 percent of the incoming flow" was replaced in the second review by "a diversion we assumed, not measured", with the setting on a chip. |
| "Detours avoid stairs" | "a stair-free detour", only for the captured card that says so. |
| "critical periods"; "our YOLO model"; "phones forecast" | "critical minutes"; "the open YOLO model in our app"; the research question says "help forecast". |

**Production and fact fixes:**

| issue in the drafts | fix in this script |
|---|---|
| "this phone" without saying Simulator | The S02 caption says iPhone Simulator on a Mac. |
| A typeset terminal under a REAL badge | S08 is recorded live, with a 202 positive control. |
| 8 street links; 134 Melbourne dots | 7 links from zones.json; dots only for the 99 ids in the archive (recount before recording). |
| The premise had no source | A source footer slot is added. |
| The S12 legend did not match the badges shown | The legend shows all five badges, and the narration says only "every result is labelled". |
| S22 still said "Next: Melbourne" | "Next" names only the street pilot. |
| Caption plan used ffmpeg `subtitles=` | Pillow PNG overlays. |
| Speaking time was unbalanced (141 vs 55 words) | 77-121 written words per member (after the second review). |

**Final review fixes (previous revision; rows marked "superseded" were changed again by the second review below):**

| issue | fix |
|---|---|
| S12 CORRECTED line read as the opposite timing direction ("2.4 s late") and left out the near-field recount | The overlay names both: timing "2.4 s off" (no direction) and the near-field rule, redefined and recounted (superseded: the long line is now a ≈12-word overlay, and the README paragraph carries the full wording). The claims row cites README, hackathon-notes and commit 3abcd7a (Apple 34% / 8% → 55% / 9%). |
| "We found it ourselves" is unrecorded; the fix commit has an AI co-author line | "We found it, fixed it, and published the correction." 5E and 5F cover how it was found. |
| Recognisable faces in S11 (enlarged by the push-in) and on the S12 laptop; S02 note said faces are a few pixels | Pillow mosaic before any zoom in S11; S12 laptop shows the mosaicked stills; S02 note now "near-field faces can be identifiable; pixelate them"; added to the never-show list and the credits ("faces pixelated by us"). |
| S11 zoompan squeezed the 1950×615 two-panel figure, and a single zoompan could not wipe | Crop each panel, fit with `force_original_aspect_ratio=decrease` + pad to 3840×2160, zoompan to 1920×1080, `xfade=wipeleft`. |
| S10 "+3.7" label contradicted the bars (0.887 − 0.849 = 3.8) | Superseded: +3.8 came from rounded bars (the real gap is 3.72), so the gap labels are dropped; if restored, +3.7 / +4.9 / +7.0 with a footnote. |
| S15 averages cover different groups | Small line: "averages over those who arrive in both plans: walkers 40/40 · wheelchair users 16/40 · stroller users 28/40"; stroller count briefly added to the 40-dot caption too (superseded: that duplicate is removed; 28/40 appears once). VERIFICATION.md does not say why the other 12 stroller users miss a plan, so no cause is claimed. |
| S16 "mapping fixed before looking at results" not yet true in the repo | The line appears only with a dated commit in experiments/datasets/melbourne/README.md; otherwise deleted. 5B and the timeline add the commit step. |
| S04 hand insert would stage a human click over the scripted pointer | Dropped; a hand insert is allowed only during a member's real click in the macOS screen-recording take. |
| S09 equation said raw "sensor reliability" | "sensor-reliability factor" (0.4 + 0.6 × reliability, prediction.py line 146), matching the dashboard footer. |
| S18 "Every redirect keeps the main route open" | "Every redirect recommendation includes keeping the main route open, with staff, …". |
| S12 asset pointed to experiments/datasets/video/yonge_dundas_640_10fps.mp4 | That file exists only locally (git-ignored); the asset now points to the mosaicked stills and the tracked ios/CrowdPulseSensor/Resources/sample_crowd.mp4. |
| S03 claimed all three rows become confident | "rows turn CRITICAL, first flagged LOW CONFIDENCE, then at least one confident"; cut on the capture; no staging. |
| `recordVideo --codec h264` | `--codec=h264` (documented form). |
| S03 marker click did not open Zone detail; tile caching across runs | Tag the marker → click `#senado-marker` → click_text "open zone detail"; the capture opens on /map so tiles load in the same profile (superseded in part: the tag is now a polling `setInterval` tagger followed by `wait_for`, and C2a is the run that opens on /map). |
| S02 payload card used "flow_direction" | Real keys: `flow_direction_deg`, `latitude` / `longitude`, `heading_deg`. |
| iOS steps: §1 only runs tests; Start is on the Live tab | Step 1 builds and launches (Xcode Cmd-R or build / install / launch); step 3 sets Mode and Detector on Setup, Start on Live. |
| Tight evidence shots could push the cut to ≈4:28 at 130 wpm | Overrun plan table; S05 / S08 marked as deliberate beats (superseded in part: S08 has already given back 0.5 s, and at 130 wpm the cut now runs ≈4:37). |
| Chapter card, badge and docked legend all claimed top-left | Fixed slot table: chapter card top-left, badge top-right, legend bottom-right strip, footer bottom-left, captions bottom-centre. |

**Second review fixes (earlier revision, 18 findings):**

| # | issue | fix |
|---|---|---|
| 1 | S14 said "30 percent of the incoming flow diverts"; the code makes routes into the zone 30% less attractive for 20 minutes (14:14-14:34 in run A), so inflow falls by less, and the forecast what-if scales inflow by 0.7 | Narration: "The effect rests on a diversion we assumed, not measured, …". Chip: "Assumed: routes into Senado made 30% less attractive for 20 min (prototype setting, not measured)". Effect window shaded on the chart. Concept limits, claims row, Q&A (with the docs-vs-code history) and never-say list updated. |
| 2 | "Approving the redirect beat doing nothing" overstated two pairs of runs: only the end density was lower, and time above CRITICAL was 32 vs 31 minutes | "left Senado less crowded by the end than doing nothing, but only modestly: it stayed critical"; on screen "minutes above CRITICAL: 32 vs 31 · two pairs of runs". (superseded in the fourth review, finding 5: "this pair: 32 vs 31 min above CRITICAL"; the minutes exist only for the final pair) |
| 3 | S10 gap label +3.8 came from rounded bars; the real gap is 3.72 (hackathon-notes: 3.7 / 4.9 / 7.0) | Gap labels dropped; if restored, +3.7 / +4.9 / +7.0 with the footnote "gaps from unrounded values, ml/models/metrics.json". |
| 4 | S11 "found 97 percent of nearby people" read as per-person recall; the figures are count ratios | "counted 97 percent as many nearby people as we did by hand" (superseded in the fourth review: "as a careful hand count"); bars titled "count vs hand count" with a one-line definition; S13 "counted 59%" labelled "count vs annotated count"; true recall (55%) only in Q&A. |
| 5 | The S04 callout "a person approves" under LIVE SOFTWARE implied a human click; the C2 click is scripted | Callout "needs a person's approval"; footer "click scripted for this recording · the approval runs the real code path"; concept line reworded. |
| 6 | S02 "not a person or device" went beyond docs/privacy.md (the ID is stable per app install) | "sensor_id = a random node label for a sensing position, not a person or a device serial"; S02 / S19 claims rows cite privacy.md. |
| 7 | S14 and S08 badges were outside the badge list | S14 "SIMULATED · recorded end-to-end run, 29 Sep 2026" (amber); S08 "LIVE SOFTWARE · recorded live" (cyan). |
| 8 | S03 asked for Senado red on the map at ≈14:08, when run A showed WARNING (amber) until 14:09:08 | "Senado amber (WARNING)" on the map; it turns red on Zone detail; cut on the capture. |
| 9 | Waiting on the map for red would lose the "turns critical" moment on Zone detail (the map uses the worse of current state and a confident forecast) | Same fix as 8, in the storyboard, the JSON and the capture timing notes. |
| 10 | One failed step lost the whole ≈6-minute C2 recording, and a one-shot eval could not tag a card that appears later | capture.py writes frames as they arrive; C2 split into C2a (map, zone detail) and C2b (interventions, SketchFuture) against one backend, with C2c as a fallback; a non-blocking `setInterval` tagger plus `wait_for` for the Senado marker, the Senado card's notice and buttons, and the St. Dominic's link; full rehearsal in the timeline. |
| 11 | The S05 research question could not be read in ≈2.5 s | 2 s silent title hold (S05 6.5 → 8.5 s). |
| 12 | The ≈40-word S12 CORRECTED overlay could not be read in a 10 s shot | ≈12-word overlay "v1 compared hand counts with frames 2.4 s off → fixed; near field redefined, recounted"; the README paragraph carries the full wording; beats retimed (4.5 / 3.5 / 2 s; superseded in the fourth review: 8 s on camera with the graphic as an inset, then the 2 s README insert). S12 stays on the never-cut list. |
| 13 | A 3 s end card (cut to 2 s by cut 1) could not be read | S20 held 6 s and added to the never-cut list; cut 1 is now an S08 stamp-hold trim. |
| 14 | S19's 20 words, three hand-offs and 1 s together did not fit 10 s | S19 11.0 s; added to the overrun plan (drop the separate all-together second first). |
| 15 | The S02 payload peel started on "only numbers", leaving ≈1.5 s for three animations | The peel starts on "It never sends a picture"; the shield and 403 land on "only numbers". |
| 16 | S14 badge not in the five-badge legend | Same fix as 7, in the storyboard and the JSON. |
| 17 | S10, S13 and S15 stacked 6-9 text blocks; S15 showed 28/40 twice | Required vs secondary lines per shot (section 6, "On-screen text load"); secondary figures moved to Q&A and the source files; duplicate stroller line removed. |
| 18 | The S03 context line sat in the lower-third, which is reserved for the speaker | Moved to the badge sub-line (new slot in the slot table); the lower-third shows [MEMBER 5] with B lit. |

**Runtime after the second review:** S05 +2.0, S11 +2.0, S14 +3.0, S19 +1.0 and S20 +3.0 s; S08, S09, S10 and S18 −0.5 s each. Total 4:10.5 → 4:19.5 (259.5 s).

**Third review fixes (previous revision, 11 findings, all should-fix; findings 1 and 8 overlap, as do 5 and 9):**

| # | issue | fix |
|---|---|---|
| 1, 8 | Text inside the captured software still used the old 30% wording. S15's St. Dominic's card shows "a full closure is the extreme case of the assumed 30% diversion" (SketchFutureCheck.tsx lines 22 and 34) right under the clicked button, and S04's evidence panel note carries "30% less inbound flow" (intervention.py line 144; quoted exactly, with a one-sentence fix, in the fourth review, finding 10). | 5A item 7: correct both strings in the code before the rehearsal (with the test at sketchfuture.test.tsx line 67 and README.md line 106). If they are not corrected, framing rules in section 6 keep both lines unreadable (S04 zoom above "Assumed effect:", S15 title-then-button pan with the crop ending under the button row). The C2b step now centres the St. Dominic's link so the title stays in frame. Added to 5F (beside README.md line 106) and the never-show list. |
| 2, 8 | The A07 fallback (taken before be83d39) shows "Assumes 30% of inbound flow diverts" | Section 6 figure notes: prefer the live capture. If A07 is used, crop S04 just under the "Current forecast" row (≈y 805) and S09 to the Decided / expired list. Same note in the S04 / S09 storyboard cells and JSON assets. |
| 3 | "The alert came with it, not before" and the chip "alert arrived with it" were too strong for two pairs of runs: run B's first CRITICAL forecast (48%, flagged) came 74 s before its crossing | Narration kept (true for run A and for confident forecasts in both runs). The chart's markers are run A's and labelled so. Chip: "Crowd built in ~3 min → first CRITICAL forecast within ~1 min of the crossing: no early warning". The run-B detail was added to the claims row and the 5F answer. |
| 4 | "We found it" in S12 was unverified, as "ourselves" was | M2's line is now "It was caught, fixed, and we published the correction." (same 9 words, true either way). "We found it, fixed it, and published the correction." is allowed only if a team member spotted the bug (5E, 5F, never-say list). |
| 5, 9 | The JSON had "Badge (top-right): ILLUSTRATION (map)" for S06; the storyboard had no badge, and "(map)" is not a defined badge text | The storyboard now has "Badge (from 4 s, over the schematic and the body diagram): ILLUSTRATION". The JSON has the same text with "top-right" added, as for S01, and "(map)" dropped. |
| 6 | 4:19.5 is 0.5 s under the 4:20 target, and at 130 wpm the cut runs ≈4:37 even after cuts 1-6 | The alternative fix was taken: re-timing from the real takes is explicitly accepted against the 5:00 hard limit, with a 4:45 ceiling. A timed read-through decides whether cuts 5 and 2 go in before recording (section 6, "Runtime control"). |
| 7 | Setup started uvicorn before the ≈1-minute dashboard build, so C2a would open at ≈14:02-14:05 sim and the click would miss S03's moment; "SIM CLOCK column" did not exist | Setup reordered: dashboard build and start, then SketchFuture, then `caffeinate`, then the backend last, with C2a launched within seconds. The timing note now reads "the simulated times in the README timing table". The JSON S03 notes were updated to match. |
| 10 | The S02 sensor_id line dropped "temporary" from docs/privacy.md | "sensor_id = a random node label for a temporary sensing position, not a person or a device serial" (storyboard and JSON). |
| 11 | The S12 README highlight had no capture method; the S08 QuickTime recording was outside the stated pipeline | New "S12 README insert" section: pandoc render, then capture.py with `scroll_to` on the tagged Correction paragraph and the highlight in post; fallback is a Pillow-typeset excerpt labelled "(excerpt)". S08 is named as the one manual capture, with an ffmpeg conform to 1920×1080 at 30 fps. |

**Options not taken (third review):**
- **Finding 6, cutting in advance:** cuts 5 and 2 were not applied before the voice shoot. They would remove the hook's "crowd building ahead" and the stated reason for the 2,000-frame benchmark. The finding's alternative (explicitly accept re-timing against the 5:00 limit) was taken instead, with the read-through as the trigger to apply them if the real pace needs it.
- **Finding 10, optional part:** "(generated once per app install)" was not added to S02's on-screen line. The 7 s shot already carries the payload card, the caption and the shield, and the extra words would not be readable. The fact stays in the S02 and S19 claims rows and in the JSON notes.

**Runtime after the third review:** unchanged, 4:19.5 (259.5 s). The S12 line keeps 9 words (guide voice 6.47 → 6.59 s in a 10 s shot), and no shot length changed.

**Fourth review fixes (this revision, 17 findings, all should-fix; findings 2 and 13 overlap, as do 7 and 12):**

| # | issue | fix |
|---|---|---|
| 1 | S11's "as many nearby people as we did by hand" claimed who made the counts; the repo does not record it (ground_truth.csv was committed only in 391da20 and 3abcd7a, both with an AI co-author line) | Narration (storyboard and JSON): "counted 97 percent as many nearby people as a careful hand count" (same 5 words; guide 16.7 → 17.0 s, still inside 18.0 s). "As we did by hand" only if a team member made the counts. Claims row, 5E (disclosure covers the counts), 5F ("Who made the 11 hand counts?" under "Who did what") and the never-say list updated. The badge's "hand-counted frames" stays (it describes the method). |
| 2, 13 | "Start C2b as soon as C2a ends (≈14:11 sim)" ignored capture.py's encode (libx264, CRF 18, ≈110 s of footage) before Chrome shuts down, and the shared DevTools port 9333: C2b would start at ≈14:15-14:21 sim, close to the St. Dominic's card's expiry (created 14:06:29 in run A; INTERVENTION_TTL_MIN = 20) | Section 6: planned capture.py change (`--port`, Chrome closed before the encode, a line printed when recording stops); C2a on `--port 9333`, C2b on `--port 9334`, launched when C2a's recording stops (≈14:12 sim → APPROVE ≈14:14, St. Dominic's ≈14:16-14:17). The "Timing" note gives the times without the change (C2a end + encode, 20-60 real s), a rehearsal line to fill in, and a decision rule: plan S15 as its own C2c from the start if the click would land after ≈14:20 or the change is not made. C2c now has its own shot file and timing. JSON S03 and S15 notes and the 13-15 Oct timeline updated. |
| 3 | Structure table row 2 still said "human APPROVE" | "APPROVE needs a person (click scripted in this recording, footer says so)". |
| 4 | S14's marker "operator approves (14:14)" implied a person | Marker "approval (scripted operator), 14:14" (storyboard and JSON; JSON line colour now "blue = approved"); never-say list. |
| 5 | S14's under-chart line set 32 vs 31 minutes next to "two pairs of runs"; the minutes exist only for the final pair | "At 14:40 · approved 0.75 vs no action 0.82 (earlier pair 0.73 vs 0.87) · this pair: 32 vs 31 min above CRITICAL". Concept limits, claims row, on-screen numbers table, 5F and the JSON notes say "final pair". |
| 6 | S11's bar title said "summed over 11 frames", but the densest pair sums only the 2 frames with ≥10 nearby people (experiments/video_eval.py, `dense = near_count >= 10`) | Title "… summed over the frames in each group …", plus a small "2 frames with ≥10 nearby people" under the densest pair (storyboard, JSON, text-load table, claims and on-screen numbers rows). |
| 7, 12 | S12 cut to the MG at 4.5 s, before M2 starts speaking (≈4.6 s at 140 wpm), so M2 was never seen speaking and the "on-camera correction by two members" claim failed | Both members stay on camera 0-8 s, framed in the left half; the timing MG runs as a Pillow split-screen inset in the right half (≈1.5-8 s); the README insert keeps its 2 s (8-10 s), cut on M2's word "correction". Storyboard, JSON, 5D, team_footage notes and the Teamwork row updated; the shot stays 10 s. |
| 8 | 5F said the old "30 percent of the incoming flow diverts" was something "the code never did", but the forecast what-if does scale inflow by 0.7 | "which the live simulation never did (the forecast what-if does scale inflow by 0.7, and the dashboard shows 'inflow ×0.7')". |
| 9 | S14 carried ≈80 words of on-screen text plus captions; one chip repeated the narration and another repeated the clock graphic | Dropped the "Senado stayed above CRITICAL" chip; merged the "no early warning" chip into the clock label; dropped "two pairs of runs"; the clock panel now enters with the third spoken limit (≈14 s) beside the chart, so its label has ≈6 s. Text-load table lists both changes; cut 6 reworded. |
| 10 | 5A item 7 misquoted the evidence note (it opens "Assumed effect (configurable prototype assumption, not validated): 30% less inbound flow."), and its proposed new opening would print "routes into the zone … less attractive" twice | 5A item 7 quotes the note exactly and the fix deletes only the clause "30% less inbound flow.", making the note one sentence. 5F, the never-say list and the JSON S04 notes quote the clause correctly. |
| 11 | S01's picture ran ahead of the words: "she sees only backs" fell on the map, and Ah Po was introduced over silhouettes | Re-timed to the words (option 2): map with Ah Po's tagged icon and the destination pin 1-6 s ("This is Ah Po, going to see the Ruins…"), eye level with her armrest in the foreground 6-9 s ("From her wheelchair, she sees only backs"), crane back up as Senado turns red 9-11.5 s ("not the crowd building ahead"); re-key to the real take. Storyboard and JSON. |
| 14 | S02 did not say which backend the app posts to, and the C2 setup did not say whether the phone joins, although runs A and B (the timing reference) had it joined at Almeida | Decision: reproduce runs A and B. The Simulator app joins every C2 run (new setup step 4), and S02 is recorded in that run during C2a's map wait. A separate no-simulation backend is only the fallback for an S02 re-shoot, never during C2; never the S08 backend. ios_capture steps 3-5, the S02 cell and the JSON S02 / S03 notes updated. |
| 15 | S02's cue times came from the guide voice; at 140 wpm "only numbers" ends at ≈17.9 s, leaving ≈0.6-1.4 s for the shield and the 403 | Cues restated at 140 wpm (≈14.9-17.0 s and ≈17.0-17.9 s) and keyed to the real take's word timestamps; if the 403 cannot hold 1 s, move 0.5 s from S04 to S02 and update all three timecode places together. The overrun table caps S04's lending at 0.5 s in all. |
| 16 | S17's B-roll was 3 s in the storyboard and 5D but 4 s in the JSON | JSON "10-13 s: B-roll; 13-18 s: counters". |
| 17 | S05's "phone on a clamp running the app" was staged unless the app is installed on a real phone (docs/testing.md §6.1); every documented run is the Simulator | The phone shows the app (Setup tab, no street clip) only if it was really installed via §6.1; otherwise its screen is off; nothing implies a field run. Storyboard, JSON, 5D, the props rule and the never-say list. |

**Options not taken (fourth review):**
- **Finding 2, shortening C2a's final wait:** kept at about 20 s. S03 needs about 8 s of Zone detail, but when a row turns confident varies by run (run B's first confident CRITICAL forecast came at 14:13:14), so a shorter wait could lose S03's "then at least one confident" moment. With the `--port` change the wait no longer delays C2b by the encode time.
- **Finding 2, S15 as C2c from the start:** not the default, because with the `--port` change C2b reaches the St. Dominic's card about 10 simulated minutes before it expires, and one fewer backend run means one fewer chance of a different scenario. It becomes the plan under the decision rule in section 6, "Timing".
- **Finding 7, compressing the MG to 2 s after a 6.5 s on-camera beat:** finding 12's split screen was taken instead. It keeps both members on camera for both lines, and the 2.4 s graphic keeps about 6.5 s on screen.
- **Finding 10, the first suggested wording** ("forecast what-if: inflow ×0.70." in place of the clause): not used, because the note's next sentence already says "The forecast what-if scales the zone's inflow by 0.70", so the panel would print it twice. The one-sentence rewrite was taken.
- **Finding 11, option 1** (eye level 1-9 s, crane up at 9 s): not taken. It leaves the map, the trilingual labels, the pin and Senado's turn to red only about 2.5 s, and gives "going to see the Ruins of St. Paul's" no destination on screen. Option 2's cost, a silent crane-up if cut 2 is applied, is noted in the S01 cell.
- **Finding 15, moving 0.5 s from S04 to S02 in advance:** not applied. At 140 wpm the 403 holds about 0.9-1.0 s, right at the threshold, so the real take decides; the move and its three timecode places are written into the S02 cell.
- **Finding 17, a laptop showing the app in the Simulator:** not taken, because [MEMBER 3] already holds a laptop; the two remaining options are combined (installed app, else screen off).

**Runtime after the fourth review:** unchanged, 4:19.5 (259.5 s); no shot length changed. The written narration stays 493 words (S11's swap is 5 words for 5). The guide reading rises from about 205.0 to 205.3 s (S11 16.7 → 17.0 s in an 18.0 s shot).
