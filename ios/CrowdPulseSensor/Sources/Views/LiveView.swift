import SwiftUI
import AVFoundation

/// Camera preview with anonymous detection boxes and the live crowd statistics.
struct LiveView: View {
    @EnvironmentObject var settings: SensorSettings
    @EnvironmentObject var node: SensorNode

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                if settings.mode == .live { CameraPreview(session: node.camera.session) } else { Color.black.overlay(Text("simulated mode").foregroundStyle(.white)) }
                GeometryReader { geo in
                    ForEach(Array((node.latest?.boxes ?? []).enumerated()), id: \.offset) { _, b in
                        Rectangle().stroke(Color.green, lineWidth: 2)
                            .frame(width: b.width * geo.size.width, height: b.height * geo.size.height)
                            .position(x: b.midX * geo.size.width, y: b.midY * geo.size.height)
                    }
                }
                if let r = node.latest, r.obstructed { Text("CAMERA OBSTRUCTED / DARK").padding(6).background(.red).foregroundStyle(.white).cornerRadius(6) }
            }
            .aspectRatio(4 / 3, contentMode: .fit)
            .background(Color.black)
            .cornerRadius(10)
            Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 6) {
                GridRow { stat("people in view", "\(node.latest?.personCount ?? 0)"); stat("density index", String(format: "%.2f", node.latest?.densityIndex ?? 0)) }
                GridRow { stat("flow", flowText); stat("speed", String(format: "%.2f m/s", node.lastObservation?.flowSpeedMps ?? 0)) }
                GridRow { stat("vision confidence", String(format: "%.2f", node.latest?.visionConfidence ?? 0)); stat("stability", String(format: "%.2f", node.motion.stability)) }
                GridRow { stat("upload", node.uploader.lastStatus); stat("buffered", "\(node.uploader.buffered)") }
                GridRow { stat("zone (backend)", node.uploader.lastZoneAssignment ?? "–"); stat("sent", "\(node.uploader.sent)") }
            }
            .padding(.horizontal)
            Text("Boxes are anonymous and exist only on this screen. Nothing identifiable leaves the phone.").font(.footnote).foregroundStyle(.secondary).multilineTextAlignment(.center)
            Button(node.running ? "Stop" : "Start") { node.running ? node.stop() : node.start() }.buttonStyle(.borderedProminent)
            Spacer()
        }
        .padding()
    }

    private var flowText: String {
        guard let o = node.lastObservation else { return "–" }
        let dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        return "\(dirs[Int((o.flowDirectionDeg + 22.5).truncatingRemainder(dividingBy: 360) / 45) % 8]) (\(Int(o.flowDirectionDeg))°)"
    }

    private func stat(_ k: String, _ v: String) -> some View {
        VStack(alignment: .leading) { Text(k).font(.caption).foregroundStyle(.secondary); Text(v).font(.headline).lineLimit(1) }
    }
}

struct CameraPreview: UIViewRepresentable {
    let session: AVCaptureSession
    func makeUIView(context: Context) -> PreviewView { let v = PreviewView(); v.videoPreviewLayer.session = session; v.videoPreviewLayer.videoGravity = .resizeAspectFill; return v }
    func updateUIView(_ uiView: PreviewView, context: Context) {}
    final class PreviewView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
        var videoPreviewLayer: AVCaptureVideoPreviewLayer { layer as! AVCaptureVideoPreviewLayer }
    }
}
