# CrowdPulse Macau — 18-scene reconstruction

Approved narrative and speakers; reviewed runtime **4:15 (255 s)**. The review uses synthetic guide narration and clearly labelled camera placeholders. Real voices, camera footage and school/supervisor details remain to be supplied.

| Speaker | STEMB | Focus |
|---|---|---|
| Yeung Hou Sam | ST | Science & Technology |
| Wong U Hei | SE | Science & Engineering |
| Ieong I Hang | B | Business & Deployment |
| Ku Seong Lai | M | Health & Accessibility |


## N01 · 0:00.0–0:04.0 · ALL

**Team**

We are CrowdPulse Macau.

**Visual:** Four neutral camera stand-ins with the confirmed names and roles; wordmark settles with the spoken name. Clearly marked as camera placeholders.

## N02 · 0:04.0–0:25.0 · Ku Seong Lai

**A visitor's view**

My focus is health and accessibility. Imagine Mrs Chan, a fictional wheelchair user visiting the Ruins of Saint Paul's. From inside the crowd, she cannot see what is building ahead. Staff decisions about redirecting people can also affect which routes she can use.

**Visual:** Reuse the sourced Macau schematic, wheelchair-eye-height view and Mrs Chan choreography. ILLUSTRATION stays visible. Introduce the speaker, then let the map and eye-level view carry the story.

## N03 · 0:25.0–0:42.0 · Ieong I Hang

**Why these decisions matter**

We want to help event staff make informed decisions. Why do these decisions matter? They affect people with different mobility needs. This Golden Week, police briefly controlled crowds at the Ruins on three afternoons.

**Visual:** Move from visitor to event staff. Give the spoken question a large focused beat. Show 2/3/4 October 2026 date chips with the police-release citation; do not imply an observed Macau crush injury.

## N04 · 0:42.0–0:51.0 · ALL

**Our question**

Can ordinary phones support crowd forecasts and staff decisions without sending images or identifying passers-by?

**Visual:** All four camera stand-ins remain visible while the full shared question is spoken. Large readable question; no title animation before the last words.

## N05 · 0:51.0–0:55.0 · Yeung Hou Sam

**CrowdPulse**

CrowdPulse follows the changing rhythm of crowds.

**Visual:** The street graph and crowd rhythm form the wordmark. Pulse refers to crowd changes, not a biometric measurement.

## N06 · 0:55.0–1:13.0 · Ieong I Hang

**A proposed supporting tool**

Macau's Public Security Police Force already runs a crowd warning system. Our proposal is a temporary sensing kit and dashboard for event staff, designed to support existing work during busy events.

**Visual:** Credit the existing police system first. Reveal a phone, dashboard and staff role as a coherent product composition. Proposed support; no partner yet. Preserve public-source wording without superiority claims.

## N07 · 1:13.0–1:27.0 · Yeung Hou Sam

**Count on the device**

My focus is the phone app and counting tests. Here it counts people from a Toronto test clip in the iPhone Simulator, and sends numerical readings to our server.

**Visual:** Product-style phone reveal, then a magnified crop of the same actual frame's readings. Use only the masked Simulator capture. Smooth movement from full device to numerical readings; no fabricated values. Working prototype / Toronto test clip.

## N08 · 1:27.0–1:48.0 · Wong U Hei

**Inspect the forecast**

My focus is forecasting, system integration and evaluation. The phone's test feed is assigned to Almeida Ribeiro. Here, we switch to the simulated Senado scenario. Staff can inspect forecasts, confidence scores and reasons.

**Visual:** Explicit test-feed/Almeida provenance beat before switching to the simulated Senado recording. Carry the phone/readout composition across the cut. Show the live-map recording, then clearly labelled forecast and explanation details captured at separate moments. Keep the simulated-data label visible; do not imply an uninterrupted clock.

## N09 · 1:48.0–2:06.0 · Ieong I Hang

**Review before acting**

My focus is deployment and how event staff would use the system. An operator reviews each suggestion, approves or rejects it, and enters a name recorded with the decision. Notices come in three languages and disclose AI use.

**Visual:** Recorded operator workflow: suggestion, notices, approval and audit record. Large clean screen frame with measured camera moves. Retain Scripted click and fictional demo-operator disclosure; the name is self-declared, not authenticated.

## N10 · 2:06.0–2:25.0 · Yeung Hou Sam

**Privacy by design**

First, privacy. Staff need crowd patterns, so we chose to process video locally and send numerical observations. Our server accepts a valid reading, rejects one containing an identity field, and refuses image uploads.

**Visual:** Local processing diagram gives way to the real recorded terminal. Show recorded 202 / 422 / 403 responses at the relevant narration. Do not manufacture shell responses or claim regulatory approval.

## N11 · 2:25.0–2:43.0 · Yeung Hou Sam

**Test the counts**

On one mall camera, the detector under-counted. After calibrating with twenty labelled frames, held-out error was about three people per frame, versus about five for a fixed guess. This calibration is not yet in the app.

**Visual:** Derived scatter/chart only; no Mall imagery. Compare held-out MAE 3.3 with fixed-count baseline 4.8, static numerals, same scale. One camera / 20 labelled frames / offline calibration / not in app.

## N12 · 2:43.0–3:08.0 · Wong U Hei

**Test the warning time**

Counting accuracy doesn't guarantee warning time. On held-out simulated days, our fifteen-minute model beat the no-change baseline. But a fast simulated surge crossed our alert threshold before a confident warning. Staff review remains essential. Our adjusted confidence score is a review cue, not a calibrated probability.

**Visual:** First hold the synthetic +15 minute F1 .865/.795 comparison; accuracy96.4/94.3 and critical recall91/79 are secondary, against simulated observed labels. Always-SAFE accuracy84.6 is context. Then show the recorded late-warning example and actual review UI. Prototype threshold, not a validated safety limit. No causal improvement claim.

## N13 · 3:08.0–3:31.0 · Ku Seong Lai

**Check who can use the route**

And what about someone like Mrs Chan? In a full-closure stress test on Macau's mapped streets, twenty-four of forty simulated wheelchair journeys had no mapped step-free route, both before and after the change. We need better map data and on-site checks before treating a modelled route as suitable for real visitors.

**Visual:** Show the actual SketchFuture model capture first, then dissolve to two equal before/after 40-dot cohorts. Both already show24 unreachable; do not animate them as newly excluded by the closure. Full closure / synthetic cohort / mapped routes, not field certification. Keep OSM attribution.

## N14 · 3:31.0–3:43.0 · Wong U Hei

**What the tests taught us**

Our tests showed why prediction quality, warning time and route accessibility need separate checks. A working prototype is the start of that process.

**Visual:** Three familiar elements return: prediction comparison, late-warning timeline, wheelchair route. No second full demo or extra metrics.

## N15 · 3:43.0–3:56.0 · Ieong I Hang

**The next evidence**

Our pre-registered Melbourne forecasting test is pending. We then want a supervised pilot, with permission. Our next milestone is evidence from real operating conditions.

**Visual:** Short roadmap: Melbourne test pending / supervised pilot proposed. No held-out analysis or invented result; no claimed partner or field deployment.

## N16 · 3:56.0–4:04.0 · Ku Seong Lai

**Back to Mrs Chan**

Back to Mrs Chan: staff would still need to inspect the route and assist her on site.

**Visual:** Return to the same underlying schematic, risk still present. Staff inspect and stand beside her. No green approved route or automatic safety certification.

## N17 · 4:04.0–4:09.0 · ALL

**People decide**

The AI recommends. A person decides.

**Visual:** All four stand-ins share the final line, with names and roles. Clear camera-placeholder label until real footage is supplied.

## N18 · 4:09.0–4:15.0 · NONE

**Credits**

(No narration.)

**Visual:** Wordmark, four confirmed names/roles, code/evidence link, material credits and school/supervisor pending notice. Full six-second hold.
