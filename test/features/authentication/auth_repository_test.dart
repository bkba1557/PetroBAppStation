import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/api_response.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/core/security/token_manager.dart';
import 'package:nnexoris_customer/features/authentication/data/auth_repository_impl.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_requests.dart';

import '../../helpers/fakes.dart';

class MockHttpClient extends Mock implements HttpClient {}

void main() {
  test('login stores the cloud-issued session tokens', () async {
    final client = MockHttpClient();
    final tokenManager = TokenManager(FakeSecureStorage());
    when(
      () => client.post<Map<String, dynamic>>(
        ApiEndpoints.login,
        data: any(named: 'data'),
      ),
    ).thenAnswer(
      (_) async => ApiResponse(data: {
        'customer': {
          'id': 'customer-1',
          'email': 'customer@example.com',
          'displayName': 'Customer',
          'emailVerified': true,
        },
        'tokens': {
          'accessToken': 'access',
          'refreshToken': 'refresh',
          'accessTokenExpiresAt': '2030-01-01T00:00:00Z',
        },
      }),
    );
    final session = await AuthRepositoryImpl(client, tokenManager).login(
      const LoginRequest(email: 'customer@example.com', password: 'password1'),
    );
    expect(session.customer.id, 'customer-1');
    expect((await tokenManager.readTokens())?.accessToken, 'access');
  });
}
