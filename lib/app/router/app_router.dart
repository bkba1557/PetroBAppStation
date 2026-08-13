import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/app/router/route_guards.dart';
import 'package:nnexoris_customer/core/config/app_config.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_controller.dart';
import 'package:nnexoris_customer/features/authentication/presentation/pages/auth_flow_pages.dart';
import 'package:nnexoris_customer/features/authentication/presentation/pages/login_page.dart';
import 'package:nnexoris_customer/features/authentication/presentation/pages/quick_login_page.dart';
import 'package:nnexoris_customer/features/authentication/presentation/pages/register_page.dart';
import 'package:nnexoris_customer/features/fueling/presentation/fueling_pages.dart';
import 'package:nnexoris_customer/features/home/presentation/home_page.dart';
import 'package:nnexoris_customer/features/profile/presentation/profile_page.dart';
import 'package:nnexoris_customer/features/qr_scanner/domain/models/qr_resolution.dart';
import 'package:nnexoris_customer/features/qr_scanner/presentation/qr_scanner_page.dart';
import 'package:nnexoris_customer/features/settings/presentation/settings_page.dart';
import 'package:nnexoris_customer/features/stations/presentation/stations_page.dart';
import 'package:nnexoris_customer/features/transactions/presentation/transactions_page.dart';
import 'package:nnexoris_customer/features/vehicles/presentation/vehicles_page_clean.dart';
import 'package:nnexoris_customer/features/wallet/presentation/wallet_pages.dart';
import 'package:nnexoris_customer/shared/widgets/mobile_navigation_shell.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authStateProvider);
  final config = ref.watch(appConfigProvider);
  final router = GoRouter(
    initialLocation: AppRoutes.splash,
    redirect: (_, state) => RouteGuards.redirect(
      auth,
      state.matchedLocation,
      requireVerifiedEmailForFueling: config.requireVerifiedEmailForFueling,
    ),
    routes: [
      GoRoute(path: AppRoutes.splash, builder: (_, _) => const SplashPage()),
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (_, _) => const OnboardingPage(),
      ),
      GoRoute(path: AppRoutes.login, builder: (_, _) => const LoginPage()),
      GoRoute(
        path: AppRoutes.quickLogin,
        builder: (_, _) => const QuickLoginPage(),
      ),
      GoRoute(
        path: AppRoutes.register,
        builder: (_, _) => const RegisterPage(),
      ),
      GoRoute(
        path: AppRoutes.verifyEmail,
        builder: (_, _) => const VerifyEmailPage(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (_, _, shell) => MobileNavigationShell(navigationShell: shell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.home,
                builder: (_, _) => const HomePage(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.stations,
                builder: (_, _) => const StationsPage(),
                routes: [
                  GoRoute(
                    path: ':stationId',
                    builder: (_, state) => StationDetailsPage(
                      stationId: state.pathParameters['stationId']!,
                    ),
                  ),
                ],
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.wallet,
                builder: (_, _) => const WalletPage(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.profile,
                builder: (_, _) => const ProfilePage(),
              ),
            ],
          ),
        ],
      ),
      GoRoute(
        path: AppRoutes.walletTopUp,
        builder: (_, _) => const WalletTopUpPage(),
      ),
      GoRoute(
        path: AppRoutes.walletTransactions,
        builder: (_, _) => const WalletTransactionsPage(),
      ),
      GoRoute(path: AppRoutes.scan, builder: (_, _) => const QrScannerPage()),
      GoRoute(
        path: AppRoutes.fuelingSetup,
        builder: (_, state) =>
            FuelingSetupPage(resolution: state.extra as QrResolution?),
      ),
      GoRoute(
        path: '/fueling/:sessionId',
        builder: (_, state) =>
            FuelingProgressPage(sessionId: state.pathParameters['sessionId']!),
      ),
      GoRoute(
        path: AppRoutes.vehicles,
        builder: (_, _) => const VehiclesPage(),
      ),
      GoRoute(
        path: AppRoutes.settings,
        builder: (_, _) => const SettingsPage(),
      ),
      GoRoute(
        path: AppRoutes.transactions,
        builder: (_, _) => const TransactionsPage(),
        routes: [
          GoRoute(
            path: ':transactionId',
            builder: (_, state) => TransactionDetailsPage(
              id: state.pathParameters['transactionId']!,
            ),
          ),
        ],
      ),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});
