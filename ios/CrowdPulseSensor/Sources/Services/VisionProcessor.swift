import Foundation
import Vision
import CoreImage
import CoreGraphics
import Combine

/// Result of analysing one camera frame. Boxes are anonymous rectangles in normalised
/// coordinates (top-left origin) used only for the on-screen overlay and the flow estimate.
struct DetectionResult {
    var boxes: [CGRect]
    var personCount: Int
    var densityIndex: Double        // relative 0..1 = count / visibleCapacity
    var boxAreaFraction: Double     // fraction of the frame covered by person boxes (secondary proxy)
    var flowImageDeg: Double?
    var flowNormPerSec: Double?
    var flowConfidence: Double
    var visionConfidence: Double
    var obstructed: Bool
    var meanBrightness: Double
    var latencyMs: Double
    var fps: Double
    var timestamp: Date
}

/// Runs Apple Vision's human-rectangle detector on-device. Frames are never stored.
final class VisionProcessor {
    private let request: VNDetectHumanRectanglesRequest
    private let ciContext = CIContext(options: [.cacheIntermediates: false])
    private var previousCentroids: [CGPoint] = []
    private var previousTime: Date?
    private var frameTimes: [Date] = []
    private let queue = DispatchQueue(label: "crowdpulse.vision", qos: .userInitiated)
    private(set) var isBusy = false

    init() {
        request = VNDetectHumanRectanglesRequest()
        request.upperBodyOnly = true   // more robust in crowds where legs are occluded
    }

    /// Analyse a pixel buffer asynchronously; `completion` runs on the vision queue.
    func process(pixelBuffer: CVPixelBuffer, orientation: CGImagePropertyOrientation, visibleCapacity: Double, completion: @escaping (DetectionResult) -> Void) {
        guard !isBusy else { return }
        isBusy = true
        queue.async { [self] in
            defer { isBusy = false }
            let t0 = Date()
            let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, orientation: orientation, options: [:])
            var boxes: [CGRect] = []
            var confidences: [Double] = []
            do {
                try handler.perform([request])
                for obs in request.results ?? [] {
                    // Vision uses a bottom-left origin; flip to top-left for the overlay/flow.
                    let b = obs.boundingBox
                    boxes.append(CGRect(x: b.minX, y: 1 - b.maxY, width: b.width, height: b.height))
                    confidences.append(Double(obs.confidence))
                }
            } catch {
                // keep going: an inference failure yields an empty, low-confidence result
            }
            let brightness = VisionProcessor.meanLuma(pixelBuffer, context: ciContext)
            let obstructed = brightness < 0.06 || brightness > 0.98
            let now = Date()
            let dt = previousTime.map { now.timeIntervalSince($0) } ?? 0
            let centroids = boxes.map { CGPoint(x: $0.midX, y: $0.midY) }
            let flow = FlowEstimator.estimate(previous: previousCentroids, current: centroids, dt: dt)
            previousCentroids = centroids
            previousTime = now
            frameTimes.append(now)
            frameTimes.removeAll { now.timeIntervalSince($0) > 2 }
            let fps = frameTimes.count > 1 ? Double(frameTimes.count - 1) / max(0.001, now.timeIntervalSince(frameTimes[0])) : 0
            let area = min(1.0, boxes.reduce(0.0) { $0 + Double($1.width * $1.height) })
            let count = boxes.count
            let density = min(1.0, Double(count) / max(1.0, visibleCapacity))
            // vision confidence: mean detector confidence, reduced by crowding (occlusion) and darkness
            let meanConf = confidences.isEmpty ? (obstructed ? 0.1 : 0.7) : confidences.reduce(0, +) / Double(confidences.count)
            let vision = max(0.05, min(0.99, meanConf * (1 - 0.3 * density) * (brightness < 0.15 ? 0.6 : 1.0)))
            completion(DetectionResult(boxes: boxes, personCount: count, densityIndex: density, boxAreaFraction: area,
                                       flowImageDeg: flow?.directionImageDeg, flowNormPerSec: flow?.magnitudeNormPerSec,
                                       flowConfidence: flow?.confidence ?? 0, visionConfidence: vision, obstructed: obstructed,
                                       meanBrightness: brightness, latencyMs: Date().timeIntervalSince(t0) * 1000, fps: fps, timestamp: now))
        }
    }

    /// Mean luminance of a heavily downscaled frame (obstruction / low-light detector).
    static func meanLuma(_ pb: CVPixelBuffer, context: CIContext) -> Double {
        let img = CIImage(cvPixelBuffer: pb)
        let extent = img.extent
        guard let filter = CIFilter(name: "CIAreaAverage", parameters: [kCIInputImageKey: img, kCIInputExtentKey: CIVector(cgRect: extent)]),
              let out = filter.outputImage else { return 0.5 }
        var px = [UInt8](repeating: 0, count: 4)
        context.render(out, toBitmap: &px, rowBytes: 4, bounds: CGRect(x: 0, y: 0, width: 1, height: 1), format: .RGBA8, colorSpace: CGColorSpaceCreateDeviceRGB())
        return (0.299 * Double(px[0]) + 0.587 * Double(px[1]) + 0.114 * Double(px[2])) / 255.0
    }
}
