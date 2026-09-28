import XCTest
import CoreGraphics
@testable import CrowdPulseSensor

final class SensorLogicTests: XCTestCase {
    func testObservationEncodesSharedSchemaKeys() throws {
        let o = SensorObservation(sensorId: "node-abc123", timestamp: Date(timeIntervalSince1970: 0), latitude: 22.19, longitude: 113.54, locationAccuracyM: 5, headingDeg: 120,
                                  deviceMotionStability: 0.95, personCount: 12, estimatedDensity: 0.3, flowDirectionDeg: 200, flowSpeedMps: 0.8, visionConfidence: 0.9,
                                  cameraObstructed: false, modelVersion: "test", mode: "live", zoneHint: nil)
        let data = try SensorObservation.encoder.encode(o)
        let json = try XCTUnwrap(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        for key in ["sensor_id", "timestamp", "latitude", "longitude", "location_accuracy_m", "heading_deg", "device_motion_stability", "person_count", "estimated_density", "flow_direction_deg", "flow_speed_mps", "vision_confidence", "camera_obstructed", "model_version"] {
            XCTAssertNotNil(json[key], "missing \(key)")
        }
        XCTAssertNil(json["image"]); XCTAssertNil(json["face_id"])
    }

    func testClampingKeepsPayloadInsideSchemaBounds() {
        let o = SensorObservation(sensorId: "node-abc123", timestamp: Date(), latitude: 95, longitude: -200, locationAccuracyM: -3, headingDeg: 725, deviceMotionStability: 1.4,
                                  personCount: 9000, estimatedDensity: 2.0, flowDirectionDeg: -30, flowSpeedMps: 40, visionConfidence: -1, cameraObstructed: false, modelVersion: "t", mode: nil, zoneHint: nil).clamped()
        XCTAssertEqual(o.latitude, 90); XCTAssertEqual(o.longitude, -180); XCTAssertEqual(o.locationAccuracyM, 0)
        XCTAssertEqual(o.headingDeg, 5, accuracy: 1e-9); XCTAssertEqual(o.deviceMotionStability, 1); XCTAssertEqual(o.personCount, 5000)
        XCTAssertEqual(o.estimatedDensity, 1); XCTAssertEqual(o.flowDirectionDeg, 330, accuracy: 1e-9); XCTAssertEqual(o.flowSpeedMps, 10); XCTAssertEqual(o.visionConfidence, 0)
    }

    func testRandomNodeIdIsAnonymousAndSchemaConformant() {
        let id = SensorSettings.randomNodeId()
        XCTAssertTrue(id.range(of: "^node-[a-z0-9]{4,32}$", options: .regularExpression) != nil)
        XCTAssertNotEqual(id, SensorSettings.randomNodeId())
    }

    func testFlowEstimatorRecoversRightwardMotion() {
        let prev = [CGPoint(x: 0.2, y: 0.5), CGPoint(x: 0.5, y: 0.5), CGPoint(x: 0.7, y: 0.3)]
        let cur = prev.map { CGPoint(x: $0.x + 0.05, y: $0.y) }
        let f = try! XCTUnwrap(FlowEstimator.estimate(previous: prev, current: cur, dt: 0.5))
        XCTAssertEqual(f.directionImageDeg, 90, accuracy: 1e-6)   // right
        XCTAssertEqual(f.magnitudeNormPerSec, 0.1, accuracy: 1e-6)
        XCTAssertEqual(f.matched, 3)
        XCTAssertGreaterThan(f.confidence, 0.5)
        XCTAssertEqual(FlowEstimator.compassDirection(imageDeg: 90, cameraHeadingDeg: 300), 30, accuracy: 1e-9)
    }

    func testFlowEstimatorIgnoresUnmatchedAndReturnsNilWhenEmpty() {
        XCTAssertNil(FlowEstimator.estimate(previous: [], current: [CGPoint(x: 0.5, y: 0.5)], dt: 0.1))
        let far = FlowEstimator.estimate(previous: [CGPoint(x: 0.1, y: 0.1)], current: [CGPoint(x: 0.9, y: 0.9)], dt: 0.1)
        XCTAssertNil(far)
    }

    func testStabilityScore() {
        XCTAssertEqual(MotionMonitor.stabilityScore(accelMagnitudes: Array(repeating: 1.0, count: 30), gyroRates: Array(repeating: 0.0, count: 30)), 1.0, accuracy: 1e-9)
        let shaky = (0..<30).map { 1.0 + 0.3 * sin(Double($0)) }
        XCTAssertLessThan(MotionMonitor.stabilityScore(accelMagnitudes: shaky, gyroRates: Array(repeating: 1.5, count: 30)), 0.5)
    }

    func testUploaderBuffersWhenOffline() {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let up = Uploader(bufferDirectory: dir)
        let o = SensorObservation(sensorId: "node-abc123", timestamp: Date(), latitude: 0, longitude: 0, locationAccuracyM: 1, headingDeg: 0, deviceMotionStability: 1, personCount: 1, estimatedDensity: 0.1, flowDirectionDeg: 0, flowSpeedMps: 0, visionConfidence: 0.5, cameraObstructed: false, modelVersion: "t", mode: nil, zoneHint: nil)
        up.enqueue(o, backendURL: "http://127.0.0.1:1")   // nothing listens here
        XCTAssertEqual(up.pendingCount, 1)
        let reloaded = Uploader(bufferDirectory: dir)
        XCTAssertEqual(reloaded.pendingCount, 1, "buffer must survive restarts")
    }
}
