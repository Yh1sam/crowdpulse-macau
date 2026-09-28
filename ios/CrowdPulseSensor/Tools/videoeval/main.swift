// videoeval — run the sensor app's on-device vision pipeline over a pre-recorded video on a Mac.
//
// Compiles the SAME VisionProcessor / FlowEstimator / SensorObservation sources as the iOS app:
//   swiftc -O -o videoeval Tools/videoeval/main.swift Sources/Services/VisionProcessor.swift \
//          Sources/Services/FlowEstimator.swift Sources/Models/SensorObservation.swift
// Usage:
//   videoeval <video.mp4> --out counts.csv [--fps 10] [--capacity 60] [--width-m 20]
//            [--obs observations.json --interval 3 --sensor node-video1 --lat 22.1934 --lon 113.5397 --heading 200]
//            [--post http://localhost:8000]
// Outputs one CSV row per analysed frame, and optionally SensorObservation batches (same schema as the phone).
import Foundation
import AVFoundation
import CoreVideo
import ImageIO

func arg(_ name: String, _ def: String? = nil) -> String? {
    let a = CommandLine.arguments
    if let i = a.firstIndex(of: name), i + 1 < a.count { return a[i + 1] }
    return def
}

guard CommandLine.arguments.count > 1 else {
    print("usage: videoeval <video> --out counts.csv [--fps 10] [--capacity 60] [--obs out.json --interval 3 --sensor node-video1 --lat .. --lon .. --heading ..] [--post URL]")
    exit(2)
}
let videoPath = CommandLine.arguments[1]
let outPath = arg("--out", "counts.csv")!
let targetFPS = Double(arg("--fps", "10")!)!
let capacity = Double(arg("--capacity", "60")!)!
let widthMeters = Double(arg("--width-m", "20")!)!
let obsPath = arg("--obs")
let interval = Double(arg("--interval", "3")!)!
let sensorId = arg("--sensor", "node-video1")!
let lat = Double(arg("--lat", "22.19340")!)!, lon = Double(arg("--lon", "113.53970")!)!, heading = Double(arg("--heading", "200")!)!
let postURL = arg("--post")

let asset = AVURLAsset(url: URL(fileURLWithPath: videoPath))
guard let track = asset.tracks(withMediaType: .video).first, let reader = try? AVAssetReader(asset: asset) else { print("cannot open video"); exit(1) }
let output = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
output.alwaysCopiesSampleData = false
reader.add(output)
reader.startReading()

// --detector apple (default upper-body; add --full-body) | coreml --model path/to/model.mlmodelc [--conf 0.25] [--iou 0.7]
let detectorKind = arg("--detector", "apple")!
let detector: PersonDetector
if detectorKind == "coreml" {
    guard let modelPath = arg("--model") else { print("--model <compiled .mlmodelc> required for --detector coreml"); exit(2) }
    let url = URL(fileURLWithPath: modelPath)
    let conf = Double(arg("--conf", "0.25")!)!, iou = Double(arg("--iou", "0.7")!)!
    detector = try! CoreMLPersonDetector(compiledModelURL: url, identifier: url.deletingPathExtension().lastPathComponent, confidenceThreshold: conf, iouThreshold: iou)
} else {
    detector = AppleHumanDetector(upperBodyOnly: !CommandLine.arguments.contains("--full-body"))
}
let vision = VisionProcessor(detector: detector)
let boxesOut = arg("--boxes-out")   // JSON with the boxes of every analysed frame (near-field scoring, overlays)
var boxDump: [[String: Any]] = []
let videoEpoch = Date(timeIntervalSince1970: 1_800_000_000)
var csv = "t_sec,person_count,density_index,box_area_fraction,flow_img_deg,flow_norm_per_s,flow_conf,vision_conf,brightness,obstructed,latency_ms\n"
var frameResults: [(Double, DetectionResult)] = []
var lastT = -1.0
var analysed = 0
let t0 = Date()
while let sb = output.copyNextSampleBuffer() {
    let pts = CMSampleBufferGetPresentationTimeStamp(sb).seconds
    if lastT >= 0 && pts - lastT < 1.0 / targetFPS - 1e-3 { continue }
    guard let pb = CMSampleBufferGetImageBuffer(sb) else { continue }
    lastT = pts
    let sem = DispatchSemaphore(value: 0)
    var res: DetectionResult?
    vision.process(pixelBuffer: pb, orientation: .up, visibleCapacity: capacity, frameTime: videoEpoch.addingTimeInterval(pts)) { r in res = r; sem.signal() }
    sem.wait()
    guard let r = res else { continue }
    frameResults.append((pts, r))
    if boxesOut != nil {
        boxDump.append(["t_sec": (pts * 1000).rounded() / 1000, "boxes": r.boxes.map { [$0.minX, $0.minY, $0.width, $0.height] }])
    }
    csv += String(format: "%.2f,%d,%.4f,%.4f,%@,%@,%.3f,%.3f,%.3f,%d,%.1f\n", pts, r.personCount, r.densityIndex, r.boxAreaFraction,
                  r.flowImageDeg.map { String(format: "%.1f", $0) } ?? "", r.flowNormPerSec.map { String(format: "%.4f", $0) } ?? "",
                  r.flowConfidence, r.visionConfidence, r.meanBrightness, r.obstructed ? 1 : 0, r.latencyMs)
    analysed += 1
}
try! csv.write(toFile: outPath, atomically: true, encoding: .utf8)
let wall = Date().timeIntervalSince(t0)
print("[\(detector.identifier)] analysed \(analysed) frames in \(String(format: "%.1f", wall)) s (\(String(format: "%.1f", Double(analysed) / max(wall, 0.001))) FPS) -> \(outPath)")
if let boxesOut {
    let data = try! JSONSerialization.data(withJSONObject: ["detector": detector.identifier, "frames": boxDump], options: [.prettyPrinted])
    try! data.write(to: URL(fileURLWithPath: boxesOut))
}

// ---- aggregate into SensorObservations exactly like SensorNode.emitObservation ----
if let obsPath {
    var observations: [SensorObservation] = []
    let start = Date()
    var windowStart = 0.0
    var window: [DetectionResult] = []
    func flush(_ tEnd: Double) {
        guard !window.isEmpty else { return }
        let n = Double(window.count)
        let count = Int((window.map { Double($0.personCount) }.reduce(0, +) / n).rounded())
        let density = window.map { $0.densityIndex }.reduce(0, +) / n
        let visionC = window.map { $0.visionConfidence }.reduce(0, +) / n
        let obstructed = window.filter { $0.obstructed }.count * 2 > window.count
        var sx = 0.0, sy = 0.0, wsum = 0.0, speedSum = 0.0
        for r in window { if let d = r.flowImageDeg, let m = r.flowNormPerSec, r.flowConfidence > 0 {
            let w = r.flowConfidence; sx += w * sin(d * .pi / 180); sy += w * cos(d * .pi / 180); wsum += w; speedSum += w * m } }
        let imageDir = wsum > 0 ? (atan2(sx, sy) * 180 / .pi + 360).truncatingRemainder(dividingBy: 360) : 0
        let speed = min(10, (wsum > 0 ? speedSum / wsum : 0) * widthMeters)
        observations.append(SensorObservation(sensorId: sensorId, timestamp: start.addingTimeInterval(tEnd), latitude: lat, longitude: lon, locationAccuracyM: 5,
                                              headingDeg: heading, deviceMotionStability: 0.98, personCount: count, estimatedDensity: density,
                                              flowDirectionDeg: FlowEstimator.compassDirection(imageDeg: imageDir, cameraHeadingDeg: heading), flowSpeedMps: speed,
                                              visionConfidence: visionC, cameraObstructed: obstructed, modelVersion: "ios-\(detector.identifier)-0.2", mode: "video", zoneHint: nil).clamped())
        window.removeAll()
    }
    for (t, r) in frameResults {
        if t - windowStart >= interval { flush(t); windowStart = t }
        window.append(r)
    }
    flush(lastT)
    let data = try! SensorObservation.encoder.encode(observations)
    try! data.write(to: URL(fileURLWithPath: obsPath))
    print("wrote \(observations.count) observations -> \(obsPath)")
    if let postURL, let url = URL(string: postURL)?.appendingPathComponent("sensor/observation") {
        var sent = 0
        for chunk in stride(from: 0, to: observations.count, by: 200) {
            let batch = Array(observations[chunk..<min(chunk + 200, observations.count)])
            var req = URLRequest(url: url); req.httpMethod = "POST"; req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = try! SensorObservation.encoder.encode(ObservationBatch(observations: batch))
            let sem = DispatchSemaphore(value: 0)
            URLSession.shared.dataTask(with: req) { _, resp, err in
                let code = (resp as? HTTPURLResponse)?.statusCode ?? -1
                if err == nil && (200..<300).contains(code) { sent += batch.count } else { print("post failed: \(err?.localizedDescription ?? "HTTP \(code)")") }
                sem.signal()
            }.resume()
            sem.wait()
        }
        print("posted \(sent) observations to \(postURL)")
    }
}
