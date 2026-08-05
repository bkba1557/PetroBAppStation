import 'package:equatable/equatable.dart';

enum StationOperatingStatus { open, closed, temporarilyUnavailable, unknown }

enum FuelKind { gasoline91, gasoline95, diesel, kerosene, lpg, other }

enum StationAvailabilityReason {
  available,
  companySelfServiceDisabled,
  stationSelfServiceDisabled,
  stationMaintenance,
  hardwareFuelingDisabled,
  edgeOffline,
  noCompatibleNozzle,
  fuelPriceUnavailable,
  outsideSchedule,
  unknown,
}

String normalizeFuelCode(Object? value) {
  final raw = (value?.toString() ?? '').trim().toLowerCase();
  final compact = raw.replaceAll(RegExp('[^a-z0-9]'), '');
  return switch (compact) {
    '91' || 'gasoline91' || 'petrol91' => 'gasoline91',
    '95' || 'gasoline95' || 'petrol95' => 'gasoline95',
    'diesel' => 'diesel',
    'kerosene' => 'kerosene',
    'lpg' => 'lpg',
    _ =>
      raw
          .replaceAll(RegExp('[^a-z0-9]+'), '_')
          .replaceAll(RegExp(r'^_+|_+$'), ''),
  };
}

FuelKind fuelKindForCode(Object? value) => switch (normalizeFuelCode(value)) {
  'gasoline91' => FuelKind.gasoline91,
  'gasoline95' => FuelKind.gasoline95,
  'diesel' => FuelKind.diesel,
  'kerosene' => FuelKind.kerosene,
  'lpg' => FuelKind.lpg,
  _ => FuelKind.other,
};

StationAvailabilityReason availabilityReasonFromJson(
  Object? value,
) => switch (value?.toString().toUpperCase()) {
  'AVAILABLE' => StationAvailabilityReason.available,
  'COMPANY_SELF_SERVICE_DISABLED' =>
    StationAvailabilityReason.companySelfServiceDisabled,
  'STATION_SELF_SERVICE_DISABLED' =>
    StationAvailabilityReason.stationSelfServiceDisabled,
  'STATION_MAINTENANCE' => StationAvailabilityReason.stationMaintenance,
  'HARDWARE_FUELING_DISABLED' =>
    StationAvailabilityReason.hardwareFuelingDisabled,
  'EDGE_OFFLINE' => StationAvailabilityReason.edgeOffline,
  'NO_COMPATIBLE_NOZZLE' => StationAvailabilityReason.noCompatibleNozzle,
  'FUEL_PRICE_UNAVAILABLE' => StationAvailabilityReason.fuelPriceUnavailable,
  'SELF_SERVICE_OUTSIDE_SCHEDULE' => StationAvailabilityReason.outsideSchedule,
  _ => StationAvailabilityReason.unknown,
};

class StationLocation extends Equatable {
  const StationLocation({
    required this.latitude,
    required this.longitude,
    required this.address,
  });

  final double latitude;
  final double longitude;
  final String address;

  factory StationLocation.fromJson(Map<String, dynamic> json) =>
      StationLocation(
        latitude: (json['latitude'] as num? ?? 0).toDouble(),
        longitude: (json['longitude'] as num? ?? 0).toDouble(),
        address: json['address'] as String? ?? '',
      );

  @override
  List<Object> get props => [latitude, longitude, address];
}

class FuelProduct extends Equatable {
  const FuelProduct({
    required this.id,
    required this.code,
    required this.rawCode,
    required this.kind,
    required this.name,
    required this.nameAr,
    required this.nameEn,
  });

  final String id;
  final String code;
  final String rawCode;
  final FuelKind kind;
  final String name;
  final String nameAr;
  final String nameEn;

  factory FuelProduct.fromJson(Map<String, dynamic> json) {
    final rawCode = (json['rawCode'] ?? json['code'] ?? json['id'] ?? '')
        .toString();
    final code = normalizeFuelCode(json['code'] ?? rawCode);
    final fallback = (json['name'] ?? code).toString();
    return FuelProduct(
      id: (json['id'] ?? code).toString(),
      code: code,
      rawCode: rawCode,
      kind: fuelKindForCode(code),
      name: fallback,
      nameAr: (json['nameAr'] ?? fallback).toString(),
      nameEn: (json['nameEn'] ?? fallback).toString(),
    );
  }

  String localizedName(String languageCode) =>
      languageCode == 'ar' ? nameAr : nameEn;

  @override
  List<Object> get props => [id, code, rawCode, kind, name, nameAr, nameEn];
}

class FuelPrice extends Equatable {
  const FuelPrice({
    required this.product,
    required this.unitPrice,
    required this.currency,
    required this.effectiveAt,
  });

  final FuelProduct product;
  final double unitPrice;
  final String currency;
  final DateTime effectiveAt;

  factory FuelPrice.fromJson(Map<String, dynamic> json) => FuelPrice(
    product: FuelProduct.fromJson(json['product'] as Map<String, dynamic>),
    unitPrice: (json['unitPrice'] as num).toDouble(),
    currency: json['currency'] as String? ?? 'SAR',
    effectiveAt: DateTime.parse(json['effectiveAt'] as String),
  );

  @override
  List<Object> get props => [product, unitPrice, currency, effectiveAt];
}

class StationService extends Equatable {
  const StationService({required this.code, required this.name});
  final String code;
  final String name;

  factory StationService.fromJson(Map<String, dynamic> json) => StationService(
    code: json['code'] as String,
    name: json['name'] as String,
  );

  @override
  List<Object> get props => [code, name];
}

class StationAvailability extends Equatable {
  const StationAvailability({
    required this.stationVisible,
    required this.companySelfServiceEnabled,
    required this.stationSelfServiceEnabled,
    required this.selfServiceEnabled,
    required this.hardwareFuelingEnabled,
    required this.edgeOnline,
    required this.status,
    required this.reason,
    required this.appFuelingAvailable,
  });

  final bool stationVisible;
  final bool companySelfServiceEnabled;
  final bool stationSelfServiceEnabled;
  final bool selfServiceEnabled;
  final bool hardwareFuelingEnabled;
  final bool edgeOnline;
  final String status;
  final StationAvailabilityReason reason;
  final bool appFuelingAvailable;

  factory StationAvailability.fromJson(
    Map<String, dynamic> json,
  ) => StationAvailability(
    stationVisible: json['stationVisible'] as bool? ?? true,
    companySelfServiceEnabled:
        json['companySelfServiceEnabled'] as bool? ?? false,
    stationSelfServiceEnabled:
        json['stationSelfServiceEnabled'] as bool? ?? false,
    selfServiceEnabled:
        json['selfServiceEnabled'] as bool? ??
        json['selfServiceAvailable'] as bool? ??
        false,
    hardwareFuelingEnabled: json['hardwareFuelingEnabled'] as bool? ?? false,
    edgeOnline: json['edgeOnline'] as bool? ?? false,
    status:
        (json['availabilityStatus'] ?? json['selfServiceStatus'] ?? 'DISABLED')
            .toString(),
    reason: availabilityReasonFromJson(json['availabilityReason']),
    appFuelingAvailable: json['appFuelingAvailable'] as bool? ?? false,
  );

  @override
  List<Object> get props => [
    stationVisible,
    companySelfServiceEnabled,
    stationSelfServiceEnabled,
    selfServiceEnabled,
    hardwareFuelingEnabled,
    edgeOnline,
    status,
    reason,
    appFuelingAvailable,
  ];
}

class Station extends Equatable {
  const Station({
    required this.id,
    required this.name,
    required this.location,
    required this.operatingStatus,
    required this.fuelPrices,
    required this.services,
    required this.availability,
    this.logoUrl,
    this.distanceMeters,
    this.operatingHours,
  });

  final String id;
  final String name;
  final String? logoUrl;
  final double? distanceMeters;
  final StationLocation location;
  final StationOperatingStatus operatingStatus;
  final List<FuelPrice> fuelPrices;
  final List<StationService> services;
  final StationAvailability availability;
  final String? operatingHours;

  bool get selfServiceAvailable => availability.selfServiceEnabled;
  bool get appFuelingAvailable => availability.appFuelingAvailable;

  factory Station.fromJson(Map<String, dynamic> json) {
    final operatingStatusName = json['operatingStatus'] as String? ?? 'unknown';
    return Station(
      id: json['id'] as String,
      name: json['name'] as String,
      logoUrl: json['logoUrl'] as String?,
      distanceMeters: (json['distanceMeters'] as num?)?.toDouble(),
      location: StationLocation.fromJson(
        json['location'] as Map<String, dynamic>,
      ),
      operatingStatus:
          StationOperatingStatus.values
              .where((value) => value.name == operatingStatusName)
              .firstOrNull ??
          StationOperatingStatus.unknown,
      fuelPrices: (json['fuelPrices'] as List<dynamic>? ?? const [])
          .map((item) => FuelPrice.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
      services: (json['services'] as List<dynamic>? ?? const [])
          .map((item) => StationService.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
      availability: StationAvailability.fromJson(json),
      operatingHours: json['operatingHours'] as String?,
    );
  }

  @override
  List<Object?> get props => [
    id,
    name,
    logoUrl,
    distanceMeters,
    location,
    operatingStatus,
    fuelPrices,
    services,
    availability,
    operatingHours,
  ];
}
