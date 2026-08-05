import 'package:equatable/equatable.dart';

class Failure extends Equatable {
  const Failure({
    required this.code,
    required this.messageKey,
    this.correlationId,
    this.isRetryable = false,
  });

  final String code;
  final String messageKey;
  final String? correlationId;
  final bool isRetryable;

  @override
  List<Object?> get props => [code, messageKey, correlationId, isRetryable];
}
