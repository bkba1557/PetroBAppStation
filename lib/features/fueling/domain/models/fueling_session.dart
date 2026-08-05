import 'package:equatable/equatable.dart';

enum FuelingSessionStatus {
  created,
  awaitingFunds,
  fundsHeld,
  qrResolved,
  authorizationQueued,
  edgeReceived,
  pumpWaiting,
  pumpAuthorized,
  readyToFuel,
  fueling,
  stopRequested,
  completed,
  settlementPending,
  settled,
  cancelled,
  failed,
  expired,
  refundPending,
  refunded,
}

String _stateName(String value) {
  final words = value.toLowerCase().split('_');
  return words.first +
      words.skip(1).map((word) =>
          word.isEmpty ? '' : '${word[0].toUpperCase()}${word.substring(1)}').join();
}

enum FuelingMode { fixedAmount, fillUp }

class FuelingSelection extends Equatable {
  const FuelingSelection({
    required this.qrResolutionId,
    required this.requestedMode,
    this.requestedAmount,
    this.maximumAuthorizationAmount,
  });
  final String qrResolutionId;
  final FuelingMode requestedMode;
  final double? requestedAmount;
  final double? maximumAuthorizationAmount;

  Map<String, dynamic> toJson() => {
        'qrResolutionId': qrResolutionId,
        'requestedMode': requestedMode.name,
        if (requestedAmount != null) 'requestedAmount': requestedAmount,
        if (maximumAuthorizationAmount != null)
          'maximumAuthorizationAmount': maximumAuthorizationAmount,
      };

  @override
  List<Object?> get props => [
        qrResolutionId,
        requestedMode,
        requestedAmount,
        maximumAuthorizationAmount,
      ];
}

class FuelingProgress extends Equatable {
  const FuelingProgress({
    required this.dispensedAmount,
    required this.dispensedVolume,
    required this.unitPrice,
    required this.sequence,
    required this.observedAt,
  });
  final double dispensedAmount;
  final double dispensedVolume;
  final double unitPrice;
  final int sequence;
  final DateTime observedAt;
  @override
  List<Object> get props =>
      [dispensedAmount, dispensedVolume, unitPrice, sequence, observedAt];
}

class FuelingReceipt extends Equatable {
  const FuelingReceipt({
    required this.receiptId,
    required this.finalAmount,
    required this.finalVolume,
    required this.currency,
  });
  final String receiptId;
  final double finalAmount;
  final double finalVolume;
  final String currency;
  @override
  List<Object> get props => [receiptId, finalAmount, finalVolume, currency];
}

class FuelingFailure extends Equatable {
  const FuelingFailure({required this.code, required this.safeMessage});
  final String code;
  final String safeMessage;
  @override
  List<Object> get props => [code, safeMessage];
}

class FuelingAuthorization extends Equatable {
  const FuelingAuthorization({
    required this.reservedAmount,
    required this.expiresAt,
  });
  final double reservedAmount;
  final DateTime expiresAt;
  @override
  List<Object> get props => [reservedAmount, expiresAt];
}

class FuelingSession extends Equatable {
  const FuelingSession({
    required this.sessionId,
    required this.transactionId,
    required this.idempotencyKey,
    required this.customerId,
    required this.stationId,
    required this.pumpId,
    required this.nozzleId,
    required this.fuelProductId,
    required this.requestedMode,
    required this.reservedAmount,
    required this.dispensedAmount,
    required this.dispensedVolume,
    required this.unitPrice,
    required this.status,
    required this.createdAt,
    required this.expiresAt,
    this.requestedAmount,
    this.maximumAuthorizationAmount,
    this.startedAt,
    this.completedAt,
    this.failureCode,
    this.failureMessage,
  });

  final String sessionId;
  final String transactionId;
  final String idempotencyKey;
  final String customerId;
  final String stationId;
  final String pumpId;
  final String nozzleId;
  final String fuelProductId;
  final FuelingMode requestedMode;
  final double? requestedAmount;
  final double? maximumAuthorizationAmount;
  final double reservedAmount;
  final double dispensedAmount;
  final double dispensedVolume;
  final double unitPrice;
  final FuelingSessionStatus status;
  final DateTime createdAt;
  final DateTime expiresAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final String? failureCode;
  final String? failureMessage;

  bool get isFinal => const {
        FuelingSessionStatus.settled,
        FuelingSessionStatus.cancelled,
        FuelingSessionStatus.failed,
        FuelingSessionStatus.expired,
      }.contains(status);

  bool get isSuccessful => status == FuelingSessionStatus.settled;

  factory FuelingSession.fromJson(Map<String, dynamic> json) => FuelingSession(
        sessionId: json['sessionId'] as String,
        transactionId: json['transactionId'] as String,
        idempotencyKey: json['idempotencyKey'] as String,
        customerId: json['customerId'] as String,
        stationId: json['stationId'] as String,
        pumpId: json['pumpId'] as String,
        nozzleId: json['nozzleId'] as String,
        fuelProductId: json['fuelProductId'] as String,
        requestedMode: FuelingMode.values.byName(json['requestedMode'] as String),
        requestedAmount: (json['requestedAmount'] as num?)?.toDouble(),
        maximumAuthorizationAmount:
            (json['maximumAuthorizationAmount'] as num?)?.toDouble(),
        reservedAmount: (json['reservedAmount'] as num).toDouble(),
        dispensedAmount: (json['dispensedAmount'] as num).toDouble(),
        dispensedVolume: (json['dispensedVolume'] as num).toDouble(),
        unitPrice: (json['unitPrice'] as num).toDouble(),
        status: FuelingSessionStatus.values.byName(
          _stateName(json['status'] as String),
        ),
        createdAt: DateTime.parse(json['createdAt'] as String),
        expiresAt: DateTime.parse(json['expiresAt'] as String),
        startedAt: json['startedAt'] == null
            ? null
            : DateTime.parse(json['startedAt'] as String),
        completedAt: json['completedAt'] == null
            ? null
            : DateTime.parse(json['completedAt'] as String),
        failureCode: json['failureCode'] as String?,
        failureMessage: json['failureMessage'] as String?,
      );

  @override
  List<Object?> get props => [
        sessionId,
        transactionId,
        idempotencyKey,
        customerId,
        stationId,
        pumpId,
        nozzleId,
        fuelProductId,
        requestedMode,
        requestedAmount,
        maximumAuthorizationAmount,
        reservedAmount,
        dispensedAmount,
        dispensedVolume,
        unitPrice,
        status,
        createdAt,
        expiresAt,
        startedAt,
        completedAt,
        failureCode,
        failureMessage,
      ];
}
