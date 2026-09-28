import SwiftUI

struct PrivacyView: View {
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Text("No facial recognition.\nNo identifiable video is transmitted.").font(.title2.bold())
                    Text("This phone counts people anonymously. Camera frames are analysed on the device and discarded immediately. Only numbers are sent to the operations backend:")
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(["timestamp and anonymous node id", "GPS position and accuracy of this phone", "compass heading of the camera", "device stability (accelerometer / gyroscope)", "number of people in view and a relative density index", "dominant movement direction and speed", "vision confidence and an obstruction flag"], id: \.self) { Text("• " + $0) }
                    }
                    Text("Never collected: images, video, faces, face embeddings, biometrics, names, device serial numbers or per-person tracks. Individuals are not followed between frames or between phones.")
                    Text("PRIVACY_MODE is enforced on the server: it rejects any image or video upload and any field not in the numerical schema.").font(.footnote).foregroundStyle(.secondary)
                }.padding()
            }
            .navigationTitle("Privacy")
        }
    }
}
