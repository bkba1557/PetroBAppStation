import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/features/stations/domain/models/station.dart';

Map<String, dynamic> stationJson({
  List<dynamic> prices = const [],
  String reason = 'HARDWARE_FUELING_DISABLED',
  String status = 'PILOT',
  bool companyEnabled = true,
  bool stationEnabled = true,
  bool selfServiceEnabled = true,
  bool hardwareEnabled = false,
  bool edgeOnline = true,
  bool appFuelingAvailable = false,
}) => {
  'id': 'STATION-HAIL-001',
  'name': 'PETRO B Hail Station',
  'companyId': '7',
  'companyNameAr': 'شركة بترول ب',
  'companyNameEn': 'Petro B Company',
  'location': {'latitude': 27.5, 'longitude': 41.7, 'address': 'Hail'},
  'operatingStatus': 'open',
  'fuelPrices': prices,
  'services': <dynamic>[],
  'stationVisible': true,
  'companySelfServiceEnabled': companyEnabled,
  'stationSelfServiceEnabled': stationEnabled,
  'selfServiceEnabled': selfServiceEnabled,
  'hardwareFuelingEnabled': hardwareEnabled,
  'edgeOnline': edgeOnline,
  'availabilityStatus': status,
  'availabilityReason': reason,
  'appFuelingAvailable': appFuelingAvailable,
};

Map<String, dynamic> priceJson(String code, {double price = 2.36}) => {
  'product': {
    'id': code,
    'code': code,
    'rawCode': code,
    'name': code,
    'nameAr': 'بنزين 95',
    'nameEn': 'Gasoline 95',
  },
  'unitPrice': price,
  'currency': 'SAR',
  'effectiveAt': '2026-08-03T19:02:33.115576+00:00',
};

void main() {
  test('converts station JSON into distinct availability state', () {
    final station = Station.fromJson(stationJson());
    expect(station.operatingStatus, StationOperatingStatus.open);
    expect(station.location.latitude, 27.5);
    expect(station.companyId, '7');
    expect(station.localizedCompanyName('en'), 'Petro B Company');
    expect(station.availability.stationVisible, isTrue);
    expect(station.selfServiceAvailable, isTrue);
    expect(station.appFuelingAvailable, isFalse);
    expect(
      station.availability.reason,
      StationAvailabilityReason.hardwareFuelingDisabled,
    );
  });

  test('hardware disabled never hides returned fuel prices', () {
    final station = Station.fromJson(
      stationJson(
        prices: [
          priceJson('gasoline91', price: 2.21),
          priceJson('gasoline95'),
          priceJson('diesel', price: 1.82),
        ],
      ),
    );
    expect(station.appFuelingAvailable, isFalse);
    expect(station.fuelPrices.map((item) => item.product.code), [
      'gasoline91',
      'gasoline95',
      'diesel',
    ]);
  });

  test('Flutter renders only products returned by the API', () {
    final station = Station.fromJson(stationJson(prices: [priceJson('lpg')]));
    expect(station.fuelPrices, hasLength(1));
    expect(station.fuelPrices.single.product.kind, FuelKind.lpg);
  });

  test('Gasoline 95 preserves bilingual API names', () {
    final product = FuelProduct.fromJson(
      priceJson('gasoline95')['product'] as Map<String, dynamic>,
    );
    expect(product.kind, FuelKind.gasoline95);
    expect(product.localizedName('ar'), 'بنزين 95');
    expect(product.localizedName('en'), 'Gasoline 95');
  });

  test('Gasoline 98 is recognized as a distinct available product', () {
    final product = FuelProduct.fromJson(
      priceJson('gasoline98')['product'] as Map<String, dynamic>,
    );
    expect(product.kind, FuelKind.gasoline98);
  });

  for (final entry in <String, String>{
    'gasoline91': 'gasoline91',
    'gasoline_91': 'gasoline91',
    'GASOLINE_91': 'gasoline91',
    '91': 'gasoline91',
    'gasoline95': 'gasoline95',
    'gasoline_95': 'gasoline95',
    'GASOLINE_95': 'gasoline95',
    '95': 'gasoline95',
    '98': 'gasoline98',
    'GASOLINE_98': 'gasoline98',
    'DIESEL': 'diesel',
    'Kerosene': 'kerosene',
    'LPG': 'lpg',
    'bio-fuel': 'bio_fuel',
  }.entries) {
    test('normalizes historical fuel code ${entry.key}', () {
      expect(normalizeFuelCode(entry.key), entry.value);
    });
  }

  for (final entry in <String, StationAvailabilityReason>{
    'AVAILABLE': StationAvailabilityReason.available,
    'COMPANY_SELF_SERVICE_DISABLED':
        StationAvailabilityReason.companySelfServiceDisabled,
    'STATION_SELF_SERVICE_DISABLED':
        StationAvailabilityReason.stationSelfServiceDisabled,
    'STATION_MAINTENANCE': StationAvailabilityReason.stationMaintenance,
    'HARDWARE_FUELING_DISABLED':
        StationAvailabilityReason.hardwareFuelingDisabled,
    'EDGE_OFFLINE': StationAvailabilityReason.edgeOffline,
    'NO_COMPATIBLE_NOZZLE': StationAvailabilityReason.noCompatibleNozzle,
    'FUEL_PRICE_UNAVAILABLE': StationAvailabilityReason.fuelPriceUnavailable,
    'SELF_SERVICE_OUTSIDE_SCHEDULE': StationAvailabilityReason.outsideSchedule,
  }.entries) {
    test('maps availability reason ${entry.key}', () {
      expect(availabilityReasonFromJson(entry.key), entry.value);
    });
  }

  test('PILOT and ACTIVE remain business statuses, not hardware flags', () {
    final pilot = Station.fromJson(stationJson(status: 'PILOT'));
    final active = Station.fromJson(
      stationJson(
        status: 'ACTIVE',
        reason: 'AVAILABLE',
        hardwareEnabled: true,
        appFuelingAvailable: true,
      ),
    );
    expect(pilot.availability.status, 'PILOT');
    expect(pilot.availability.hardwareFuelingEnabled, isFalse);
    expect(active.availability.status, 'ACTIVE');
    expect(active.appFuelingAvailable, isTrue);
  });

  test('decodes station route metrics', () {
    final route = StationRouteMetrics.fromJson({
      'stationId': 'station-1',
      'distanceMeters': 10750,
      'durationSeconds': 821.2,
    });

    expect(route.stationId, 'station-1');
    expect(route.distanceMeters, 10750);
    expect(route.durationSeconds, 821);
  });
}
