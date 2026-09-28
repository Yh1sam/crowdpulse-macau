import Foundation
import CoreLocation
import Combine

/// GPS position/accuracy of the sensor node and the compass heading the camera faces.
final class LocationMonitor: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var latitude: Double = 0
    @Published var longitude: Double = 0
    @Published var accuracyM: Double = 10000
    @Published var headingDeg: Double = 0
    @Published var headingAccuracy: Double = -1
    @Published var authorized = false
    @Published var hasFix = false

    private let manager = CLLocationManager()

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.headingFilter = 2
    }

    func start() {
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()
        if CLLocationManager.headingAvailable() { manager.startUpdatingHeading() }
    }

    func stop() { manager.stopUpdatingLocation(); manager.stopUpdatingHeading() }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorized = manager.authorizationStatus == .authorizedWhenInUse || manager.authorizationStatus == .authorizedAlways
        if authorized { manager.startUpdatingLocation() }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let l = locations.last, l.horizontalAccuracy >= 0 else { return }
        latitude = l.coordinate.latitude
        longitude = l.coordinate.longitude
        accuracyM = l.horizontalAccuracy
        hasFix = true
    }

    func locationManager(_ manager: CLLocationManager, didUpdateHeading newHeading: CLHeading) {
        headingDeg = newHeading.trueHeading >= 0 ? newHeading.trueHeading : newHeading.magneticHeading
        headingAccuracy = newHeading.headingAccuracy
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) { /* keep last fix; accuracy field reports it */ }
}
