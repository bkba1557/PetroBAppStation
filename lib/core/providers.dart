import 'dart:async';
import 'dart:ui';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/config/app_config.dart';
import 'package:nnexoris_customer/core/network/api_client.dart';
import 'package:nnexoris_customer/core/network/auth_interceptor.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/core/network/network_info.dart';
import 'package:nnexoris_customer/core/network/request_metadata_interceptor.dart';
import 'package:nnexoris_customer/core/network/retry_interceptor.dart';
import 'package:nnexoris_customer/core/realtime/http_sse_client.dart';
import 'package:nnexoris_customer/core/realtime/realtime_client.dart';
import 'package:nnexoris_customer/core/security/quick_login_service.dart';
import 'package:nnexoris_customer/core/security/secure_storage_service.dart';
import 'package:nnexoris_customer/core/security/token_manager.dart';
import 'package:nnexoris_customer/core/storage/preferences_service.dart';
import 'package:nnexoris_customer/features/authentication/data/auth_repository_impl.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_tokens.dart';
import 'package:nnexoris_customer/features/authentication/domain/repositories/auth_repository.dart';
import 'package:nnexoris_customer/features/fueling/application/fueling_session_monitor.dart';
import 'package:nnexoris_customer/features/fueling/data/fueling_repository_impl.dart';
import 'package:nnexoris_customer/features/fueling/domain/repositories/fueling_repository.dart';
import 'package:nnexoris_customer/features/home/data/dashboard_repository.dart';
import 'package:nnexoris_customer/features/qr_scanner/data/qr_repository_impl.dart';
import 'package:nnexoris_customer/features/qr_scanner/domain/repositories/qr_repository.dart';
import 'package:nnexoris_customer/features/stations/data/device_location_service.dart';
import 'package:nnexoris_customer/features/stations/data/station_navigation_service.dart';
import 'package:nnexoris_customer/features/stations/data/station_repository_impl.dart';
import 'package:nnexoris_customer/features/stations/domain/repositories/station_repository.dart';
import 'package:nnexoris_customer/features/transactions/data/transaction_repository.dart';
import 'package:nnexoris_customer/features/vehicles/data/vehicle_repository_impl.dart';
import 'package:nnexoris_customer/features/vehicles/domain/repositories/vehicle_repository.dart';
import 'package:nnexoris_customer/features/wallet/data/wallet_repository_impl.dart';
import 'package:nnexoris_customer/features/wallet/domain/repositories/wallet_repository.dart';
import 'package:shared_preferences/shared_preferences.dart';

final secureStorageProvider = Provider<SecureStorageService>(
  (ref) => throw StateError('Secure storage must be overridden at bootstrap'),
);
final sharedPreferencesProvider = Provider<SharedPreferences>(
  (ref) =>
      throw StateError('SharedPreferences must be overridden at bootstrap'),
);
final appVersionProvider = Provider<String>(
  (ref) => throw StateError('App version must be overridden at bootstrap'),
);
final deviceIdProvider = Provider<String>(
  (ref) => throw StateError('Device ID must be overridden at bootstrap'),
);
final preferencesServiceProvider = Provider(
  (ref) => PreferencesService(ref.watch(sharedPreferencesProvider)),
);
final tokenManagerProvider = Provider(
  (ref) => TokenManager(ref.watch(secureStorageProvider)),
);
final quickLoginServiceProvider = Provider(
  (ref) => QuickLoginService(ref.watch(secureStorageProvider)),
);
final networkInfoProvider = Provider<NetworkInfo>(
  (ref) => ConnectivityNetworkInfo(Connectivity()),
);
final networkConnectionStateProvider = StreamProvider<NetworkConnectionState>(
  (ref) => ref.watch(networkInfoProvider).changes,
);

final dioProvider = Provider<Dio>((ref) {
  final config = ref.watch(appConfigProvider);
  final dio = Dio(
    BaseOptions(
      baseUrl: config.apiBaseUrl.toString(),
      connectTimeout: config.connectTimeout,
      receiveTimeout: config.receiveTimeout,
      contentType: Headers.jsonContentType,
    ),
  );
  final refreshDio = Dio(BaseOptions(baseUrl: config.apiBaseUrl.toString()));
  Future<AuthTokens?> refresh(String refreshToken) async {
    try {
      final response = await refreshDio.post<Map<String, dynamic>>(
        ApiEndpoints.refresh,
        data: {'refreshToken': refreshToken},
        options: Options(extra: {'skipAuth': true}),
      );
      return AuthTokens.fromJson(response.data!);
    } on DioException {
      return null;
    }
  }

  dio.interceptors.addAll([
    RequestMetadataInterceptor(
      localeTag: () => PlatformDispatcher.instance.locale.languageCode,
      appVersion: ref.watch(appVersionProvider),
      deviceId: ref.watch(deviceIdProvider),
    ),
    AuthInterceptor(
      tokenManager: ref.watch(tokenManagerProvider),
      dio: dio,
      refreshTokens: refresh,
    ),
    RetryInterceptor(dio),
  ]);
  return dio;
});

final httpClientProvider = Provider<HttpClient>(
  (ref) => ApiClient(ref.watch(dioProvider)),
);
final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepositoryImpl(
    ref.watch(httpClientProvider),
    ref.watch(tokenManagerProvider),
  ),
);
final stationRepositoryProvider = Provider<StationRepository>(
  (ref) => StationRepositoryImpl(ref.watch(httpClientProvider)),
);
final locationServiceProvider = Provider<LocationService>(
  (ref) => DeviceLocationService(),
);
final stationNavigationServiceProvider = Provider(
  (ref) => const StationNavigationService(),
);
final vehicleRepositoryProvider = Provider<VehicleRepository>(
  (ref) => VehicleRepositoryImpl(ref.watch(httpClientProvider)),
);
final walletRepositoryProvider = Provider<WalletRepository>(
  (ref) => WalletRepositoryImpl(ref.watch(httpClientProvider)),
);
final dashboardRepositoryProvider = Provider(
  (ref) => DashboardRepository(ref.watch(httpClientProvider)),
);
final transactionRepositoryProvider = Provider(
  (ref) => TransactionRepository(ref.watch(httpClientProvider)),
);
final qrRepositoryProvider = Provider<QrRepository>(
  (ref) => QrRepositoryImpl(ref.watch(httpClientProvider)),
);
final fuelingSessionRepositoryProvider = Provider<FuelingSessionRepository>(
  (ref) => FuelingRepositoryImpl(ref.watch(httpClientProvider)),
);
final realtimeClientProvider = Provider<RealtimeClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final client = NnexorisHttpSseClient(
    uri: config.webSocketBaseUrl,
    accessToken: ref.watch(tokenManagerProvider).accessToken,
  );
  unawaited(() async {
    try {
      await client.connect();
    } on Object {
      // Connection state and REST reconciliation handle initial unavailability.
    }
  }());
  ref.onDispose(() => unawaited(client.disconnect()));
  return client;
});
final realtimeConnectionStateProvider = StreamProvider<RealtimeConnectionState>(
  (ref) => ref.watch(realtimeClientProvider).connectionStates,
);
final fuelingSessionMonitorProvider = Provider<FuelingSessionMonitor>(
  (ref) => FuelingSessionMonitor(
    ref.watch(fuelingSessionRepositoryProvider),
    ref.watch(realtimeClientProvider),
  ),
);
