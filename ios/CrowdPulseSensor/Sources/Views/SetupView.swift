import SwiftUI

struct SetupView: View {
    @EnvironmentObject var settings: SensorSettings
    @EnvironmentObject var node: SensorNode
    @StateObject private var catalog = ZoneCatalog()

    var body: some View {
        NavigationStack {
            Form {
                Section("Sensor") {
                    TextField("Sensor name (local only)", text: $settings.sensorName)
                    HStack { Text("Anonymous node id"); Spacer(); Text(settings.sensorId).font(.system(.body, design: .monospaced)) }
                    Button("Regenerate id") { settings.regenerateId() }
                    Picker("Mode", selection: $settings.mode) { ForEach(SensorSettings.SensorMode.allCases) { Text($0.rawValue.capitalized).tag($0) } }
                    Picker("Detector", selection: $settings.detector) { ForEach(SensorSettings.DetectorChoice.allCases) { Text($0.label).tag($0) } }
                }
                Section {
                    if catalog.zones.isEmpty {
                        TextField("Zone id (e.g. senado_square)", text: $settings.zoneHint).autocapitalization(.none)
                    } else {
                        Picker("Zone", selection: $settings.zoneHint) {
                            Text("By GPS only").tag("")
                            ForEach(catalog.zones) { Text($0.name).tag($0.id) }
                            if !settings.zoneHint.isEmpty && !catalog.zones.contains(where: { $0.id == settings.zoneHint }) {
                                Text("\(settings.zoneHint) (unknown)").tag(settings.zoneHint)
                            }
                        }
                    }
                    Button("Reload zones from backend") { catalog.load(backendURL: settings.backendURL) }
                    Text(catalog.status).font(.footnote).foregroundStyle(.secondary)
                } header: {
                    Text("Placement")
                } footer: {
                    Text("Inside the Macau district the phone is placed by GPS. Anywhere else (a school, at home) it joins the zone chosen here.")
                }
                Section("Backend") {
                    TextField("Backend URL", text: $settings.backendURL).keyboardType(.URL).autocapitalization(.none)
                        .onSubmit { catalog.load(backendURL: settings.backendURL) }
                    Stepper("Send every \(Int(settings.intervalSeconds)) s", value: $settings.intervalSeconds, in: 1...5, step: 1).onChange(of: settings.intervalSeconds) { _, _ in node.restartTimer() }
                }
                Section("Calibration") {
                    Stepper("Visible capacity: \(Int(settings.visibleCapacity)) people", value: $settings.visibleCapacity, in: 5...500, step: 5)
                    Stepper("Visible width: \(Int(settings.visibleWidthMeters)) m", value: $settings.visibleWidthMeters, in: 2...40, step: 1)
                    Text("Density index = people in view ÷ visible capacity (relative 0–1, not persons/m²).").font(.footnote).foregroundStyle(.secondary)
                }
                Section("Status") {
                    row("GPS", node.location.hasFix ? String(format: "±%.0f m", node.location.accuracyM) : (node.location.authorized ? "waiting for fix" : "not authorised"))
                    row("Heading", String(format: "%.0f°", node.location.headingDeg))
                    row("Camera", settings.mode == .simulated ? "simulated" : (node.cameraAuthorized ? "on" : "off / not authorised"))
                    row("ML", node.mlStatus)
                    row("Motion stability", String(format: "%.2f", node.motion.stability))
                    row("Upload", node.uploader.lastStatus)
                }
                Section {
                    Button(node.running ? "Stop sensing" : "Start sensing") { node.running ? node.stop() : node.start() }
                        .frame(maxWidth: .infinity).font(.headline)
                }
            }
            .navigationTitle("Sensor setup")
            .onAppear { if catalog.zones.isEmpty { catalog.load(backendURL: settings.backendURL) } }
        }
    }

    private func row(_ k: String, _ v: String) -> some View { HStack { Text(k); Spacer(); Text(v).foregroundStyle(.secondary).multilineTextAlignment(.trailing) } }
}
