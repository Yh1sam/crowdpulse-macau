# CrowdPulse Macau — 18-scene reconstruction

Approved narrative and speakers; reviewed runtime **4:31 (271 s)**. The review uses synthetic guide narration and clearly labelled camera placeholders. Real voices, camera footage and school/supervisor details remain to be supplied.

| Speaker | STEMB | Focus |
|---|---|---|
| Yeung Hou Sam (Sam) | ST | 手機計數、系統整合開發、資料私隱 |
| Wong U Hei (Thomas) | SE | 計數測試、人潮預測、評估、失敗案例 |
| Ieong I Hang (Ean) | B | 使用者需要、工作人員操作流程、影片剪輯 |
| Ku Seong Lai (Curtis) | M | 健康與無障礙、輪椅使用者情境、路線模型限制 |


| Scene | Time | Speaker | Exact narration |
|---|---|---|---|
| N01 | 0:00.0–0:04.0 | ALL | We are CrowdPulse Macau. |
| N02 | 0:04.0–0:24.0 | Ku Seong Lai | My focus is health and accessibility. Imagine a wheelchair user visiting the Ruins of Saint Paul's. From inside the crowd, they cannot see what is building ahead. Staff decisions about redirecting people can also affect which routes they can use. |
| N03 | 0:24.0–0:41.0 | Ieong I Hang | We want to help event staff make informed decisions. Why do these decisions matter? They affect people with different mobility needs. This Golden Week, police briefly controlled crowds at the Ruins on three afternoons. |
| N04 | 0:41.0–0:50.0 | ALL | Can ordinary phones support crowd forecasts and staff decisions without sending images or identifying passers-by? |
| N05 | 0:50.0–0:54.0 | Yeung Hou Sam | CrowdPulse follows the changing rhythm of crowds. |
| N06 | 0:54.0–1:14.0 | Ieong I Hang | Macau's Public Security Police Force already runs a crowd warning system. CrowdPulse explores a portable workflow for event staff: phones send numbers, forecasts show uncertainty, and suggestions stay under review when evidence is missing. |
| N07 | 1:14.0–1:28.0 | Yeung Hou Sam | My focus is the phone app, system integration and privacy. Here it counts people from a Toronto test clip in the iPhone Simulator, and sends numerical readings to our server. |
| N08 | 1:28.0–1:49.0 | Wong U Hei | My focus is counting tests, crowd forecasting and evaluation. The phone's test feed is assigned to Almeida Ribeiro. Here, we switch to the simulated Senado scenario. Staff can inspect forecasts, confidence scores and reasons. |
| N09 | 1:49.0–2:15.0 | Ieong I Hang | My focus is user needs, staff workflows and video editing. Here, route accessibility is unverified, so CrowdPulse blocks approval. The operator requests an on-site check, then rejects the diversion. Both actions are recorded under a self-declared name. Draft public notices disclose AI use in three languages. |
| N10 | 2:15.0–2:34.0 | Yeung Hou Sam | First, privacy. Staff need crowd patterns, so we chose to process video locally and send numerical observations. Our server accepts a valid reading, rejects one containing an identity field, and refuses image uploads. |
| N11 | 2:34.0–2:52.0 | Wong U Hei | On one mall camera, the detector under-counted. After calibrating with twenty labelled frames, held-out error was about three people per frame, versus about five for a fixed guess. This calibration is not yet in the app. |
| N12 | 2:52.0–3:19.0 | Wong U Hei | Counting accuracy doesn't guarantee warning time. On held-out simulated days, our fifteen-minute model beat the no-change baseline. But in a fast simulated surge, the first confident warning came about a minute after the alert threshold was crossed. Staff review remains essential. Our adjusted confidence score is a review cue, not a calibrated probability. |
| N13 | 3:19.0–3:44.0 | Ku Seong Lai | CrowdPulse also includes scenario simulation, to compare street changes for different mobility needs. In one full-closure stress test, twenty-four of forty simulated wheelchair journeys had no mapped step-free route in either plan. The closure did not create those twenty-four unreachable journeys. Map data and on-site checks still matter. |
| N14 | 3:44.0–3:59.0 | Wong U Hei | Our tests showed why prediction quality, warning time and route accessibility need separate checks. In CrowdPulse, missing route evidence now blocks approval and leads to a recorded request for an on-site check. |
| N15 | 3:59.0–4:12.0 | Ieong I Hang | We pre-registered our forecasting test on Melbourne pedestrian counts. We then want a supervised pilot, with permission. Our next milestone is evidence from real operating conditions. |
| N16 | 4:12.0–4:20.0 | Ku Seong Lai | For a wheelchair user, staff would still need to inspect the route and provide assistance on site. |
| N17 | 4:20.0–4:25.0 | ALL | The AI recommends. A person decides. |
| N18 | 4:25.0–4:31.0 | NONE |  |
