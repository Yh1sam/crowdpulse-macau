import Foundation
import Combine

/// Operator-configured settings for this sensor node. Persisted in UserDefaults.
final class SensorSettings: ObservableObject {
    /// `model_version` sent with every observation: app pipeline version + active detector.
    static func modelVersion(detector: String) -> String { "ios-\(detector)-0.2" }

    @Published var backendURL: String { didSet { save() } }
    @Published var sensorId: String { didSet { save() } }
    @Published var sensorName: String { didSet { save() } }
    @Published var zoneHint: String { didSet { save() } }
    /// Number of people that would fill this camera's view (calibrated by the operator).
    /// Defines the relative density index for this node: density = count / visibleCapacity.
    @Published var visibleCapacity: Double { didSet { save() } }
    /// Approximate real-world width covered by the frame at pedestrian distance (m); used only for a rough speed estimate.
    @Published var visibleWidthMeters: Double { didSet { save() } }
    @Published var intervalSeconds: Double { didSet { save() } }
    @Published var mode: SensorMode { didSet { save() } }
    @Published var detector: DetectorChoice { didSet { save() } }

    enum SensorMode: String, CaseIterable, Identifiable, Codable {
        case live, video, simulated
        var id: String { rawValue }
    }

    /// On-device person detector. YOLO11n is the default (measured: finds ~97% of near-field people on
    /// the CC0 crossing clip vs ~55% for Apple's built-in detector; experiments/results/video/summary.md).
    enum DetectorChoice: String, CaseIterable, Identifiable, Codable {
        case yolo11n, apple
        var id: String { rawValue }
        var label: String { self == .yolo11n ? "YOLO11n (CoreML)" : "Apple built-in" }
    }

    private let defaults: UserDefaults
    private var loading = true

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        backendURL = defaults.string(forKey: "backendURL") ?? "http://localhost:8000"
        sensorId = defaults.string(forKey: "sensorId") ?? SensorSettings.randomNodeId()
        sensorName = defaults.string(forKey: "sensorName") ?? "Sensor node"
        zoneHint = defaults.string(forKey: "zoneHint") ?? ""
        visibleCapacity = defaults.object(forKey: "visibleCapacity") as? Double ?? 40
        visibleWidthMeters = defaults.object(forKey: "visibleWidthMeters") as? Double ?? 8
        intervalSeconds = defaults.object(forKey: "intervalSeconds") as? Double ?? 3
        mode = SensorMode(rawValue: defaults.string(forKey: "mode") ?? "") ?? .live
        detector = DetectorChoice(rawValue: defaults.string(forKey: "detector") ?? "") ?? .yolo11n
        loading = false
        save()
    }

    /// Anonymous node id: `node-` + 6 random hex characters. Not derived from the device.
    static func randomNodeId() -> String {
        let hex = "0123456789abcdef"
        return "node-" + String((0..<6).map { _ in hex.randomElement()! })
    }

    func regenerateId() { sensorId = SensorSettings.randomNodeId() }

    private func save() {
        guard !loading else { return }
        defaults.set(backendURL, forKey: "backendURL")
        defaults.set(sensorId, forKey: "sensorId")
        defaults.set(sensorName, forKey: "sensorName")
        defaults.set(zoneHint, forKey: "zoneHint")
        defaults.set(visibleCapacity, forKey: "visibleCapacity")
        defaults.set(visibleWidthMeters, forKey: "visibleWidthMeters")
        defaults.set(min(5, max(1, intervalSeconds)), forKey: "intervalSeconds")
        defaults.set(mode.rawValue, forKey: "mode")
        defaults.set(detector.rawValue, forKey: "detector")
    }
}
