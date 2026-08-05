import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/app/router/route_guards.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/customer.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_state.dart';

void main() {
  const unverified = Customer(
    id: '1',
    email: 'a@example.com',
    displayName: 'A',
    emailVerified: false,
  );
  test('unauthenticated user cannot enter protected routes', () {
    expect(
      RouteGuards.redirect(
        const AuthState(status: AuthStatus.unauthenticated),
        AppRoutes.wallet,
      ),
      AppRoutes.login,
    );
  });
  test('unauthenticated user leaves splash for login', () {
    expect(
      RouteGuards.redirect(
        const AuthState(status: AuthStatus.unauthenticated),
        AppRoutes.splash,
      ),
      AppRoutes.login,
    );
  });
  test('quick-login lock redirects every protected route to PIN unlock', () {
    const locked = AuthState(status: AuthStatus.quickLoginRequired);
    expect(RouteGuards.redirect(locked, AppRoutes.home), AppRoutes.quickLogin);
    expect(RouteGuards.redirect(locked, AppRoutes.quickLogin), isNull);
  });
  test('unverified user cannot start fueling', () {
    expect(
      RouteGuards.redirect(
        const AuthState(
          status: AuthStatus.emailVerificationRequired,
          customer: unverified,
        ),
        AppRoutes.fuelingSetup,
      ),
      AppRoutes.verifyEmail,
    );
    expect(
      RouteGuards.redirect(
        const AuthState(
          status: AuthStatus.emailVerificationRequired,
          customer: unverified,
        ),
        AppRoutes.verifyEmail,
      ),
      isNull,
    );
  });
}
