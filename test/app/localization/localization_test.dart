import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/l10n/generated/app_localizations.dart';

void main() {
  test('loads English and Arabic resources', () async {
    final english = await AppLocalizations.delegate.load(const Locale('en'));
    final arabic = await AppLocalizations.delegate.load(const Locale('ar'));
    expect(english.login, 'Sign in');
    expect(arabic.login, 'تسجيل الدخول');
    expect(AppLocalizations.supportedLocales, contains(const Locale('ar')));
  });

  testWidgets('Arabic resolves RTL and English resolves LTR', (tester) async {
    Future<TextDirection> directionFor(Locale locale) async {
      late TextDirection direction;
      await tester.pumpWidget(
        WidgetsApp(
          color: const Color(0xFFFFFFFF),
          locale: locale,
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
          ],
          builder: (context, child) {
            direction = Directionality.of(context);
            return const SizedBox();
          },
        ),
      );
      return direction;
    }

    expect(await directionFor(const Locale('ar')), TextDirection.rtl);
    expect(await directionFor(const Locale('en')), TextDirection.ltr);
  });
}
