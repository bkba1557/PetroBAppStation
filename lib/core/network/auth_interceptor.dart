import 'dart:async';

import 'package:dio/dio.dart';
import 'package:nnexoris_customer/core/security/token_manager.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_tokens.dart';

typedef RefreshTokens = Future<AuthTokens?> Function(String refreshToken);

class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({
    required TokenManager tokenManager,
    required Dio dio,
    required RefreshTokens refreshTokens,
  }) : _tokenManager = tokenManager,
       _dio = dio,
       _refreshTokens = refreshTokens;

  final TokenManager _tokenManager;
  final Dio _dio;
  final RefreshTokens _refreshTokens;
  Future<AuthTokens?>? _refreshInFlight;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (options.extra['skipAuth'] != true) {
      final accessToken = await _tokenManager.accessToken();
      if (accessToken != null) {
        options.headers['Authorization'] = 'Bearer $accessToken';
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final request = err.requestOptions;
    if (err.response?.statusCode != 401 ||
        request.extra['skipAuth'] == true ||
        request.extra['authRetried'] == true) {
      handler.next(err);
      return;
    }

    final refreshToken = await _tokenManager.refreshToken();
    if (refreshToken == null) {
      await _tokenManager.clear();
      handler.next(err);
      return;
    }

    try {
      _refreshInFlight ??= _refreshTokens(
        refreshToken,
      ).whenComplete(() => _refreshInFlight = null);
      final tokens = await _refreshInFlight;
      if (tokens == null) throw err;
      await _tokenManager.save(tokens);
      request.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
      request.extra['authRetried'] = true;
      handler.resolve(await _dio.fetch<dynamic>(request));
    } on Object {
      await _tokenManager.clear();
      handler.next(err);
    }
  }
}
