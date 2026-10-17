# Privacy architecture

Privacy is a hard requirement of CrowdPulse, enforced in code, not only in policy.

## Principles

1. **Raw camera frames never leave the phone.** Person detection runs on the device. The default detector is YOLO11n, a 5 MB CoreML model bundled with the app (`CoreMLPersonDetector` in `ios/CrowdPulseSensor/Sources/Services/PersonDetector.swift`). Apple Vision's built-in `VNDetectHumanRectanglesRequest` is the fallback: it can be chosen on the app's Setup page, and the app uses it automatically if the YOLO11n model is missing from the bundle (`SensorNode.swift`). The app has no code path that uploads images. Debug snapshots exist only on-screen.
2. **No facial recognition, no face embeddings, no biometrics.** Person detection produces anonymous rectangles that are discarded after counting and motion estimation.
3. **No persistent pedestrian identity.** Frame-to-frame motion is estimated from box-centroid displacement within ~0.5 s; nothing is tracked across seconds, frames are not linked to earlier frames, and phones never share per-person data.
4. **Numerical metadata only.** The observation schema (`shared/schemas/sensor_observation.schema.json`) is closed: `additionalProperties: false`, and the backend's Pydantic model uses `extra="forbid"`. A payload with e.g. `face_id` is rejected with HTTP 422 (tested).
5. **Anonymous node IDs.** `node-xxxx` labels are random and identify a temporary sensing position, not a person or a device serial.
6. **PRIVACY_MODE = true by default** (`shared/config.json`). While on, the backend rejects any `multipart/*`, `image/*` or `video/*` POST with HTTP 403 and the `/sensor/frame` endpoint is permanently disabled. There is no storage for images anywhere in the schema.
7. **Minimal retention.** Raw observations and predictions are pruned after 48 h (`CROWDPULSE_RETENTION_HOURS`); zone states are one-minute aggregates.
8. **Location is the sensor's, not people's.** GPS/heading describe where the phone stands and which way it faces.

## What is transmitted

| field | purpose |
|---|---|
| sensor_id, timestamp, model_version | provenance |
| latitude, longitude, location_accuracy_m, heading_deg | where the sensor is and what it looks at |
| device_motion_stability, camera_obstructed, vision_confidence | reliability of the observation |
| person_count, estimated_density (relative 0–1) | crowd level |
| flow_direction_deg, flow_speed_mps | aggregate movement |

## What is never collected about passers-by

Images, video, faces, face embeddings, names, MAC/Bluetooth/Wi-Fi identifiers, IMEI/serial numbers, per-person trajectories, demographic attributes.

## Names the system stores: the person who decides (and an optional ground-truth recorder)

Every approve, reject and alert acknowledgement carries the name typed in the dashboard's **"Deciding as"** field (`dashboard/src/components/OperatorField.tsx`). The backend refuses an empty name, "operator" and "system" with HTTP 422 (`DecisionIn` in `backend/app/schemas.py`) and writes the name as `decided_by` and as the audit-log actor (`decide_intervention` in `backend/app/services/engine.py`), so the log says who decided. This is staff data, kept for accountability:

- The name is self-declared. The prototype has no login, so it records who the person said they were, not a checked identity.
- The audit log is not pruned by the 48 h retention above; how long it is kept is for the operating department to set.
- The dashboard keeps the name in that browser's `localStorage` (in memory only if storage is blocked).
- The only other name field is `recorded_by` on manual ground-truth counts (`POST /experiments/ground-truth`, API only, for controlled experiments; optional, with free-text notes). Those records are not pruned either and are exported by `/export/ground_truth.csv`. Record a role or pseudonym there, not a passer-by's details.

## Telling the public

- **Every public notice says an AI forecast is involved.** The system appends `AI_NOTICE` (`backend/app/services/intervention.py`) to every non-empty notice it drafts, in all three languages: "Advice from an AI crowd forecast, approved by staff." / "此建議來自人工智能人流預測，並經工作人員批准。" / "Recomendação baseada numa previsão de afluência feita por inteligência artificial, aprovada pelo pessoal." The Chinese and Portuguese wording still needs a check by a fluent team member. Tested by `test_public_notices_say_ai_is_involved_and_staff_approved` in `backend/tests/test_api.py`.
- **A sign at each phone (planned, not yet made).** A draft trilingual sign (Chinese, Portuguese, English) is in [docs/research/brief-evidence.md, section 6](research/brief-evidence.md#6-legal-basis-and-telling-the-public-to-be-confirmed-with-the-authority-not-a-compliance-claim). It says that phones count people on the device, that images are not stored or sent, that the AI only recommends and staff decide, and it names the responsible body and a contact. The wording and format are **to be confirmed with the authority (the Personal Data Protection Bureau) and the operating department; this is not a compliance claim.** The same section explains why Macau's Personal Data Protection Act (Law 8/2005) probably applies even though no image is stored (running a counting model on camera frames is likely "processing"; a team inference), and what the law asks for: telling people who the controller is and why, and notifying the authority within 8 days of starting.
- The dashboard shows a short privacy statement on its Privacy page (`dashboard/src/app/privacy/page.tsx`); where the two differ, this document is the reference.

## Residual risks and mitigations

- *A phone is stolen while sensing.* Nothing identifiable is stored on it; the buffer holds numbers only.
- *Counting at a sensitive location could reveal attendance.* Deployment is restricted to public tourist spaces by authorised staff; zone aggregation further blurs single-sensor views. Near a place of worship (for example St Dominic's Church) the sensitive-data rules of Law 8/2005 need the authority's view first (brief-evidence.md, section 6).
- *Operator misuse of the camera preview.* The preview is on-device and cannot be recorded by the app; the planned sign tells people that counting is in progress.
- *A wrong or borrowed name in "Deciding as".* Without a login the log cannot prove who decided. A deployment would need real operator accounts; the prototype has none and does not claim to check identity.
- *Faces in our published material.* The public-domain street clip used for testing shows real passers-by. Faces are pixelated in the published detector figure (`experiments/results/video/detector_overlay.png`) and in the app screenshots and 30 s recording in `experiments/results/simulation_run/` (`experiments/mask_faces.py`, head boxes in `experiments/mask_faces_boxes.json`), and `experiments/video_eval.py` masks the frame before it plots `detector_overlay.png`.
