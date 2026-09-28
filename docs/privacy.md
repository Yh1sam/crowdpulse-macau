# Privacy architecture

Privacy is a hard requirement of CrowdPulse, enforced in code, not only in policy.

## Principles

1. **Raw camera frames never leave the phone.** Detection runs on-device (Apple Vision `VNDetectHumanRectanglesRequest`); the app has no code path that uploads images. Debug snapshots exist only on-screen.
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

## What is never collected

Images, video, faces, face embeddings, names, MAC/Bluetooth/Wi-Fi identifiers, IMEI/serial numbers, per-person trajectories, demographic attributes.

## Residual risks and mitigations

- *A phone is stolen while sensing.* Nothing identifiable is stored on it; the buffer holds numbers only.
- *Counting at a sensitive location could reveal attendance.* Deployment is restricted to public tourist spaces by authorised staff; zone aggregation further blurs single-sensor views.
- *Operator misuse of the camera preview.* The preview is on-device and cannot be recorded by the app; a physical sign should indicate active crowd sensing.

The dashboard shows this statement on its Privacy page.
