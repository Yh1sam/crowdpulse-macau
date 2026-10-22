# CrowdPulse Macau — 18-scene reconstruction

Approved narrative and speakers; reviewed runtime **4:37 (277 s)**. The review uses synthetic guide narration and clearly labelled camera placeholders. Real voices, camera footage and school/supervisor details remain to be supplied.

| Speaker | STEMB | Focus |
|---|---|---|
| Yeung Hou Sam (Sam) | ST | 手機計數、系統整合開發、資料私隱 |
| Wong U Hei (Thomas) | SE | 計數測試、人潮預測、評估、失敗案例 |
| Ieong I Hang (Ean) | B | 使用者需要、工作人員操作流程、影片剪輯 |
| Ku Seong Lai (Curtis) | M | 健康與無障礙、輪椅使用者情境、路線模型限制 |


## N01 · 0:00.0–0:04.0 · ALL

**Team**

We are CrowdPulse Macau.

**Visual:** Four neutral camera stand-ins with the confirmed names and roles; wordmark settles with the spoken name. Clearly marked as camera placeholders.

## N02 · 0:04.0–0:24.0 · Ku Seong Lai

**A wheelchair user's view**

My focus is health and accessibility. Imagine a wheelchair user visiting the Ruins of Saint Paul's. From inside the crowd, they cannot see what is building ahead. Staff decisions about redirecting people can also affect which routes they can use.

**Visual:** Anonymous wheelchair-user illustration on the Macau schematic, followed by eye-level silhouettes. Replace the named character tag with Wheelchair user. ILLUSTRATION remains visible; this is not a real person's story.

## N03 · 0:24.0–0:41.0 · Ieong I Hang

**Why these decisions matter**

We want to help event staff make informed decisions. Why do these decisions matter? They affect people with different mobility needs. This Golden Week, police briefly controlled crowds at the Ruins on three afternoons.

**Visual:** Move from visitor to event staff. Give the spoken question a large focused beat. Show 2/3/4 October 2026 date chips with the police-release citation; do not imply an observed Macau crush injury.

## N04 · 0:41.0–0:50.0 · ALL

**Our question**

Can ordinary phones support crowd forecasts and staff decisions without sending images or identifying passers-by?

**Visual:** All four camera stand-ins remain visible while the full shared question is spoken. Large readable question; no title animation before the last words.

## N05 · 0:50.0–0:54.0 · Yeung Hou Sam

**CrowdPulse**

CrowdPulse follows the changing rhythm of crowds.

**Visual:** The street graph and crowd rhythm form the wordmark. Pulse refers to crowd changes, not a biometric measurement.

## N06 · 0:54.0–1:14.0 · Yeung Hou Sam

**A proposed supporting tool**

Macau's Public Security Police Force already runs a crowd warning system. CrowdPulse explores a portable workflow for event staff: phones send numbers, forecasts show uncertainty, and suggestions stay under review when evidence is missing.

**Visual:** Credit the existing police system first. Reveal a phone, dashboard and staff role as a coherent product composition. Proposed support; no partner yet. Preserve public-source wording without superiority claims.

## N07 · 1:14.0–1:28.0 · Yeung Hou Sam

**Count on the device**

My focus is the phone app, system integration and privacy. Here it counts people from a Toronto test clip in the iPhone Simulator, and sends numerical readings to our server.

**Visual:** Product-style phone reveal, then a magnified crop of the same actual frame's readings. Use only the masked Simulator capture. Smooth movement from full device to numerical readings; no fabricated values. Working prototype / Toronto test clip.

## N08 · 1:28.0–1:49.0 · Wong U Hei

**Inspect the forecast**

My focus is counting tests, crowd forecasting and evaluation. The phone's test feed is assigned to Almeida Ribeiro. Here, we switch to the simulated Senado scenario. Staff can inspect forecasts, confidence scores and reasons.

**Visual:** Explicit test-feed/Almeida provenance beat before switching to the simulated Senado recording. Carry the phone/readout composition across the cut. Show the live-map recording, then clearly labelled forecast and explanation details captured at separate moments. Keep the simulated-data label visible; do not imply an uninterrupted clock.

## N09 · 1:49.0–2:15.0 · Ieong I Hang

**Review before acting**

My focus is user needs, staff workflows and video editing. Here, route accessibility is unverified, so CrowdPulse blocks approval. The operator requests an on-site check, then rejects the diversion. Both actions are recorded under a self-declared name. Draft public notices disclose AI use in three languages.

**Visual:** Real updated dashboard with a seeded synthetic recommendation, explicitly labelled verification test. Show the blocked APPROVE control, request a field check, reject the diversion and show both audit events. The request is not a completed inspection. Separate labelled draft-notice insert; no public notice is issued. The demo name is fictional and self-declared.

## N10 · 2:15.0–2:34.0 · Yeung Hou Sam

**Privacy by design**

First, privacy. Staff need crowd patterns, so we chose to process video locally and send numerical observations. Our server accepts a valid reading, rejects one containing an identity field, and refuses image uploads.

**Visual:** Local processing diagram gives way to the real recorded terminal. Show recorded 202 / 422 / 403 responses at the relevant narration. Do not manufacture shell responses or claim regulatory approval.

## N11 · 2:34.0–2:52.0 · Wong U Hei

**Test the counts**

On one mall camera, the detector under-counted. After calibrating with twenty labelled frames, held-out error was about three people per frame, versus about five for a fixed guess. This calibration is not yet in the app.

**Visual:** Derived scatter/chart only; no Mall imagery. Compare held-out MAE 3.3 with fixed-count baseline 4.8, static numerals, same scale. One camera / 20 labelled frames / offline calibration / not in app.

## N12 · 2:52.0–3:19.0 · Wong U Hei

**Test the warning time**

Counting accuracy doesn't guarantee warning time. On held-out simulated days, our fifteen-minute model beat the no-change baseline. But in a fast simulated surge, the first confident warning came about a minute after the alert threshold was crossed. Staff review remains essential. Our adjusted confidence score is a review cue, not a calibrated probability.

**Visual:** Keep the simulated +15-minute scores. Highlight About 1 minute late in the Run A sampled timeline, then show the review UI. Timestamps differ by 59 simulated seconds; sampling is about 30 simulated seconds, so do not imply precise field latency. Prototype threshold is not a safety limit.

## N13 · 3:19.0–3:44.0 · Ku Seong Lai

**Compare a street-change scenario**

CrowdPulse also includes scenario simulation, to compare street changes for different mobility needs. In one full-closure stress test, twenty-four of forty simulated wheelchair journeys had no mapped step-free route in either plan. The closure did not create those twenty-four unreachable journeys. Map data and on-site checks still matter.

**Visual:** Present this as CrowdPulse's Scenario simulation feature, with no separate product logo or pitch. Show the actual branded module before the paired 40-dot cohorts. Both have24 unreachable. Explicitly label the unchanged baseline: no newly unreachable journeys in this cohort. Model results do not verify a real alternative route.

## N14 · 3:44.0–3:59.0 · Wong U Hei

**What the tests taught us**

Our tests showed why prediction quality, warning time and route accessibility need separate checks. In CrowdPulse, missing route evidence now blocks approval and leads to a recorded request for an on-site check.

**Visual:** Three familiar elements return: prediction comparison, late-warning timeline, wheelchair route. No second full demo or extra metrics.

## N15 · 3:59.0–4:18.0 · Ieong I Hang

**The next evidence**

We pre-registered our forecasting test on Melbourne pedestrian counts. On real counts, fifteen-minute F1 was 0.553, against 0.551 for no change: no clear difference. We then want a supervised pilot, with permission.

**Visual:** Short roadmap: Melbourne test result / supervised pilot proposed. The result is the pre-registered one, run once after the window closed on 22 Oct (experiments/results/melbourne/summary.md): +15 min macro-F1 model 0.553 vs no change 0.551, interval [-0.003, +0.007], so no clear difference; a moving-average baseline (0.560) led at all three horizons; the model led no-change at +5 and +10 min. Stated whichever way it came out; no claimed partner or field deployment.

## N16 · 4:18.0–4:26.0 · Ku Seong Lai

**Return to the wheelchair user**

For a wheelchair user, staff would still need to inspect the route and provide assistance on site.

**Visual:** Return to the anonymous wheelchair-user illustration, with staff checking the route. No named character, real-person claim or all-clear stamp.

## N17 · 4:26.0–4:31.0 · ALL

**People decide**

The AI recommends. A person decides.

**Visual:** All four stand-ins share the final line, with names and roles. Clear camera-placeholder label until real footage is supplied.

## N18 · 4:31.0–4:37.0 · NONE

**Credits**

(No narration.)

**Visual:** CrowdPulse wordmark, confirmed names and roles, code/evidence link and material credits. Production notes keep pending school/supervisor details; remove the pending label from the film credits. Guide/camera-placeholder labels stay while the media is still a guide version.
