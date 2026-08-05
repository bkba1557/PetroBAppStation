import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/network/api_response.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/stations/data/station_repository_impl.dart';
import 'package:nnexoris_customer/features/stations/domain/models/station.dart';
import 'package:nnexoris_customer/features/stations/domain/repositories/station_repository.dart';

class RecordingHttpClient implements HttpClient {
  final List<(String, Map<String, dynamic>?)> gets = [];
  final List<(String, Object?)> posts = [];
  var mutationCount = 0;

  @override
  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? query,
    T Function(Object? json)? decode,
  }) async {
    gets.add((path, query));
    final payload = path.endsWith('/availability')
        ? <String, dynamic>{
            'stationVisible': true,
            'companySelfServiceEnabled': true,
            'stationSelfServiceEnabled': true,
            'selfServiceEnabled': true,
            'hardwareFuelingEnabled': false,
            'edgeOnline': true,
            'availabilityStatus': 'PILOT',
            'availabilityReason': 'HARDWARE_FUELING_DISABLED',
            'appFuelingAvailable': false,
          }
        : path.endsWith('/fuel-prices')
        ? <dynamic>[]
        : path == 'stations'
        ? <dynamic>[]
        : <String, dynamic>{
            'id': 'station-1',
            'name': 'Station',
            'location': {'latitude': 0, 'longitude': 0, 'address': ''},
            'operatingStatus': 'open',
            'fuelPrices': <dynamic>[],
            'services': <dynamic>[],
          };
    return ApiResponse<T>(data: decode!(payload));
  }

  @override
  Future<ApiResponse<T>> patch<T>(
    String path, {
    Object? data,
    T Function(Object? json)? decode,
  }) async {
    mutationCount += 1;
    throw UnimplementedError();
  }

  @override
  Future<ApiResponse<T>> post<T>(
    String path, {
    Object? data,
    String? idempotencyKey,
    T Function(Object? json)? decode,
  }) async {
    if (path.endsWith('/route-matrix')) {
      posts.add((path, data));
      return ApiResponse<T>(
        data: decode!({
          'routes': [
            {
              'stationId': 'station-1',
              'distanceMeters': 12500,
              'durationSeconds': 900,
            },
          ],
        }),
      );
    }
    mutationCount += 1;
    throw UnimplementedError();
  }

  @override
  Future<ApiResponse<void>> delete(String path) async {
    mutationCount += 1;
    throw UnimplementedError();
  }
}

void main() {
  test('every station refresh bypasses stale intermediary cache', () async {
    final client = RecordingHttpClient();
    final repository = StationRepositoryImpl(client);
    await repository.getStations();
    await repository.getStations();
    expect(client.gets, hasLength(2));
    expect(
      client.gets.every((call) => call.$2!.containsKey('_refresh')),
      isTrue,
    );
    expect(
      client.gets.first.$2!['_refresh'],
      isNot(client.gets.last.$2!['_refresh']),
    );
  });

  test('viewing prices and availability performs GET requests only', () async {
    final client = RecordingHttpClient();
    final repository = StationRepositoryImpl(client);
    await repository.getFuelPrices('station-1');
    final availability = await repository.getAvailability('station-1');
    expect(client.mutationCount, 0);
    expect(availability.hardwareFuelingEnabled, isFalse);
    expect(
      availability.reason,
      StationAvailabilityReason.hardwareFuelingDisabled,
    );
  });

  test('route matrix sends the origin and decodes Google route data', () async {
    final client = RecordingHttpClient();
    final repository = StationRepositoryImpl(client);
    final routes = await repository.getRouteMetrics(
      const GeoPosition(latitude: 24.7, longitude: 46.6),
      const ['station-1'],
    );

    expect(routes['station-1']?.distanceMeters, 12500);
    expect(routes['station-1']?.durationSeconds, 900);
    expect(client.posts.single.$1, 'stations/route-matrix');
    expect(client.mutationCount, 0);
  });
}
