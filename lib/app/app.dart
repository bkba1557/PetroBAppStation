import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/app/localization/locale_controller.dart';
import 'package:nnexoris_customer/app/router/app_router.dart';
import 'package:nnexoris_customer/app/theme/app_theme.dart';
import 'package:nnexoris_customer/app/theme/theme_controller.dart';
import 'package:nnexoris_customer/l10n/generated/app_localizations.dart';

class NnexorisApp extends ConsumerWidget {
  const NnexorisApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
        debugShowCheckedModeBanner: false,
        onGenerateTitle: (context) => AppLocalizations.of(context).appName,
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        themeMode: ref.watch(themeModeProvider),
        locale: ref.watch(localeProvider),
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        routerConfig: ref.watch(appRouterProvider),
      );
}
