# Round-one proposal (150-word limit)

Draft of 2026-10-20, 144 words (counted with `wc -w`). Submission deadline: 25 October 2026, 23:59 HKT/MST.

In Golden Week 2026, police briefly controlled crowds at the Ruins of St. Paul's on three afternoons. They already have a crowd warning system.

CrowdPulse Macau explores a portable workflow for event staff. Phones count people on-device and send numbers, without images or identities. Forecasts cover 5-15 minutes, show confidence and reasons, and flag uncertainty for review.

CrowdPulse includes scenario simulation to compare street changes. Map data and models are not field verification: unverified diversions cannot be approved. Operators can request a field check or reject suggestions, with actions logged under self-declared names. Draft notices disclose AI use in Chinese, English and Portuguese.

On held-out simulated days, 15-minute forecasts score macro-F1 0.865 versus 0.795 for no change (accuracy 96.4% versus 94.3%). A fast simulated surge produced a confident warning about a minute late. Next: the pre-registered Melbourne test, then a supervised pilot with permission.

## Where each claim comes from

| claim | source |
|---|---|
| in Golden Week 2026, the Public Security Police briefly imposed crowd control at the Ruins of St. Paul's on three afternoons | Public Security Police Force via the Government Information Bureau, 8 Oct 2026: "先後於10月2日至4日下午在大三巴短暫實施人潮管制措施" (crowd control briefly imposed at the Ruins on the afternoons of 2-4 Oct; <https://www.gcs.gov.mo/news/detail/zh-hant/N26JHjeU3y>). The same measure ran on the afternoons of 3-5 Oct 2024 (<https://www.gcs.gov.mo/news/detail/zh-hant/N24JHSmry5>). docs/research/brief-evidence.md, section 1 |
| they (the Public Security Police) already run a "crowd forecast and early-warning system" there | The system's official name, 人流預測預警系統, in quotation marks because official replies describe what it does today as real-time density monitoring with alerts, with zone-level forecasting planned (Security Secretariat reply, 28 Jan 2026, <https://www.al.gov.mo/uploads/attachment/2026-02/0deba43cc8fb4c29b0f91b919a1fde7f.pdf>). It was set up "於大三巴周邊、新馬路一帶和關閘廣場" (around the Ruins, along Almeida Ribeiro and at Border Gate Square): Security Secretariat reply to the Legislative Assembly, 18 Jan 2023 (<https://al.gov.mo/uploads/attachment/2023-02/1507663db7492e369a.pdf>). The 2026 Policy Address annex (PDF p.108) says the police will optimise and expand it (<https://www.gov.mo/zh-hant/wp-content/uploads/sites/4/2025/11/2026_policy_cn.pdf>). Its forecast horizon, method and accuracy are not published, so the proposal does not claim it lacks short-horizon forecasts. docs/research/brief-evidence.md, sections 3-4 |
| CrowdPulse proposes movable phones (placed temporarily by staff) | Phones on temporary mounts, moved between events, are the design's operating model (`docs/deployment.md`, "Operational model"); not yet field-tested |
| only numbers leave the phone, never images or identities | closed observation schema (`extra="forbid"`), media uploads refused with 403, iOS payload of numbers only; tests in `backend/tests/test_api.py` |
| forecasts 5-15 minutes ahead (5, 10, 15) with a confidence score; uncertain forecasts get human review | `backend/app/services/prediction.py`, `shared/config.json` (threshold 0.60), dashboard *LOW CONFIDENCE — HUMAN REVIEW REQUIRED* |
| unverified diversions blocked; field-check requests and rejection logged under self-declared names | `backend/app/services/route_review.py`, `backend/app/services/engine.py`, `backend/tests/test_route_review.py`; the request is not a completed inspection or authenticated identity |
| scenario simulation is a CrowdPulse feature | Street-change model in `sketchfuture/`; full-closure stress test, not verification of an actual alternative route |
| draft zh/en/pt notices disclose AI use | `backend/app/services/intervention.py`, dashboard labels them Draft / not for publication |
| signs would disclose AI use | a plan: the draft trilingual sign in `docs/research/brief-evidence.md`, section 6 (to be confirmed with the Personal Data Protection Bureau and the operating department). Separately, every public notice the system drafts ends "Advice from an AI crowd forecast, approved by staff." (`backend/app/services/intervention.py`) |
| F1 0.865 vs 0.795; accuracy 96.4% vs 94.3% | `ml/models/metrics.json`, +15 min on synthetic held-out days: macro-F1 0.865 vs persistence 0.795; accuracy 0.9636 vs persistence 0.9426. Most minutes are SAFE, so always guessing SAFE would score 0.846 (SAFE support 14,505 of 17,152); that is why macro-F1 leads. Intervals: `experiments/results/uncertainty/summary.md` |
| a fast simulated surge turned critical before any confident forecast said so | `experiments/results/simulation_run/README.md`: the first confident (≥ 60%) CRITICAL forecast came at 14:09:08 in run A and 14:13:14 in run B, after the true density crossed CRITICAL at 14:08:09 and 14:09:20 ("No early warning in this scenario") |
| 2,000 annotated mall-camera frames; error from 13 to about 3 people per frame with 20 labelled frames | `experiments/results/mall/summary.md` (Mall dataset; raw held-out MAE 13.42, calibrated 3.33; one camera, post-hoc analysis) |
| next: real pedestrian-sensor data | Melbourne pedestrian counts (per minute or per 5 minutes) archived since 2026-10-12 (`experiments/datasets/melbourne/README.md`); the analysis is pre-registered in that README before its test days (18-22 Oct 2026, Melbourne time) and not yet run |
