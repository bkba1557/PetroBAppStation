import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/config/app_config.dart';
import 'package:nnexoris_customer/core/config/environment.dart';

void main() {
  test('production accepts only HTTPS and WSS', () {
    final config = AppConfig(
      apiBaseUrl: Uri.parse('https://customer-api.nnexoris.com/api/v1/customer/'),
      webSocketBaseUrl: Uri.parse('wss://customer-api.nnexoris.com/api/v1/customer/realtime'),
      environment: AppEnvironment.production,
      enableLogging: false,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    );
    expect(config.validate, returnsNormally);
  });

  test('production rejects insecure transport', () {
    final config = AppConfig(
      apiBaseUrl: Uri.parse('http://customer-api.nnexoris.com/api/v1/customer/'),
      webSocketBaseUrl: Uri.parse('ws://customer-api.nnexoris.com/api/v1/customer/realtime'),
      environment: AppEnvironment.production,
      enableLogging: false,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    );
    expect(config.validate, throwsStateError);
  });

  test('API base URL requires trailing slash so relative routes retain prefix', () {
    final config = AppConfig(
      apiBaseUrl: Uri.parse('https://customer-api.nnexoris.com/api/v1/customer'),
      webSocketBaseUrl: Uri.parse('wss://customer-api.nnexoris.com/api/v1/customer/realtime'),
      environment: AppEnvironment.production,
      enableLogging: false,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    );
    expect(config.validate, throwsFormatException);
  });
}
