class AppException implements Exception {
  const AppException({
    required this.code,
    required this.safeMessage,
    this.statusCode,
    this.correlationId,
    this.cause,
  });

  final String code;
  final String safeMessage;
  final int? statusCode;
  final String? correlationId;
  final Object? cause;

  @override
  String toString() => 'AppException($code, status: $statusCode)';
}

class NetworkException extends AppException {
  const NetworkException({
    required super.code,
    required super.safeMessage,
    super.statusCode,
    super.correlationId,
    super.cause,
  });
}

class AuthenticationException extends AppException {
  const AuthenticationException({
    required super.code,
    required super.safeMessage,
    super.statusCode,
    super.correlationId,
    super.cause,
  });
}
