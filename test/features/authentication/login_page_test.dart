import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_controller.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_state.dart';
import 'package:nnexoris_customer/features/authentication/presentation/pages/login_page.dart';
import 'package:nnexoris_customer/l10n/generated/app_localizations.dart';

class TestAuthController extends AuthController {
  @override
  AuthState build() => const AuthState(status: AuthStatus.unauthenticated);
}

void main() {
  testWidgets('login page renders localized form fields', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [authStateProvider.overrideWith(TestAuthController.new)],
        child: const MaterialApp(
          locale: Locale('en'),
          localizationsDelegates: [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: LoginPage(),
        ),
      ),
    );
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
