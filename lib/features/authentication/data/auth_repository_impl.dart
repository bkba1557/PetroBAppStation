import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/core/security/token_manager.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_requests.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_session.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_tokens.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/customer.dart';
import 'package:nnexoris_customer/features/authentication/domain/repositories/auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl(this._client, this._tokens);

  final HttpClient _client;
  final TokenManager _tokens;

  @override
  Future<AuthSession> login(LoginRequest request) async {
    final response = await _client.post<Map<String, dynamic>>(
      ApiEndpoints.login,
      data: request.toJson(),
    );
    final session = AuthSession.fromJson(response.data);
    await _tokens.save(session.tokens);
    return session;
  }

  @override
  Future<AuthSession> register(RegisterRequest request) async {
    final response = await _client.post<Map<String, dynamic>>(
      ApiEndpoints.register,
      data: request.toJson(),
    );
    final session = AuthSession.fromJson(response.data);
    await _tokens.save(session.tokens);
    return session;
  }

  @override
  Future<void> logout() async {
    try {
      await _client.post<void>(ApiEndpoints.logout);
    } finally {
      await _tokens.clear();
    }
  }

  @override
  Future<AuthTokens> refreshToken(String refreshToken) async {
    final response = await _client.post<Map<String, dynamic>>(
      ApiEndpoints.refresh,
      data: {'refreshToken': refreshToken},
    );
    final tokens = AuthTokens.fromJson(response.data);
    await _tokens.save(tokens);
    return tokens;
  }

  @override
  Future<Customer> getCurrentUser() async {
    final response = await _client.get<Map<String, dynamic>>(
      ApiEndpoints.profile,
    );
    return Customer.fromJson(response.data);
  }

  @override
  Future<Customer> verifyEmail(String verificationCode) async {
    final response = await _client.post<Map<String, dynamic>>(
      ApiEndpoints.verifyEmail,
      data: {'code': verificationCode},
    );
    return Customer.fromJson(response.data);
  }

  @override
  Future<void> resendVerificationEmail() =>
      _client.post<void>(ApiEndpoints.resendVerification).then((_) {});

  @override
  Future<void> forgotPassword(String email) => _client
      .post<void>(ApiEndpoints.forgotPassword, data: {'email': email})
      .then((_) {});

  @override
  Future<void> resetPassword(ResetPasswordRequest request) => _client
      .post<void>(ApiEndpoints.resetPassword, data: request.toJson())
      .then((_) {});
}
