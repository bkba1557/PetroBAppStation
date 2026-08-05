import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/providers.dart';

final themeModeProvider = NotifierProvider<ThemeController, ThemeMode>(
  ThemeController.new,
);

class ThemeController extends Notifier<ThemeMode> {
  static const _key = 'theme_mode';

  @override
  ThemeMode build() {
    final value = ref.read(preferencesServiceProvider).getString(_key);
    return ThemeMode.values.where((item) => item.name == value).firstOrNull ??
        ThemeMode.light;
  }

  Future<void> setThemeMode(ThemeMode value) async {
    state = value;
    await ref.read(preferencesServiceProvider).setString(_key, value.name);
  }
}
