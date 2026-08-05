import 'package:nnexoris_customer/features/stations/domain/models/station.dart';

class StationQuery {
  const StationQuery({this.latitude, this.longitude});
  final double? latitude;
  final double? longitude;

  Map<String, dynamic> toQuery() => {
    if (latitude != null) 'latitude': latitude,
    if (longitude != null) 'longitude': longitude,
  };
}

abstract interface class StationRepository {
  Future<List<Station>> getStations([
    StationQuery query = const StationQuery(),
  ]);
  Future<Station> getStation(String stationId);
  Future<List<FuelPrice>> getFuelPrices(String stationId);
  Future<StationAvailability> getAvailability(String stationId);
}

class GeoPosition {
  const GeoPosition({required this.latitude, required this.longitude});
  final double latitude;
  final double longitude;
}

abstract interface class LocationService {
  /// Returns null when permission is denied or location is unavailable.
  Future<GeoPosition?> currentLocation();
}
