export default function Privacy() {
  return (
    <div className="max-w-3xl space-y-3 text-sm text-zinc-300">
      <h1 className="text-xl font-bold text-white">Privacy statement</h1>
      <p className="rounded-lg border border-sky-800 bg-sky-950/40 p-3 text-base text-sky-100"><b>No facial recognition. No identifiable video is transmitted or stored.</b></p>
      <h2 className="font-semibold text-white">How the system works</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>Authorised staff temporarily place ordinary smartphones at tourist hotspots. Each phone analyses its own camera frames <b>on the device</b>.</li>
        <li>The phone detects people as anonymous boxes, counts them, estimates crowd density (a relative 0–1 index, not persons per m²) and the dominant movement direction and speed.</li>
        <li>Only <b>numbers</b> leave the phone: timestamp, GPS position and accuracy, compass heading, device stability, person count, density index, flow direction and speed, vision confidence, an obstruction flag and a model version.</li>
        <li>Raw frames are never uploaded. In PRIVACY_MODE (the default, and the only supported configuration) the backend rejects any image or video upload with HTTP 403 and the data schema forbids extra fields.</li>
        <li>Sensor node IDs are random labels (e.g. <code>node-a1f3</code>) that identify a temporary position, not a person or a device serial number.</li>
        <li>No face embeddings, biometrics, names, MAC addresses or persistent pedestrian identifiers exist anywhere in the pipeline. Individuals are never tracked across frames or between phones.</li>
        <li>Stored data is numerical, aggregated per zone and per minute, and pruned after 48 hours by default.</li>
      </ul>
      <h2 className="font-semibold text-white">Responsible AI</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>Every forecast shows its confidence. Below the operator threshold it is labelled <b>LOW CONFIDENCE — HUMAN REVIEW REQUIRED</b>.</li>
        <li>Unusual conditions (rain, closures, sensor failure, extreme values) trigger a warning that the prediction may be less reliable.</li>
        <li>The AI never acts on its own: it recommends, and a human operator approves or rejects. Decisions are recorded in an audit log.</li>
        <li>Recommendations include an accessibility check so that elderly and reduced-mobility visitors are not forced onto stairs or long detours, and public notices are provided in Chinese, English and Portuguese.</li>
      </ul>
      <p className="text-xs text-zinc-500">Prototype built for the Imperial College London Global Hackathon 2026 (High School Track, Responsible AI). Thresholds are experimental and the crowd data shown may be simulated.</p>
    </div>
  );
}
