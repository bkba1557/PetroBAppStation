import 'package:geolocator/geolocator.dart';
import 'package:nnexoris_customer/features/stations/domain/repositories/station_repository.dart';

class DeviceLocationService implements LocationService {
  @override
  Future<LocationAccessStatus> accessStatus() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      return LocationAccessStatus.serviceDisabled;
    }
    return _mapPermission(await Geolocator.checkPermission());
  }

  @override
  Future<LocationAccessStatus> requestAccess() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      return LocationAccessStatus.serviceDisabled;
    }
    return _mapPermission(await Geolocator.requestPermission());
  }

  @override
  Future<bool> openAppSettings() => Geolocator.openAppSettings();

  @override
  Future<bool> openLocationSettings() => Geolocator.openLocationSettings();

  @override
  Future<GeoPosition?> currentLocation() async {
    if (await accessStatus() != LocationAccessStatus.granted) return null;

    final position = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        timeLimit: Duration(seconds: 12),
      ),
    );
    return GeoPosition(
      latitude: position.latitude,
      longitude: position.longitude,
    );
  }

  LocationAccessStatus _mapPermission(LocationPermission permission) =>
      switch (permission) {
        LocationPermission.always ||
        LocationPermission.whileInUse => LocationAccessStatus.granted,
        LocationPermission.deniedForever => LocationAccessStatus.deniedForever,
        LocationPermission.denied ||
        LocationPermission.unableToDetermine => LocationAccessStatus.denied,
      };
}
