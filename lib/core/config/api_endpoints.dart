abstract final class ApiEndpoints {
  // Relative paths preserve the /api/v1/customer/ prefix in Dio's baseUrl.
  static const register = 'auth/register';
  static const login = 'auth/login';
  static const refresh = 'auth/refresh';
  static const logout = 'auth/logout';
  static const verifyEmail = 'auth/verify-email';
  static const resendVerification = 'auth/resend-verification-email';
  static const forgotPassword = 'auth/forgot-password';
  static const resetPassword = 'auth/reset-password';
  static const profile = 'profile';
  static const stations = 'stations';
  static const wallet = 'wallet';
  static const walletTransactions = '$wallet/transactions';
  static const walletTopUps = '$wallet/topups';
  static const qrResolve = 'qr/resolve';
  static const fuelingSessions = 'fueling-sessions';
  static String authorizeFuelingSession(String sessionId) =>
      '$fuelingSessions/$sessionId/authorize';
  static const vehicles = 'vehicles';
  static const dashboard = 'dashboard';
  static const analytics = 'analytics';
  static const transactions = 'transactions';
}
