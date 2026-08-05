abstract final class AppRoutes {
  static const splash = '/splash';
  static const onboarding = '/onboarding';
  static const login = '/login';
  static const quickLogin = '/quick-login';
  static const register = '/register';
  static const verifyEmail = '/verify-email';
  static const home = '/home';
  static const stations = '/stations';
  static const wallet = '/wallet';
  static const walletTopUp = '/wallet/top-up';
  static const walletTransactions = '/wallet/transactions';
  static const scan = '/scan';
  static const fuelingSetup = '/fueling/setup';
  static const vehicles = '/vehicles';
  static const profile = '/profile';
  static const settings = '/settings';
  static const transactions = '/transactions';

  static String station(String id) => '/stations/$id';
  static String fueling(String id) => '/fueling/$id';
  static String transaction(String id) => '/transactions/$id';
}
