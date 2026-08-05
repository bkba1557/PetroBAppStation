import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/config/environment.dart';

final appConfigProvider = Provider<AppConfig>(
  (ref) => throw StateError('AppConfig must be overridden during bootstrap'),
);

class AppConfig {
  const AppConfig({
    required this.apiBaseUrl,
    required this.webSocketBaseUrl,
    required this.environment,
    required this.enableLogging,
    required this.connectTimeout,
    required this.receiveTimeout,
    this.requireVerifiedEmailForFueling = false,
    this.inAppMapsEnabled = true,
  });

  factory AppConfig.fromEnvironment() {
    const environmentValue = String.fromEnvironment(
      'APP_ENV',
      defaultValue: 'production',
    );
    const apiOverride = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: '',
    );
    const socketOverride = String.fromEnvironment(
      'WS_BASE_URL',
      defaultValue: '',
    );
    const logging = bool.fromEnvironment('ENABLE_LOGGING', defaultValue: false);
    const connectSeconds = int.fromEnvironment(
      'CONNECT_TIMEOUT_SECONDS',
      defaultValue: 15,
    );
    const receiveSeconds = int.fromEnvironment(
      'RECEIVE_TIMEOUT_SECONDS',
      defaultValue: 20,
    );
    const requireVerifiedEmail = bool.fromEnvironment(
      'REQUIRE_VERIFIED_EMAIL_FOR_FUELING',
      defaultValue: false,
    );
    const inAppMapsEnabled = bool.fromEnvironment(
      'GOOGLE_MAPS_IOS_ENABLED',
      defaultValue: true,
    );

    final environment = AppEnvironment.parse(environmentValue);
    final defaults = switch (environment) {
      AppEnvironment.development => (
        'http://localhost:8080/api/v1/customer/',
        'ws://localhost:8080/api/v1/customer/realtime',
      ),
      AppEnvironment.production => (
        'https://customer-api.nnexoris.com/api/v1/customer/',
        'wss://customer-api.nnexoris.com/api/v1/customer/realtime',
      ),
      AppEnvironment.staging => ('', ''),
    };
    final apiUrl = apiOverride.isEmpty ? defaults.$1 : apiOverride;
    final socketUrl = socketOverride.isEmpty ? defaults.$2 : socketOverride;

    return AppConfig(
      apiBaseUrl: Uri.parse(apiUrl),
      webSocketBaseUrl: Uri.parse(socketUrl),
      environment: environment,
      enableLogging: logging,
      connectTimeout: Duration(seconds: connectSeconds),
      receiveTimeout: Duration(seconds: receiveSeconds),
      requireVerifiedEmailForFueling: requireVerifiedEmail,
      inAppMapsEnabled: inAppMapsEnabled,
    )..validate();
  }

  final Uri apiBaseUrl;
  final Uri webSocketBaseUrl;
  final AppEnvironment environment;
  final bool enableLogging;
  final Duration connectTimeout;
  final Duration receiveTimeout;
  final bool requireVerifiedEmailForFueling;
  final bool inAppMapsEnabled;

  bool get isProduction => environment == AppEnvironment.production;

  void validate() {
    if (!apiBaseUrl.hasScheme || !webSocketBaseUrl.hasScheme) {
      throw const FormatException('API and WebSocket URLs require a scheme');
    }
    if (!apiBaseUrl.path.endsWith('/')) {
      throw const FormatException('API_BASE_URL must end with /');
    }
    if (environment != AppEnvironment.development &&
        (apiBaseUrl.scheme != 'https' || webSocketBaseUrl.scheme != 'wss')) {
      throw StateError('Staging and production require HTTPS and WSS');
    }
    if (environment == AppEnvironment.production &&
        (apiBaseUrl.host != 'customer-api.nnexoris.com' ||
            webSocketBaseUrl.host != 'customer-api.nnexoris.com')) {
      throw StateError('Production must use the NNEXORIS Customer API');
    }
    if (connectTimeout <= Duration.zero || receiveTimeout <= Duration.zero) {
      throw StateError('Network timeouts must be positive');
    }
  }
}
