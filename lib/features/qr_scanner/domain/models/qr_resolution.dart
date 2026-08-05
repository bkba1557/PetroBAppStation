import 'package:equatable/equatable.dart';

class QrPayloadReference extends Equatable {
  const QrPayloadReference({required this.token});
  final String token;
  @override
  List<Object> get props => [token];
}

class QrResolution extends Equatable {
  const QrResolution({
    required this.resolutionId,
    required this.stationId,
    required this.pumpId,
    required this.nozzleId,
    required this.fuelProductId,
    required this.expiresAt,
    required this.singleUse,
  });
  final String resolutionId;
  final String stationId;
  final String pumpId;
  final String nozzleId;
  final String fuelProductId;
  final DateTime expiresAt;
  final bool singleUse;

  factory QrResolution.fromJson(Map<String, dynamic> json) => QrResolution(
        resolutionId: json['resolutionId'] as String,
        stationId: json['stationId'] as String,
        pumpId: json['pumpId'] as String,
        nozzleId: json['nozzleId'] as String,
        fuelProductId: json['fuelProductId'] as String,
        expiresAt: DateTime.parse(json['expiresAt'] as String),
        singleUse: json['singleUse'] as bool? ?? true,
      );

  @override
  List<Object> get props => [
        resolutionId,
        stationId,
        pumpId,
        nozzleId,
        fuelProductId,
        expiresAt,
        singleUse,
      ];
}

class QrValidationResult extends Equatable {
  const QrValidationResult({required this.isValid, this.resolution, this.code});
  final bool isValid;
  final QrResolution? resolution;
  final String? code;
  @override
  List<Object?> get props => [isValid, resolution, code];
}
