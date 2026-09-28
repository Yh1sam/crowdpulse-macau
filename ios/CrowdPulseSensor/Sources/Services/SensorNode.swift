import Foundation
import Combine
import CoreGraphics
import CoreImage
import CoreVideo
import ImageIO

/// Coordinates camera → vision → sensors → observation → upload.
@MainActor
final class SensorNode: ObservableObject {
    let settings: SensorSettings
    let camera = CameraService()
    let vision = VisionProcessor()
    let motion = MotionMonitor()
    let location = LocationMonitor()
    let uploader = Uploader()

    @Published var running = false
    @Published var cameraAuthorized = false
    @Published var latest: DetectionResult?
    @Published var lastObservation: SensorObservation?
    @Published var observationsBuilt = 0
    @Published var mlStatus = "idle"
    /// Latest decoded frame in video mode (for the on-screen preview only).
    @Published var videoFrame: CGImage?
    private var video: VideoFrameSource?
    private let previewContext = CIContext(options: [.cacheIntermediates: false])
    private var previewTick = 0

    private var timer: Timer?
    private var simTick = 0
    private var recent: [DetectionResult] = []

    init(settings: SensorSettings) {
        self.settings = settings
        camera.frameHandler = { [weak self] pb, orientation in self?.handleFrame(pb, orientation) }
    }

    func start() {
        guard !running else { return }
        running = true
        motion.start()
        location.start()
        switch settings.mode {
        case .live:
            camera.requestAccess { [weak self] ok in
                guard let self else { return }
                self.cameraAuthorized = ok
                if ok { self.camera.configure(); self.camera.start(); self.mlStatus = "Vision human detector (on-device)" }
                else { self.mlStatus = "camera permission denied" }
            }
        case .video:
            if let url = VideoFrameSource.bundledSample() {
                let v = VideoFrameSource(url: url)
                v.frameHandler = { [weak self] pb, o in self?.handleFrame(pb, o) }
                v.start()
                video = v
                mlStatus = "Vision human detector on pre-recorded video (CC0 sample clip)"
            } else {
                mlStatus = "sample video missing from bundle"
            }
        case .simulated:
            mlStatus = "simulated detections (no camera)"
        }
        scheduleTimer()
    }

    func stop() {
        running = false
        camera.stop()
        video?.stop()
        video = nil
        motion.stop()
        location.stop()
        timer?.invalidate()
        timer = nil
    }

    func restartTimer() { if running { scheduleTimer() } }

    private func scheduleTimer() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: max(1, min(5, settings.intervalSeconds)), repeats: true) { [weak self] _ in
            Task { @MainActor in self?.emitObservation() }
        }
    }

    private nonisolated func handleFrame(_ pb: CVPixelBuffer, _ orientation: CGImagePropertyOrientation) {
        Task { @MainActor in
            let cap = self.settings.visibleCapacity
            if self.settings.mode == .video {
                self.previewTick += 1
                if self.previewTick % 2 == 0, let cg = self.previewContext.createCGImage(CIImage(cvPixelBuffer: pb), from: CIImage(cvPixelBuffer: pb).extent) {
                    self.videoFrame = cg
                }
            }
            self.vision.process(pixelBuffer: pb, orientation: orientation, visibleCapacity: cap) { result in
                Task { @MainActor in
                    self.latest = result
                    self.recent.append(result)
                    if self.recent.count > 60 { self.recent.removeFirst(self.recent.count - 60) }
                }
            }
        }
    }

    /// Build one observation from the detections since the last emission (mean of the window).
    func emitObservation() {
        if settings.mode == .simulated { pushSimulatedDetection() }
        let window = recent
        recent.removeAll()
        guard let last = window.last ?? latest else { return }
        let n = Double(max(1, window.count))
        let count = Int((window.map { Double($0.personCount) }.reduce(0, +) / n).rounded())
        let density = window.map { $0.densityIndex }.reduce(0, +) / n
        let vision = window.map { $0.visionConfidence }.reduce(0, +) / n
        let obstructed = window.filter { $0.obstructed }.count * 2 > window.count
        // flow: confidence-weighted circular mean of image directions, then rotate by the compass heading
        var sx = 0.0, sy = 0.0, wsum = 0.0, speedSum = 0.0
        for r in window { if let d = r.flowImageDeg, let m = r.flowNormPerSec, r.flowConfidence > 0 {
            let w = r.flowConfidence; sx += w * sin(d * .pi / 180); sy += w * cos(d * .pi / 180); wsum += w; speedSum += w * m } }
        let imageDir = wsum > 0 ? (atan2(sx, sy) * 180 / .pi + 360).truncatingRemainder(dividingBy: 360) : Double.random(in: 0..<360)
        let normSpeed = wsum > 0 ? speedSum / wsum : 0
        let speedMps = min(10, normSpeed * settings.visibleWidthMeters)
        let obs = SensorObservation(
            sensorId: settings.sensorId, timestamp: Date(),
            latitude: location.latitude, longitude: location.longitude, locationAccuracyM: location.hasFix ? location.accuracyM : 10000,
            headingDeg: location.headingDeg, deviceMotionStability: motion.stability,
            personCount: count, estimatedDensity: density,
            flowDirectionDeg: FlowEstimator.compassDirection(imageDeg: imageDir, cameraHeadingDeg: location.headingDeg),
            flowSpeedMps: speedMps, visionConfidence: vision, cameraObstructed: obstructed,
            modelVersion: SensorSettings.modelVersion, mode: settings.mode.rawValue,
            zoneHint: settings.zoneHint.isEmpty ? nil : settings.zoneHint).clamped()
        _ = last
        lastObservation = obs
        observationsBuilt += 1
        uploader.enqueue(obs, backendURL: settings.backendURL)
    }

    /// Simulated-detection mode (for the iOS Simulator / no camera): a slow sine wave of crowding.
    private func pushSimulatedDetection() {
        simTick += 1
        let t = Double(simTick)
        let base = 0.5 + 0.4 * sin(t / 40)
        let count = max(0, Int((base * settings.visibleCapacity + Double.random(in: -2...2)).rounded()))
        let boxes = (0..<min(count, 30)).map { _ in CGRect(x: Double.random(in: 0.05...0.85), y: Double.random(in: 0.2...0.8), width: 0.08, height: 0.18) }
        latest = DetectionResult(boxes: boxes, personCount: count, densityIndex: min(1, Double(count) / settings.visibleCapacity), boxAreaFraction: Double(boxes.count) * 0.0144,
                                 flowImageDeg: 20 + 10 * sin(t / 15), flowNormPerSec: 0.08 + 0.03 * sin(t / 9), flowConfidence: 0.7, visionConfidence: 0.85 - 0.3 * base,
                                 obstructed: false, meanBrightness: 0.5, latencyMs: 12, fps: 10, timestamp: Date())
        if let l = latest { recent.append(l) }
    }
}
