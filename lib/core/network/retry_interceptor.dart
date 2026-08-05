import 'dart:async';
import 'dart:math';

import 'package:dio/dio.dart';

class RetryInterceptor extends Interceptor {
  RetryInterceptor(this._dio, {this.maxRetries = 2});

  final Dio _dio;
  final int maxRetries;

  static const _safeMethods = {'GET', 'HEAD', 'OPTIONS'};
  static const _sensitiveFragments = {
    '/wallet/topups',
    '/wallet/reservations',
    '/fueling-sessions',
    '/authorize',
    '/payment',
  };

  bool canRetry(RequestOptions request) {
    if (_safeMethods.contains(request.method.toUpperCase())) return true;
    final hasKey =
        request.headers['Idempotency-Key']?.toString().isNotEmpty ?? false;
    if (!hasKey) return false;
    return _sensitiveFragments.any(request.path.contains) ||
        request.extra['idempotent'] == true;
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final options = err.requestOptions;
    final attempt = options.extra['retryAttempt'] as int? ?? 0;
    final retryableStatus =
        err.response?.statusCode == 408 ||
        err.response?.statusCode == 429 ||
        (err.response?.statusCode ?? 0) >= 500;
    final retryableTransport =
        err.type == DioExceptionType.connectionError ||
        err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout;

    if (attempt >= maxRetries ||
        !canRetry(options) ||
        (!retryableStatus && !retryableTransport)) {
      handler.next(err);
      return;
    }

    options.extra['retryAttempt'] = attempt + 1;
    final jitter = Random().nextInt(150);
    await Future<void>.delayed(
      Duration(milliseconds: 300 * (1 << attempt) + jitter),
    );
    try {
      handler.resolve(await _dio.fetch<dynamic>(options));
    } on DioException catch (nextError) {
      handler.next(nextError);
    }
  }
}
