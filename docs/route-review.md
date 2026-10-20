# CrowdPulse route review — 20 October 2026

CrowdPulse proposes a diversion but does not approve it when route accessibility has not been verified. The current prototype has no workflow for accepting and validating field-inspection evidence, so **all `redirect_flow` approvals remain blocked**. Map stair/steep flags and a runnable scenario simulation cannot remove the block.

The API supplies `approval_blocked` and `approval_block_reason` as derived response fields. The backend applies the policy independently when an approval is posted. A legacy row, a missing map crosswalk, a `verified` flag supplied by a client, or stored metadata claiming a model check passed does not override it. Non-diversion action types retain the existing human approval workflow.

`POST /interventions/{id}/request-field-check` requires a nonempty self-declared operator name and a pending, unexpired diversion. It records a timestamp, requester and note in the intervention and a `route_field_check_requested` audit event. Retries return the original request without duplicate events. This is a **request**, not dispatch to a real team, an inspection result, authenticated identity or permission to approve. Rejection remains available and records the missing-evidence reason. Neither blocked approval nor a field-check request changes the simulated crowd.

The UI shows **ACCESSIBILITY NOT VERIFIED**, a disabled **APPROVE**, **REQUEST FIELD CHECK** and **REJECT**. After a request and page reload, it still says unverified. Public-message templates are marked **Draft — not for publication**.

Scenario simulation is a CrowdPulse feature, implemented in the existing `sketchfuture/` directory. Its full-closure stress test compares modelled journeys; it does not independently certify the proposed alternative route or enable approval. The separate product branding was removed from the interface and current pitch.

## Validation

- Python suite: **60 passed**, including direct API bypass attempts, supported/unsupported corridor inputs, legacy/self-declared metadata, request persistence/idempotency, rejection, expiry, operator-name validation and non-diversion approval.
- Dashboard: **26 passed**, including mounted-page cases where even a false allow flag cannot enable a diversion; requests and rejections send the self-declared name and reason.
- Scenario feature: **33 passed**; production build passed. Dashboard production build passed. Existing Vite config and large map-bundle advisories remain.
- Actual production UI + backend: typed a valid name, confirmed diversion approval stayed disabled, attempted a direct API approval (409), requested a field check, reloaded, confirmed it remained unverified, rejected it, and checked the persisted audit and `effect_applied=false`.

Screenshots are local under `output/playwright/`. The new N09 recording uses an isolated database seeded with explicit synthetic prediction inputs by `video/seed_review_demo.py`; the API, disabled controls, request, rejection and audit are real executions. It is labelled as a seeded verification test and is not evidence of a model inference or field deployment. The new model-feature capture uses the existing deterministic cohort and actual scenario interface.

The old `experiments/results/simulation_run/` results describe earlier approved-simulation experiments. Their numerical results have not been regenerated or relabelled as outcomes of the new policy. Melbourne held-out data was not opened or analysed for this change.
