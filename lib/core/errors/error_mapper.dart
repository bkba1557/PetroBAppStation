import 'package:dio/dio.dart';
import 'package:nnexoris_customer/core/errors/app_exception.dart';
import 'package:nnexoris_customer/core/errors/failure.dart';
import 'package:nnexoris_customer/core/network/error_payload_dto.dart';

abstract final class ErrorMapper {
  static AppException toException(Object error) {
    if (error is AppException) return error;
    final failure = toFailure(error);
    if (failure.code == 'UNAUTHORIZED' || failure.code == 'SESSION_EXPIRED') {
      return AuthenticationException(
        code: failure.code,
        safeMessage: failure.messageKey,
        correlationId: failure.correlationId,
        cause: error,
      );
    }
    return NetworkException(
      code: failure.code,
      safeMessage: failure.messageKey,
      correlationId: failure.correlationId,
      cause: error,
    );
  }

  static Failure toFailure(Object error) {
    if (error is AppException) {
      return Failure(
        code: error.code,
        messageKey: _messageKey(error.code),
        correlationId: error.correlationId,
        isRetryable: error is NetworkException && error.statusCode == null,
      );
    }
    if (error is DioException) {
      final correlationId = error.response?.headers.value('x-correlation-id');
      final code = _serverCode(error.response?.data) ??
          _httpCode(error.response?.statusCode) ??
          _dioCode(error.type);
      return Failure(
        code: code,
        messageKey: _messageKey(code),
        correlationId: correlationId,
        isRetryable: const {
          DioExceptionType.connectionError,
          DioExceptionType.connectionTimeout,
          DioExceptionType.receiveTimeout,
        }.contains(error.type),
      );
    }
    return const Failure(code: 'UNKNOWN', messageKey: 'errorUnexpected');
  }

  static String? _serverCode(Object? data) {
    if (data is Map<String, dynamic>) {
      final payload = ErrorPayloadDto.fromJson(data);
      return payload.code ?? payload.error;
    }
    return null;
  }

  static String _dioCode(DioExceptionType type) => switch (type) {
        DioExceptionType.connectionTimeout => 'CONNECTION_TIMEOUT',
        DioExceptionType.sendTimeout => 'SEND_TIMEOUT',
        DioExceptionType.receiveTimeout => 'RECEIVE_TIMEOUT',
        DioExceptionType.connectionError => 'OFFLINE',
        DioExceptionType.cancel => 'REQUEST_CANCELLED',
        _ => 'NETWORK_ERROR',
      };

  static String? _httpCode(int? statusCode) => switch (statusCode) {
        401 => 'UNAUTHORIZED',
        403 => 'FORBIDDEN',
        404 => 'NOT_FOUND',
        409 => 'CONFLICT',
        429 => 'RATE_LIMITED',
        _ => null,
      };

  static String _messageKey(String code) => switch (code) {
        'INVALID_CREDENTIALS' => 'errorInvalidCredentials',
        'EMAIL_VERIFICATION_REQUIRED' => 'errorEmailVerificationRequired',
        'INSUFFICIENT_FUNDS' => 'errorInsufficientFunds',
        'OFFLINE' || 'CONNECTION_TIMEOUT' || 'RECEIVE_TIMEOUT' => 'errorOffline',
        'SESSION_EXPIRED' || 'UNAUTHORIZED' => 'errorSessionExpired',
        _ => 'errorUnexpected',
      };
}
