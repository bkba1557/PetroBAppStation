import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/features/authentication/presentation/pages/auth_flow_pages.dart';
import 'package:nnexoris_customer/l10n/generated/app_localizations.dart';

void main() {
  testWidgets('shows the animated PETRO B brand splash', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        locale: Locale('ar'),
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: SplashPage(),
      ),
    );

    expect(find.text('PETRO B'), findsOneWidget);
    expect(find.text('طاقة أذكى · تجربة أسرع'), findsOneWidget);
    expect(find.byType(Image), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 600));
    expect(tester.takeException(), isNull);
  });
}
