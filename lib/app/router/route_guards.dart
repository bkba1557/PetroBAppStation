import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_state.dart';

abstract final class RouteGuards {
  static const _public = {
    AppRoutes.splash,
    AppRoutes.onboarding,
    AppRoutes.login,
    AppRoutes.quickLogin,
    AppRoutes.register,
  };

  static bool _requiresVerifiedEmail(String location) =>
      location == AppRoutes.scan || location.startsWith('/fueling');

  static String? redirect(
    AuthState auth,
    String location, {
    bool requireVerifiedEmailForFueling = true,
  }) {
    if (auth.status == AuthStatus.initial ||
        auth.status == AuthStatus.loading) {
      return location == AppRoutes.splash ? null : AppRoutes.splash;
    }
    if (auth.status == AuthStatus.quickLoginRequired) {
      return location == AppRoutes.quickLogin ? null : AppRoutes.quickLogin;
    }
    if (!auth.isAuthenticated) {
      if (location == AppRoutes.splash) {
        return AppRoutes.login;
      }
      return _public.contains(location) ? null : AppRoutes.login;
    }
    if (requireVerifiedEmailForFueling &&
        _requiresVerifiedEmail(location) &&
        auth.customer?.emailVerified != true) {
      return AppRoutes.verifyEmail;
    }
    if (location == AppRoutes.verifyEmail &&
        auth.customer?.emailVerified != true) {
      return null;
    }
    if (_public.contains(location) || location == AppRoutes.verifyEmail) {
      return AppRoutes.home;
    }
    return null;
  }
}
