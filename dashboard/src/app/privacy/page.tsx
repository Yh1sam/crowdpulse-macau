/** Privacy statement. Every line describes the code as it is; docs/privacy.md is the full reference. */
export default function Privacy() {
  return (
    <div className="max-w-3xl space-y-3 text-sm text-zinc-300">
      <h1 className="text-xl font-bold text-white">Privacy statement</h1>
      <p className="rounded-lg border border-sky-800 bg-sky-950/40 p-3 text-base text-sky-100"><b>No facial recognition. No image or video leaves the phone, and the backend stores none.</b></p>
      <h2 className="font-semibold text-white">How the system works</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>The system is designed for authorised staff to place ordinary smartphones temporarily at tourist hotspots. It has not been tested in the field in Macau.</li>
        <li>The sensor app analyses each frame <b>on the phone</b>: it detects people as anonymous boxes, counts them, and estimates a crowd density index (relative, 0–1) and the main direction and speed of movement. To estimate movement it matches box centres between consecutive frames; no box is given an identity.</li>
        <li>Each reading the phone sends is <b>numbers and short labels only</b>: an anonymous node label (<code>node-</code> plus random characters, not derived from the device), timestamp, GPS position and accuracy, compass heading, device stability, person count, density index, flow direction and speed, vision confidence, an obstruction flag, the model version and, optionally, the mode (live, video or simulated) and a zone chosen by staff.</li>
        <li>The reading&apos;s schema is closed. It has no field for images, faces, names or device identifiers, and the backend rejects a reading with any extra field (for example <code>face_id</code>) with HTTP 422.</li>
        <li>With PRIVACY_MODE on (the default, and the only supported configuration), the backend refuses any image, video or multipart upload with HTTP 403, and its frame-upload endpoint always answers 403. The phone app has no code that uploads images.</li>
      </ul>
      <h2 className="font-semibold text-white">What is stored, and for how long</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>The backend stores each reading as received, one-minute aggregates per zone, forecasts, alerts, recommendations, the audit log and each phone&apos;s latest reading, plus any manual ground-truth counts recorded through the experiments API (<code>POST /experiments/ground-truth</code>, with an optional recorder name and notes; the dashboard never calls it). No stored field identifies a passer-by.</li>
        <li>Readings and forecasts older than <b>48 hours</b> are deleted (the default, set by <code>CROWDPULSE_RETENTION_HOURS</code>). The backend checks on every 100th forecast refresh, which is every few minutes while readings arrive.</li>
        <li>Zone aggregates, alerts, recommendations, the audit log, each phone&apos;s latest reading and the ground-truth records are not deleted by that rule. How long to keep them is for the operating department to decide.</li>
      </ul>
      <h2 className="font-semibold text-white">The name of the person who decides</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>Every approve, reject and alert acknowledgement is stored with the name typed under <b>&ldquo;Deciding as&rdquo;</b>: on the recommendation or alert, and as the actor in the audit log. The backend refuses an empty name, &ldquo;operator&rdquo; and &ldquo;system&rdquo;.</li>
        <li>The name is self-declared. The prototype has no login, so the log records who the person said they were, not a checked identity. This browser keeps the name in its local storage (in memory only, if storage is blocked).</li>
        <li>These names are staff data, kept for accountability. The 48-hour deletion does not apply to them.</li>
      </ul>
      <h2 className="font-semibold text-white">Responsible AI</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>Every forecast shows its confidence, or NO DATA when a zone has too little reliable sensor data. Below the threshold (0.60, in <code>shared/config.json</code>) it is labelled <b>LOW CONFIDENCE — HUMAN REVIEW REQUIRED</b>.</li>
        <li>When several of a zone&apos;s inputs fall outside the range of the training data, or an anomaly detector flags them, the forecast carries a warning that its reliability may be reduced, and its confidence is lowered. Few sensors online, poor-quality readings or disagreeing sensors lower it too.</li>
        <li>The AI never acts on its own: it recommends, and a named person approves or rejects. In the simulation, a recommendation&apos;s effect is applied only after approval.</li>
        <li>Detour routes are scored with a penalty for stairs, steep sections and length. Each redirect recommendation says whether its route has stairs or steep sections, and redirect notices say staff can help visitors with reduced mobility.</li>
      </ul>
      <h2 className="font-semibold text-white">Telling the public</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>Public notices are drafted in Chinese, English and Portuguese, and every notice ends by saying an AI forecast is involved: <i>&ldquo;Advice from an AI crowd forecast, approved by staff.&rdquo;</i> The Chinese and Portuguese wording still needs a check by a fluent speaker.</li>
        <li>A sign at each phone saying that counting is in progress is planned, not yet made.</li>
      </ul>
      <p className="text-xs text-zinc-500">Prototype built for the Imperial College London Hackathon Hong Kong &amp; Macau 2026 · High School track · Challenge 2(c) Responsible AI. Thresholds are experimental and the crowd data shown may be simulated. The full privacy description is in <code>docs/privacy.md</code>.</p>
    </div>
  );
}
