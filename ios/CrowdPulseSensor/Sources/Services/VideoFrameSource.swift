import Foundation
import AVFoundation
import CoreVideo
import ImageIO

/// Pre-recorded-video mode: decodes a clip (bundled sample or a file URL) and feeds frames to the
/// same handler the camera uses, paced at the target FPS and looped. Frames are never written anywhere.
final class VideoFrameSource {
    var targetFPS: Double = 10
    var frameHandler: ((CVPixelBuffer, CGImagePropertyOrientation) -> Void)?
    private(set) var isRunning = false
    private(set) var lastError: String?
    private var thread: Thread?
    private let url: URL

    init(url: URL) { self.url = url }

    static func bundledSample() -> URL? {
        Bundle.main.url(forResource: "sample_crowd", withExtension: "mp4")
    }

    func start() {
        guard !isRunning else { return }
        isRunning = true
        let t = Thread { [weak self] in self?.loop() }
        t.qualityOfService = .userInitiated
        thread = t
        t.start()
    }

    func stop() { isRunning = false }

    private func loop() {
        while isRunning {
            let asset = AVURLAsset(url: url)
            guard let track = asset.tracks(withMediaType: .video).first, let reader = try? AVAssetReader(asset: asset) else {
                lastError = "cannot open video"; isRunning = false; return
            }
            let output = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
            output.alwaysCopiesSampleData = false
            reader.add(output)
            reader.startReading()
            let start = Date()
            var lastPTS = -1.0
            while isRunning, let sb = output.copyNextSampleBuffer() {
                let pts = CMSampleBufferGetPresentationTimeStamp(sb).seconds
                if lastPTS >= 0 && pts - lastPTS < 1.0 / targetFPS - 1e-3 { continue }
                lastPTS = pts
                // real-time pacing so the flow estimate's dt matches the clip
                let due = start.addingTimeInterval(pts)
                let wait = due.timeIntervalSinceNow
                if wait > 0 { Thread.sleep(forTimeInterval: wait) }
                if let pb = CMSampleBufferGetImageBuffer(sb) { frameHandler?(pb, .up) }
            }
            reader.cancelReading()
        }
    }
}
