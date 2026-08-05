import 'package:equatable/equatable.dart';

class RealtimeEvent extends Equatable {
  const RealtimeEvent({
    required this.eventId,
    required this.eventType,
    required this.entityId,
    required this.sequence,
    required this.occurredAt,
    required this.payload,
  });

  final String eventId;
  final String eventType;
  final String entityId;
  final int sequence;
  final DateTime occurredAt;
  final Map<String, dynamic> payload;

  factory RealtimeEvent.fromJson(Map<String, dynamic> json) => RealtimeEvent(
        eventId: json['eventId'] as String,
        eventType: json['eventType'] as String,
        entityId: json['entityId'] as String,
        sequence: json['sequence'] as int,
        occurredAt: DateTime.parse(json['occurredAt'] as String),
        payload: Map<String, dynamic>.from(json['payload'] as Map),
      );

  @override
  List<Object> get props =>
      [eventId, eventType, entityId, sequence, occurredAt, payload];
}

class FuelingProgressEvent extends Equatable {
  const FuelingProgressEvent({
    required this.sessionId,
    required this.amount,
    required this.volume,
    required this.sequence,
  });
  final String sessionId;
  final double amount;
  final double volume;
  final int sequence;
  @override
  List<Object> get props => [sessionId, amount, volume, sequence];
}

class WalletBalanceUpdatedEvent extends Equatable {
  const WalletBalanceUpdatedEvent({
    required this.walletId,
    required this.available,
    required this.reserved,
    required this.version,
  });
  final String walletId;
  final double available;
  final double reserved;
  final int version;
  @override
  List<Object> get props => [walletId, available, reserved, version];
}
