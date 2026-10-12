# Round-one proposal (150-word limit)

Draft of 2026-10-12, 149 words (counted with `wc -w`). Submission deadline: 25 October 2026, 23:59 HKT/MST.

Every Golden Week, the Ruins of St. Paul's and Senado Square become dangerously crowded. Macau has forecast attraction crowds hours to days ahead; operators also need the next fifteen minutes, street by street.

CrowdPulse turns ordinary smartphones, placed temporarily by staff, into anonymous crowd sensors. Each phone counts people on-device and sends only numbers, never images or identities. A model forecasts congestion 5, 10 and 15 minutes ahead with a confidence score; uncertain forecasts go to human review. Operators approve every action, such as detours that avoid stairs for elderly and wheelchair users, announced in Chinese, English and Portuguese.

On held-out simulated days, 15-minute forecasts beat a "no change" baseline (F1 0.865 vs 0.795). On 2,000 annotated real crowd images, calibrating the camera with 20 labelled frames cut counting error from 13 to about 3 people per frame. Next: testing forecasts on real pedestrian-sensor data, then a street pilot.

## Where each claim comes from

| claim | source |
|---|---|
| Macau has forecast attraction crowds hours to days ahead | Macao SAR government news, 30 April 2019: MGTO's smart visitor-flow application forecasts 20 attractions 4 h, 24 h and 7 days ahead (<https://www.gov.mo/en/?p=111714>). Whether it still runs today was not confirmed. |
| only numbers leave the phone, never images or identities | closed observation schema (`extra="forbid"`), media uploads refused with 403, iOS payload of numbers only; tests in `backend/tests/test_api.py` |
| forecasts 5, 10, 15 min ahead with confidence; uncertain ones go to human review | `backend/app/services/prediction.py`, `shared/config.json` (threshold 0.60), dashboard *LOW CONFIDENCE — HUMAN REVIEW REQUIRED* |
| operators approve every action; detours avoid stairs; zh/en/pt notices | `backend/app/services/intervention.py` (accessibility penalty, notices), approve/reject audit log |
| F1 0.865 vs 0.795 | `ml/models/metrics.json`, +15 min macro-F1 vs persistence on synthetic held-out days |
| 2,000 annotated images; error from 13 to about 3 people per frame with 20 labelled frames | `experiments/results/mall/summary.md` (Mall dataset; raw held-out MAE 13.42, calibrated 3.33; one camera, post-hoc analysis) |
| testing forecasts on real pedestrian-sensor data | Melbourne per-minute counts archived since 2026-10-12 (`experiments/datasets/melbourne/README.md`); analysis not yet done |
