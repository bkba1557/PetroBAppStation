import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/stations/domain/models/station.dart';
import 'package:nnexoris_customer/features/stations/domain/repositories/station_repository.dart';

class StationRepositoryImpl implements StationRepository {
  StationRepositoryImpl(this._client);
  final HttpClient _client;
  var _refreshSequence = 0;

  String get _refreshToken =>
      '${DateTime.now().microsecondsSinceEpoch}-${_refreshSequence++}';

  @override
  Future<List<Station>> getStations([
    StationQuery query = const StationQuery(),
  ]) async {
    final response = await _client.get<List<Station>>(
      ApiEndpoints.stations,
      query: {
        ...query.toQuery(),
        '_refresh': _refreshToken,
      },
      decode: (json) => (json as List<dynamic>)
          .map((item) => Station.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
    );
    return response.data;
  }

  @override
  Future<Station> getStation(String stationId) async {
    final response = await _client.get<Station>(
      '${ApiEndpoints.stations}/$stationId',
      query: {'_refresh': _refreshToken},
      decode: (json) => Station.fromJson(json as Map<String, dynamic>),
    );
    return response.data;
  }

  @override
  Future<List<FuelPrice>> getFuelPrices(String stationId) async {
    final response = await _client.get<List<FuelPrice>>(
      '${ApiEndpoints.stations}/$stationId/fuel-prices',
      query: {'_refresh': _refreshToken},
      decode: (json) => (json as List<dynamic>)
          .map((item) => FuelPrice.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
    );
    return response.data;
  }

  @override
  Future<StationAvailability> getAvailability(String stationId) async {
    final response = await _client.get<StationAvailability>(
      '${ApiEndpoints.stations}/$stationId/availability',
      query: {'_refresh': _refreshToken},
      decode: (json) =>
          StationAvailability.fromJson(json as Map<String, dynamic>),
    );
    return response.data;
  }
}
