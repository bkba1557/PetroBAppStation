import 'dart:convert';

import 'package:nnexoris_customer/core/security/secure_storage_service.dart';
import 'package:nnexoris_customer/features/authentication/domain/models/auth_tokens.dart';

class TokenManager {
  TokenManager(this._storage);

  static const _tokensKey = 'customer_auth_tokens_v1';
  final SecureStorageService _storage;

  Future<AuthTokens?> readTokens() async {
    final encoded = await _storage.read(_tokensKey);
    if (encoded == null) return null;
    try {
      return AuthTokens.fromJson(
        Map<String, dynamic>.from(jsonDecode(encoded) as Map),
      );
    } on Object {
      await clear();
      return null;
    }
  }

  Future<void> save(AuthTokens tokens) =>
      _storage.write(_tokensKey, jsonEncode(tokens.toJson()));

  Future<String?> accessToken() async => (await readTokens())?.accessToken;
  Future<String?> refreshToken() async => (await readTokens())?.refreshToken;
  Future<void> clear() => _storage.delete(_tokensKey);
}
