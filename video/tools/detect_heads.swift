// Offline head finder with Apple Vision (no network).
// Build: swiftc -O video/tools/detect_heads.swift -o video/build/tools/detect_heads
// Usage: detect_heads <list.txt>   (one image path per line)
// Prints one JSON object per image: faces (VNDetectFaceRectanglesRequest) and head keypoints
// (VNDetectHumanBodyPoseRequest: nose, eyes, ears, neck), in pixel coordinates, origin top-left.
import Foundation
import Vision
import ImageIO
import CoreGraphics

func loadCG(_ path: String) -> CGImage? {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil) else { return nil }
    return CGImageSourceCreateImageAtIndex(src, 0, nil)
}

let args = CommandLine.arguments
guard args.count > 1, let list = try? String(contentsOfFile: args[1], encoding: .utf8) else {
    FileHandle.standardError.write("usage: detect list.txt\n".data(using: .utf8)!)
    exit(2)
}

for line in list.split(separator: "\n") {
    let path = String(line).trimmingCharacters(in: .whitespaces)
    if path.isEmpty { continue }
    guard let cg = loadCG(path) else { print("{\"path\":\"\(path)\",\"error\":\"load\"}"); continue }
    let W = Double(cg.width), H = Double(cg.height)
    let faceReq = VNDetectFaceRectanglesRequest()
    let poseReq = VNDetectHumanBodyPoseRequest()
    let upperReq = VNDetectHumanRectanglesRequest()
    upperReq.upperBodyOnly = true
    let fullReq = VNDetectHumanRectanglesRequest()
    fullReq.upperBodyOnly = false
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try handler.perform([faceReq, poseReq, upperReq, fullReq]) } catch {
        print("{\"path\":\"\(path)\",\"error\":\"vision\"}"); continue
    }
    var faces: [[String: Double]] = []
    for f in faceReq.results ?? [] {
        let b = f.boundingBox
        faces.append(["x0": b.minX * W, "y0": (1 - b.maxY) * H, "x1": b.maxX * W, "y1": (1 - b.minY) * H,
                      "conf": Double(f.confidence)])
    }
    var uppers: [[String: Double]] = []
    for u in upperReq.results ?? [] {
        let b = u.boundingBox
        uppers.append(["x0": b.minX * W, "y0": (1 - b.maxY) * H, "x1": b.maxX * W, "y1": (1 - b.minY) * H,
                       "conf": Double(u.confidence)])
    }
    var fulls: [[String: Double]] = []
    for u in fullReq.results ?? [] {
        let b = u.boundingBox
        fulls.append(["x0": b.minX * W, "y0": (1 - b.maxY) * H, "x1": b.maxX * W, "y1": (1 - b.minY) * H,
                      "conf": Double(u.confidence)])
    }
    var poses: [[String: [Double]]] = []
    let names: [(VNHumanBodyPoseObservation.JointName, String)] = [
        (.nose, "nose"), (.leftEye, "leye"), (.rightEye, "reye"), (.leftEar, "lear"), (.rightEar, "rear"),
        (.neck, "neck"), (.leftShoulder, "lsho"), (.rightShoulder, "rsho")]
    for p in poseReq.results ?? [] {
        var d: [String: [Double]] = [:]
        for (jn, key) in names {
            if let pt = try? p.recognizedPoint(jn), pt.confidence > 0.1 {
                d[key] = [Double(pt.location.x) * W, (1 - Double(pt.location.y)) * H, Double(pt.confidence)]
            }
        }
        if !d.isEmpty { poses.append(d) }
    }
    let obj: [String: Any] = ["path": path, "w": W, "h": H, "faces": faces, "poses": poses, "uppers": uppers, "fulls": fulls]
    let data = try! JSONSerialization.data(withJSONObject: obj, options: [.sortedKeys])
    print(String(data: data, encoding: .utf8)!)
}
