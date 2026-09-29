import Foundation
import Combine

/// The zones the backend knows, loaded from `GET /config`, so the operator picks a zone instead of typing its id.
/// The chosen zone is sent as `zone_hint`. The backend uses it when the phone's GPS is not within a zone
/// (school experiment, indoor test, a phone at home joining the demo); inside the district GPS wins.
@MainActor
final class ZoneCatalog: ObservableObject {
    struct Zone: Decodable, Identifiable, Hashable {
        let id: String
        let name: String
    }

    @Published private(set) var zones: [Zone] = []
    @Published private(set) var status: String = "not loaded"

    private struct ConfigResponse: Decodable {
        struct Graph: Decodable { let zones: [Zone] }
        let zoneGraph: Graph
        enum CodingKeys: String, CodingKey { case zoneGraph = "zone_graph" }
    }

    static func decode(_ data: Data) throws -> [Zone] {
        try JSONDecoder().decode(ConfigResponse.self, from: data).zoneGraph.zones
    }

    func load(backendURL: String, session: URLSession = .shared) {
        guard let url = URL(string: backendURL.trimmingCharacters(in: .whitespaces))?.appendingPathComponent("config") else {
            status = "invalid backend URL"; return
        }
        status = "loading…"
        var req = URLRequest(url: url)
        req.timeoutInterval = 6
        session.dataTask(with: req) { [weak self] data, resp, error in
            let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
            let result: Result<[Zone], Error>
            if let data, error == nil, (200..<300).contains(code) {
                result = Result { try ZoneCatalog.decode(data) }
            } else {
                result = .failure(error ?? URLError(.badServerResponse))
            }
            Task { @MainActor in
                guard let self else { return }
                switch result {
                case .success(let zones):
                    self.zones = zones
                    self.status = "\(zones.count) zones"
                case .failure:
                    self.status = "could not load zones (backend unreachable?)"
                }
            }
        }.resume()
    }
}
