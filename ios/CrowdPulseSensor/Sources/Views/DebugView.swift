import SwiftUI

struct DebugView: View {
    @EnvironmentObject var node: SensorNode
    @EnvironmentObject var settings: SensorSettings

    var body: some View {
        NavigationStack {
            List {
                Section("Motion") {
                    row("accelerometer (g)", String(format: "%.2f  %.2f  %.2f", node.motion.accel.x, node.motion.accel.y, node.motion.accel.z))
                    row("gyroscope (rad/s)", String(format: "%.2f  %.2f  %.2f", node.motion.gyro.x, node.motion.gyro.y, node.motion.gyro.z))
                    row("stability score", String(format: "%.3f", node.motion.stability))
                }
                Section("Location") {
                    row("lat / lon", String(format: "%.5f, %.5f", node.location.latitude, node.location.longitude))
                    row("GPS accuracy", String(format: "±%.1f m", node.location.accuracyM))
                    row("heading", String(format: "%.1f° (±%.0f)", node.location.headingDeg, node.location.headingAccuracy))
                }
                Section("Vision") {
                    row("detector", node.vision.detector.identifier)
                    if let err = node.latest?.inferenceError { row("inference error", err) }
                    row("frame rate", String(format: "%.1f FPS", node.latest?.fps ?? 0))
                    row("inference latency", String(format: "%.0f ms", node.latest?.latencyMs ?? 0))
                    row("detections", "\(node.latest?.personCount ?? 0)")
                    row("box area fraction", String(format: "%.3f", node.latest?.boxAreaFraction ?? 0))
                    row("mean brightness", String(format: "%.2f", node.latest?.meanBrightness ?? 0))
                    row("flow (image)", node.latest?.flowImageDeg.map { String(format: "%.0f° · %.3f w/s · conf %.2f", $0, node.latest?.flowNormPerSec ?? 0, node.latest?.flowConfidence ?? 0) } ?? "–")
                }
                Section("Upload") {
                    row("status", node.uploader.lastStatus)
                    row("sent / failed / buffered", "\(node.uploader.sent) / \(node.uploader.failed) / \(node.uploader.buffered)")
                    row("server time", node.uploader.lastServerTime ?? "–")
                    row("observations built", "\(node.observationsBuilt)")
                }
                Section("Last observation (exact payload)") {
                    Text(payload).font(.system(.caption2, design: .monospaced))
                }
            }
            .navigationTitle("Debug")
        }
    }

    private var payload: String {
        guard let o = node.lastObservation, let d = try? SensorObservation.encoder.encode(o), let s = String(data: d, encoding: .utf8) else { return "–" }
        return s
    }

    private func row(_ k: String, _ v: String) -> some View { HStack { Text(k); Spacer(); Text(v).foregroundStyle(.secondary).font(.system(.body, design: .monospaced)).multilineTextAlignment(.trailing) } }
}
