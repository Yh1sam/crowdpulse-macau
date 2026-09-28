import Foundation
import Vision
import CoreML
import CoreImage
import CoreVideo
import ImageIO

/// One anonymous detection: a rectangle in normalised image coordinates (top-left origin) and a score.
/// No crops, embeddings or identities are ever produced.
struct PersonBox {
    var rect: CGRect
    var confidence: Double
}

/// Pluggable on-device person detector. Implementations must be safe to call from one serial queue.
protocol PersonDetector: AnyObject {
    /// Short identifier sent as part of `model_version` (provenance of every observation).
    var identifier: String { get }
    func detect(_ pixelBuffer: CVPixelBuffer, orientation: CGImagePropertyOrientation) throws -> [PersonBox]
}

/// Apple's built-in `VNDetectHumanRectanglesRequest`. No model file needed, but it misses most
/// people further than a few metres away (measured: ~34% of near-field people on the CC0 crossing clip).
final class AppleHumanDetector: PersonDetector {
    private let request: VNDetectHumanRectanglesRequest
    let identifier: String

    init(upperBodyOnly: Bool = true) {
        request = VNDetectHumanRectanglesRequest()
        request.upperBodyOnly = upperBodyOnly
        identifier = upperBodyOnly ? "apple-human-upper" : "apple-human-full"
        #if targetEnvironment(simulator)
        // Vision's built-in detectors cannot create a GPU/ANE inference context in the iOS Simulator.
        if let cpu = MLComputeDevice.allComputeDevices.first(where: { if case .cpu = $0 { return true } else { return false } }) {
            request.setComputeDevice(cpu, for: .main)
        }
        #endif
    }

    func detect(_ pixelBuffer: CVPixelBuffer, orientation: CGImagePropertyOrientation) throws -> [PersonBox] {
        let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, orientation: orientation, options: [:])
        try handler.perform([request])
        return (request.results ?? []).map { obs in
            let b = obs.boundingBox  // bottom-left origin -> flip
            return PersonBox(rect: CGRect(x: b.minX, y: 1 - b.maxY, width: b.width, height: b.height), confidence: Double(obs.confidence))
        }
    }
}

/// A CoreML object detector exported with an NMS stage (e.g. YOLO11 via
/// `Tools/export_yolo.py`). Only the "person" class is kept.
final class CoreMLPersonDetector: PersonDetector {
    private let vnModel: VNCoreMLModel
    private let request: VNCoreMLRequest
    let identifier: String
    let confidenceThreshold: Double
    let iouThreshold: Double

    init(compiledModelURL: URL, identifier: String, confidenceThreshold: Double = 0.25, iouThreshold: Double = 0.7) throws {
        let config = MLModelConfiguration()
        config.computeUnits = .all
        let model = try MLModel(contentsOf: compiledModelURL, configuration: config)
        vnModel = try VNCoreMLModel(for: model)
        // The exported pipeline takes its thresholds as extra model inputs.
        vnModel.featureProvider = try MLDictionaryFeatureProvider(dictionary: [
            "iouThreshold": MLFeatureValue(double: iouThreshold),
            "confidenceThreshold": MLFeatureValue(double: confidenceThreshold),
        ])
        request = VNCoreMLRequest(model: vnModel)
        // Letterbox instead of crop: a centre crop would cut off the sides of a wide street view.
        request.imageCropAndScaleOption = .scaleFit
        self.identifier = identifier
        self.confidenceThreshold = confidenceThreshold
        self.iouThreshold = iouThreshold
    }

    func detect(_ pixelBuffer: CVPixelBuffer, orientation: CGImagePropertyOrientation) throws -> [PersonBox] {
        let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, orientation: orientation, options: [:])
        try handler.perform([request])
        var out: [PersonBox] = []
        for case let obs as VNRecognizedObjectObservation in request.results ?? [] {
            guard let top = obs.labels.first, top.identifier == "person" else { continue }
            let b = obs.boundingBox  // bottom-left origin -> flip
            out.append(PersonBox(rect: CGRect(x: b.minX, y: 1 - b.maxY, width: b.width, height: b.height), confidence: Double(top.confidence)))
        }
        return out
    }

    /// The bundled default detector (YOLO11n, ~5 MB), or nil if the model is not in the bundle.
    static func bundledDefault(bundle: Bundle = .main) -> CoreMLPersonDetector? {
        guard let url = bundle.url(forResource: "yolo11n", withExtension: "mlmodelc") else { return nil }
        return try? CoreMLPersonDetector(compiledModelURL: url, identifier: "yolo11n")
    }
}
