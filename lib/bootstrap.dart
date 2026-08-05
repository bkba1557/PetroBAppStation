import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/app/app.dart';
import 'package:nnexoris_customer/core/config/app_config.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/core/security/device_identity_service.dart';
import 'package:nnexoris_customer/core/security/secure_storage_service.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<void> bootstrap() async {
  WidgetsFlutterBinding.ensureInitialized();
  final config = AppConfig.fromEnvironment();
  final secureStorage = PlatformSecureStorage();
  final deviceId = await DeviceIdentityService(secureStorage).getOrCreate();
  final packageInfo = await PackageInfo.fromPlatform();
  final preferences = await SharedPreferences.getInstance();

  await runZonedGuarded(
    () async => runApp(
      ProviderScope(
        overrides: [
          appConfigProvider.overrideWithValue(config),
          secureStorageProvider.overrideWithValue(secureStorage),
          sharedPreferencesProvider.overrideWithValue(preferences),
          appVersionProvider.overrideWithValue(packageInfo.version),
          deviceIdProvider.overrideWithValue(deviceId),
        ],
        child: const NnexorisApp(),
      ),
    ),
    (error, stackTrace) {
      // Production reporting is injected later and must redact sensitive data.
      FlutterError.reportError(
        FlutterErrorDetails(exception: error, stack: stackTrace),
      );
    },
  );
}
