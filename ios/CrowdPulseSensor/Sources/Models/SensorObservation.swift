import Foundation

/// Exactly the shared schema (`shared/schemas/sensor_observation.schema.json`).
/// Numbers only: no images, no identifiers of people.
struct SensorObservation: Codable, Equatable {
    var sensorId: String
    var timestamp: Date
    var latitude: Double
    var longitude: Double
    var locationAccuracyM: Double
    var headingDeg: Double
    var deviceMotionStability: Double
    var personCount: Int
    var estimatedDensity: Double
    var flowDirectionDeg: Double
    var flowSpeedMps: Double
    var visionConfidence: Double
    var cameraObstructed: Bool
    var modelVersion: String
    var mode: String?
    var zoneHint: String?

    enum CodingKeys: String, CodingKey {
        case sensorId = "sensor_id", timestamp, latitude, longitude
        case locationAccuracyM = "location_accuracy_m", headingDeg = "heading_deg"
        case deviceMotionStability = "device_motion_stability", personCount = "person_count"
        case estimatedDensity = "estimated_density", flowDirectionDeg = "flow_direction_deg"
        case flowSpeedMps = "flow_speed_mps", visionConfidence = "vision_confidence"
        case cameraObstructed = "camera_obstructed", modelVersion = "model_version", mode
        case zoneHint = "zone_hint"
    }

    static let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        return e
    }()

    /// Clamp everything into the schema's bounds so a noisy sensor can never produce an invalid payload.
    func clamped() -> SensorObservation {
        var o = self
        o.latitude = min(90, max(-90, latitude))
        o.longitude = min(180, max(-180, longitude))
        o.locationAccuracyM = min(10000, max(0, locationAccuracyM))
        o.headingDeg = headingDeg.isFinite ? ((headingDeg.truncatingRemainder(dividingBy: 360)) + 360).truncatingRemainder(dividingBy: 360) : 0
        o.deviceMotionStability = min(1, max(0, deviceMotionStability))
        o.personCount = min(5000, max(0, personCount))
        o.estimatedDensity = min(1, max(0, estimatedDensity))
        o.flowDirectionDeg = flowDirectionDeg.isFinite ? ((flowDirectionDeg.truncatingRemainder(dividingBy: 360)) + 360).truncatingRemainder(dividingBy: 360) : 0
        o.flowSpeedMps = min(10, max(0, flowSpeedMps.isFinite ? flowSpeedMps : 0))
        o.visionConfidence = min(1, max(0, visionConfidence))
        return o
    }
}

struct ObservationBatch: Codable {
    var observations: [SensorObservation]
}
