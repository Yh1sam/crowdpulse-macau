import Foundation
import CoreMotion
import Combine

/// Accelerometer + gyroscope → device stability score (1 = perfectly still).
/// Used to discount observations when the phone is moved, knocked or carried.
final class MotionMonitor: ObservableObject {
    @Published var accel: (x: Double, y: Double, z: Double) = (0, 0, 0)
    @Published var gyro: (x: Double, y: Double, z: Double) = (0, 0, 0)
    @Published var stability: Double = 1.0
    @Published var available = false

    private let manager = CMMotionManager()
    private var accelWindow: [Double] = []
    private var gyroWindow: [Double] = []
    private let windowSize = 30  // ~1.5 s at 20 Hz

    func start() {
        available = manager.isAccelerometerAvailable && manager.isGyroAvailable
        guard available else { return }
        manager.accelerometerUpdateInterval = 0.05
        manager.gyroUpdateInterval = 0.05
        manager.startAccelerometerUpdates(to: .main) { [weak self] data, _ in
            guard let self, let a = data?.acceleration else { return }
            self.accel = (a.x, a.y, a.z)
            self.push(&self.accelWindow, sqrt(a.x * a.x + a.y * a.y + a.z * a.z))
            self.recompute()
        }
        manager.startGyroUpdates(to: .main) { [weak self] data, _ in
            guard let self, let r = data?.rotationRate else { return }
            self.gyro = (r.x, r.y, r.z)
            self.push(&self.gyroWindow, sqrt(r.x * r.x + r.y * r.y + r.z * r.z))
        }
    }

    func stop() { manager.stopAccelerometerUpdates(); manager.stopGyroUpdates() }

    private func push(_ w: inout [Double], _ v: Double) { w.append(v); if w.count > windowSize { w.removeFirst() } }

    private func recompute() { stability = MotionMonitor.stabilityScore(accelMagnitudes: accelWindow, gyroRates: gyroWindow) }

    /// Stability = 1 − (scaled std-dev of |accel| + scaled mean |gyro|), clamped to 0…1.
    /// A phone on a tripod scores ≈0.97–0.99; a hand-held phone ≈0.6–0.85; a knocked phone < 0.5.
    static func stabilityScore(accelMagnitudes: [Double], gyroRates: [Double]) -> Double {
        guard accelMagnitudes.count >= 2 else { return 1.0 }
        let mean = accelMagnitudes.reduce(0, +) / Double(accelMagnitudes.count)
        let variance = accelMagnitudes.reduce(0) { $0 + ($1 - mean) * ($1 - mean) } / Double(accelMagnitudes.count)
        let accelSD = sqrt(variance)                               // g units
        let gyroMean = gyroRates.isEmpty ? 0 : gyroRates.reduce(0, +) / Double(gyroRates.count)  // rad/s
        let penalty = min(1.0, accelSD * 8.0) * 0.6 + min(1.0, gyroMean * 2.0) * 0.4
        return max(0, min(1, 1 - penalty))
    }
}
