import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/security/token_manager.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_tokens.dart';

import '../../helpers/fakes.dart';

void main() {
  test('round-trips tokens and clears them', () async {
    final storage = FakeSecureStorage();
    final manager = TokenManager(storage);
    final tokens = AuthTokens(
      accessToken: 'access-value',
      refreshToken: 'refresh-value',
      accessTokenExpiresAt: DateTime.utc(2030),
    );
    await manager.save(tokens);
    expect(await manager.readTokens(), tokens);
    await manager.clear();
    expect(await manager.readTokens(), isNull);
  });
}
