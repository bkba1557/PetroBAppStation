import 'package:equatable/equatable.dart';

enum WalletReservationStatus {
  pending,
  reserved,
  partiallyCaptured,
  captured,
  released,
  failed,
  expired,
}

enum WalletTopUpStatus {
  created,
  pendingPayment,
  paid,
  failed,
  cancelled,
  expired,
  refunded,
}

enum PaymentStatus { pending, authorized, paid, failed, cancelled, refunded }

class WalletBalance extends Equatable {
  const WalletBalance({
    required this.available,
    required this.reserved,
    required this.currency,
    required this.version,
  });
  final double available;
  final double reserved;
  final String currency;
  final int version;

  factory WalletBalance.fromJson(Map<String, dynamic> json) => WalletBalance(
        available: (json['available'] as num).toDouble(),
        reserved: (json['reserved'] as num).toDouble(),
        currency: json['currency'] as String,
        version: json['version'] as int,
      );

  @override
  List<Object> get props => [available, reserved, currency, version];
}

class Wallet extends Equatable {
  const Wallet({required this.id, required this.balance, required this.totalCredited,
    required this.totalSpent, required this.totalRefunded, required this.updatedAt});
  final String id;
  final WalletBalance balance;
  final double totalCredited;
  final double totalSpent;
  final double totalRefunded;
  final DateTime updatedAt;

  factory Wallet.fromJson(Map<String, dynamic> json) => Wallet(
        id: json['id'] as String,
        balance: WalletBalance.fromJson(json['balance'] as Map<String, dynamic>),
        totalCredited: ((json['summary'] as Map?)?['totalCredited'] as num? ?? 0).toDouble(),
        totalSpent: ((json['summary'] as Map?)?['totalSpent'] as num? ?? 0).toDouble(),
        totalRefunded: ((json['summary'] as Map?)?['totalRefunded'] as num? ?? 0).toDouble(),
        updatedAt: DateTime.parse(json['updatedAt'] as String),
      );
  @override
  List<Object> get props => [id, balance, totalCredited, totalSpent, totalRefunded, updatedAt];
}

class WalletTransaction extends Equatable {
  const WalletTransaction({
    required this.id,
    required this.type,
    required this.amount,
    required this.currency,
    required this.createdAt,
  });
  final String id;
  final String type;
  final double amount;
  final String currency;
  final DateTime createdAt;

  factory WalletTransaction.fromJson(Map<String, dynamic> json) =>
      WalletTransaction(
        id: json['id'] as String,
        type: json['type'] as String,
        amount: (json['amount'] as num).toDouble(),
        currency: json['currency'] as String,
        createdAt: DateTime.parse(json['createdAt'] as String),
      );
  @override
  List<Object> get props => [id, type, amount, currency, createdAt];
}

class WalletReservation extends Equatable {
  const WalletReservation({
    required this.id,
    required this.amount,
    required this.status,
    required this.expiresAt,
  });
  final String id;
  final double amount;
  final WalletReservationStatus status;
  final DateTime expiresAt;
  @override
  List<Object> get props => [id, amount, status, expiresAt];
}

class WalletTopUp extends Equatable {
  const WalletTopUp({
    required this.id,
    required this.amount,
    required this.status,
    this.paymentRedirectUrl,
    this.clientSecret,
    this.publishableKey,
    this.paymentIntentId,
  });
  final String id;
  final double amount;
  final WalletTopUpStatus status;
  final Uri? paymentRedirectUrl;
  final String? clientSecret;
  final String? publishableKey;
  final String? paymentIntentId;

  factory WalletTopUp.fromJson(Map<String, dynamic> json) => WalletTopUp(
        id: json['id'] as String,
        amount: (json['amount'] as num).toDouble(),
        status: WalletTopUpStatus.values.byName(json['status'] as String),
        paymentRedirectUrl: json['paymentRedirectUrl'] == null
            ? null
            : Uri.parse(json['paymentRedirectUrl'] as String),
        clientSecret: json['clientSecret'] as String?,
        publishableKey: json['publishableKey'] as String?,
        paymentIntentId: json['paymentIntentId'] as String?,
      );
  @override
  List<Object?> get props => [
        id,
        amount,
        status,
        paymentRedirectUrl,
        clientSecret,
        publishableKey,
        paymentIntentId,
      ];
}

class PaymentMethod extends Equatable {
  const PaymentMethod({required this.id, required this.type, required this.label});
  final String id;
  final String type;
  final String label;
  @override
  List<Object> get props => [id, type, label];
}
