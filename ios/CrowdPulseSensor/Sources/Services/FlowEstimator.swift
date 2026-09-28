import Foundation
import CoreGraphics

/// Anonymous frame-to-frame flow estimate from detection-box centroids.
///
/// Boxes of consecutive frames are matched greedily to their nearest neighbour within a
/// radius; the matched displacements are combined with a robust (median) vector. Matches
/// live for one frame pair only: nothing is tracked over time and nothing identifies a person.
struct FlowEstimate: Equatable {
    var directionImageDeg: Double   // 0 = up in the image, 90 = right
    var magnitudeNormPerSec: Double // fraction of frame width per second
    var confidence: Double          // 0..1, from match count and vector agreement
    var matched: Int
}

enum FlowEstimator {
    static func estimate(previous: [CGPoint], current: [CGPoint], dt: Double, maxMatchDistance: CGFloat = 0.12) -> FlowEstimate? {
        guard dt > 0, !previous.isEmpty, !current.isEmpty else { return nil }
        var used = Set<Int>()
        var dxs: [Double] = [], dys: [Double] = []
        for p in previous {
            var best = -1
            var bestD = CGFloat.greatestFiniteMagnitude
            for (j, c) in current.enumerated() where !used.contains(j) {
                let d = hypot(c.x - p.x, c.y - p.y)
                if d < bestD { bestD = d; best = j }
            }
            if best >= 0 && bestD <= maxMatchDistance {
                used.insert(best)
                dxs.append(Double(current[best].x - p.x))
                dys.append(Double(current[best].y - p.y))
            }
        }
        guard dxs.count >= 1 else { return nil }
        let mdx = median(dxs), mdy = median(dys)
        let mag = hypot(mdx, mdy) / dt
        // agreement: fraction of vectors pointing within 60° of the median direction
        let ang = atan2(mdx, mdy)
        var agree = 0
        for (dx, dy) in zip(dxs, dys) where hypot(dx, dy) > 1e-4 {
            let a = atan2(dx, dy)
            var diff = abs(a - ang)
            if diff > .pi { diff = 2 * .pi - diff }
            if diff < .pi / 3 { agree += 1 }
        }
        let agreement = dxs.count > 0 ? Double(agree) / Double(dxs.count) : 0
        let countFactor = min(1.0, Double(dxs.count) / 6.0)
        // image coordinates: y grows downward in UIKit-style normalised space we use (top-left origin)
        let dirDeg = (atan2(mdx, -mdy) * 180 / .pi + 360).truncatingRemainder(dividingBy: 360)
        return FlowEstimate(directionImageDeg: dirDeg, magnitudeNormPerSec: mag, confidence: 0.5 * agreement + 0.5 * countFactor, matched: dxs.count)
    }

    /// Convert an image-relative direction into a compass bearing given the camera heading
    /// (image "up" = away from the camera = the heading direction; image right = heading + 90).
    static func compassDirection(imageDeg: Double, cameraHeadingDeg: Double) -> Double {
        ((imageDeg + cameraHeadingDeg).truncatingRemainder(dividingBy: 360) + 360).truncatingRemainder(dividingBy: 360)
    }

    static func median(_ v: [Double]) -> Double {
        let s = v.sorted()
        let n = s.count
        guard n > 0 else { return 0 }
        return n % 2 == 1 ? s[n / 2] : 0.5 * (s[n / 2 - 1] + s[n / 2])
    }
}
