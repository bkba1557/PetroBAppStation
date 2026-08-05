import 'package:nnexoris_customer/features/authentication/domain/models/auth_requests.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_session.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_tokens.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/customer.dart';

abstract interface class AuthRepository {
  Future<AuthSession> register(RegisterRequest request);
  Future<AuthSession> login(LoginRequest request);
  Future<void> logout();
  Future<AuthTokens> refreshToken(String refreshToken);
  Future<Customer> verifyEmail(String verificationCode);
  Future<void> resendVerificationEmail();
  Future<void> forgotPassword(String email);
  Future<void> resetPassword(ResetPasswordRequest request);
  Future<Customer> getCurrentUser();
}
