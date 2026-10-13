# Round-one proposal (150-word limit)

Draft of 2026-10-13, 149 words (counted with `wc -w`). Submission deadline: 25 October 2026, 23:59 HKT/MST.

In Golden Week 2026, police briefly imposed crowd control at the Ruins of St. Paul's on three afternoons; in 2025, crowds surged back soon after control ended. Police already run a "crowd forecast and early-warning system" there. CrowdPulse proposes movable sensors: smartphones placed temporarily by staff.

Each phone counts people on-device and sends only numbers, never images or identities. A model forecasts congestion 5, 10 and 15 minutes ahead with a confidence score; uncertain forecasts go to human review. Operators approve every action, such as detours that minimise stairs for elderly and wheelchair users, announced in Chinese, English and Portuguese.

On held-out simulated days, 15-minute forecasts beat a "no change" baseline (F1 0.865 vs 0.795). On 2,000 annotated mall-camera frames, calibrating the camera with 20 labelled frames cut counting error from 13 to about 3 people per frame. Next: testing forecasts on real pedestrian-sensor data, then a street pilot.

## Where each claim comes from

| claim | source |
|---|---|
| in Golden Week 2026, police briefly imposed crowd control at the Ruins of St. Paul's on three afternoons | Public Security Police Force via the Government Information Bureau, 8 Oct 2026: "先後於10月2日至4日下午在大三巴短暫實施人潮管制措施" (crowd control briefly imposed at the Ruins on the afternoons of 2-4 Oct; <https://www.gcs.gov.mo/news/detail/zh-hant/N26JHjeU3y>). The same measure ran on the afternoons of 3-5 Oct 2024 (<https://www.gcs.gov.mo/news/detail/zh-hant/N24JHSmry5>). docs/research/brief-evidence.md, section 1 |
| in 2025, crowds surged back soon after control ended | Macao Daily News, 5 Oct 2025: control on Rua de S. Paulo, the street up to the Ruins, ran 13:00-15:40; then "不久，旅客大軍再次回湧" (soon the crowds surged back) and control was reimposed 16:25-17:25 (<https://www.macaodaily.com/html/2025-10/05/content_1861519.htm>). docs/research/brief-evidence.md, section 1 |
| police already run a "crowd forecast and early-warning system" there | The system's official name, 人流預測預警系統, in quotation marks because official replies describe what it does today as real-time density monitoring with alerts, with zone-level forecasting planned (Security Secretariat reply, 28 Jan 2026, <https://www.al.gov.mo/uploads/attachment/2026-02/0deba43cc8fb4c29b0f91b919a1fde7f.pdf>). It was set up "於大三巴周邊、新馬路一帶和關閘廣場" (around the Ruins, along Almeida Ribeiro and at Border Gate Square): Security Secretariat reply to the Legislative Assembly, 18 Jan 2023 (<https://al.gov.mo/uploads/attachment/2023-02/1507663db7492e369a.pdf>). The 2026 Policy Address annex (PDF p.108) says the police will optimise and expand it (<https://www.gov.mo/zh-hant/wp-content/uploads/sites/4/2025/11/2026_policy_cn.pdf>). Its forecast horizon, method and accuracy are not published, so the proposal does not claim it lacks short-horizon forecasts. docs/research/brief-evidence.md, sections 3-4 |
| CrowdPulse proposes movable sensors: smartphones placed temporarily by staff | Phones on temporary mounts, moved between events, are the design's operating model (`docs/deployment.md`, "Operational model"); not yet field-tested |
| only numbers leave the phone, never images or identities | closed observation schema (`extra="forbid"`), media uploads refused with 403, iOS payload of numbers only; tests in `backend/tests/test_api.py` |
| forecasts 5, 10, 15 min ahead with confidence; uncertain ones go to human review | `backend/app/services/prediction.py`, `shared/config.json` (threshold 0.60), dashboard *LOW CONFIDENCE — HUMAN REVIEW REQUIRED* |
| operators approve every action; detours minimise stairs; zh/en/pt notices | `backend/app/services/intervention.py` (a stair penalty, not a ban: a card says when its route still has stairs; notices), approve/reject audit log |
| F1 0.865 vs 0.795 | `ml/models/metrics.json`, +15 min macro-F1 vs persistence on synthetic held-out days |
| 2,000 annotated mall-camera frames; error from 13 to about 3 people per frame with 20 labelled frames | `experiments/results/mall/summary.md` (Mall dataset; raw held-out MAE 13.42, calibrated 3.33; one camera, post-hoc analysis) |
| testing forecasts on real pedestrian-sensor data | Melbourne per-minute counts archived since 2026-10-12 (`experiments/datasets/melbourne/README.md`); analysis not yet done |
