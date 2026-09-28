import Foundation
import Combine

/// Sends observations to the backend. If the backend is unreachable the numerical
/// observations are buffered (JSON file, bounded size) and retried later. Never buffers video.
final class Uploader: ObservableObject {
    @Published var lastStatus: String = "idle"
    @Published var sent: Int = 0
    @Published var failed: Int = 0
    @Published var buffered: Int = 0
    @Published var lastZoneAssignment: String?
    @Published var lastServerTime: String?

    private let bufferURL: URL
    private var buffer: [SensorObservation] = []
    private let maxBuffer = 2000
    private let session: URLSession
    private var inFlight = false

    init(session: URLSession = .shared, bufferDirectory: URL? = nil) {
        self.session = session
        let dir = bufferDirectory ?? FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        bufferURL = dir.appendingPathComponent("crowdpulse_buffer.json")
        load()
    }

    func enqueue(_ obs: SensorObservation, backendURL: String) {
        buffer.append(obs.clamped())
        if buffer.count > maxBuffer { buffer.removeFirst(buffer.count - maxBuffer) }
        buffered = buffer.count
        persist()
        flush(backendURL: backendURL)
    }

    func flush(backendURL: String) {
        guard !inFlight, !buffer.isEmpty, let url = URL(string: backendURL.trimmingCharacters(in: .whitespaces))?.appendingPathComponent("sensor/observation") else { return }
        let batch = Array(buffer.prefix(200))
        guard let body = try? SensorObservation.encoder.encode(ObservationBatch(observations: batch)) else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = body
        req.timeoutInterval = 8
        inFlight = true
        session.dataTask(with: req) { [weak self] data, resp, error in
            DispatchQueue.main.async {
                guard let self else { return }
                self.inFlight = false
                let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
                if error == nil, (200..<300).contains(code) {
                    self.buffer.removeFirst(min(batch.count, self.buffer.count))
                    self.sent += batch.count
                    self.lastStatus = "sent \(batch.count) (HTTP \(code))"
                    if let data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        if let z = (json["zone_assignments"] as? [String: Any])?.values.first { self.lastZoneAssignment = "\(z)" }
                        self.lastServerTime = json["server_time"] as? String
                    }
                } else if code == 422 || code == 403 {
                    // schema/privacy rejection: drop the batch, never retry invalid payloads
                    self.buffer.removeFirst(min(batch.count, self.buffer.count))
                    self.failed += batch.count
                    self.lastStatus = "rejected by backend (HTTP \(code))"
                } else {
                    self.failed += 1
                    self.lastStatus = "offline — buffering (\(error?.localizedDescription ?? "HTTP \(code)"))"
                }
                self.buffered = self.buffer.count
                self.persist()
                if !self.buffer.isEmpty && (200..<300).contains(code) { self.flush(backendURL: backendURL) }
            }
        }.resume()
    }

    private func persist() { try? SensorObservation.encoder.encode(buffer).write(to: bufferURL, options: .atomic) }

    private func load() {
        let dec = JSONDecoder(); dec.dateDecodingStrategy = .iso8601
        if let data = try? Data(contentsOf: bufferURL), let b = try? dec.decode([SensorObservation].self, from: data) { buffer = b; buffered = b.count }
    }

    var pendingCount: Int { buffer.count }
}
