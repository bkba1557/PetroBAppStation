import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/app/localization/locale_controller.dart';
import 'package:nnexoris_customer/app/theme/theme_controller.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(themeModeProvider);
    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.settings)),
      body: ListView(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: SegmentedButton<ThemeMode>(
              segments: [
                ButtonSegment(value: ThemeMode.system, label: Text(context.l10n.systemTheme)),
                ButtonSegment(value: ThemeMode.light, label: Text(context.l10n.lightTheme)),
                ButtonSegment(value: ThemeMode.dark, label: Text(context.l10n.darkTheme)),
              ],
              selected: {mode},
              onSelectionChanged: (value) =>
                  ref.read(themeModeProvider.notifier).setThemeMode(value.first),
            ),
          ),
          const Divider(),
          ListTile(title: Text(context.l10n.language)),
          ListTile(
            title: Text(context.l10n.arabic),
            onTap: () => ref.read(localeProvider.notifier).setLocale(const Locale('ar')),
          ),
          ListTile(
            title: Text(context.l10n.english),
            onTap: () => ref.read(localeProvider.notifier).setLocale(const Locale('en')),
          ),
        ],
      ),
    );
  }
}
