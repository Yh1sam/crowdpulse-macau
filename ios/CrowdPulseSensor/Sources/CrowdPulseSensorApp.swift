import SwiftUI

@main
struct CrowdPulseSensorApp: App {
    @StateObject private var settings: SensorSettings
    @StateObject private var node: SensorNode

    init() {
        let s = SensorSettings()
        _settings = StateObject(wrappedValue: s)
        _node = StateObject(wrappedValue: SensorNode(settings: s))
    }

    var body: some Scene {
        WindowGroup {
            TabView {
                SetupView().tabItem { Label("Setup", systemImage: "gearshape") }
                LiveView().tabItem { Label("Live", systemImage: "camera.viewfinder") }
                PrivacyView().tabItem { Label("Privacy", systemImage: "lock.shield") }
                DebugView().tabItem { Label("Debug", systemImage: "waveform.path.ecg") }
            }
            .environmentObject(settings)
            .environmentObject(node)
        }
    }
}
