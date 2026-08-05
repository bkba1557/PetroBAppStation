import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/providers.dart';

final localeProvider = NotifierProvider<LocaleController, Locale?>(
  LocaleController.new,
);

class LocaleController extends Notifier<Locale?> {
  static const _key = 'locale';

  @override
  Locale? build() {
    final code = ref.read(preferencesServiceProvider).getString(_key);
    return code == null ? const Locale('ar') : code == 'system' ? null : Locale(code);
  }

  Future<void> setLocale(Locale? locale) async {
    state = locale;
    await ref
        .read(preferencesServiceProvider)
        .setString(_key, locale?.languageCode ?? 'system');
  }
}
