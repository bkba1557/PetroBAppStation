import 'package:nnexoris_customer/core/security/secure_storage_service.dart';

class FakeSecureStorage implements SecureStorageService {
  final Map<String, String> values = {};
  @override
  Future<void> clear() async => values.clear();
  @override
  Future<void> delete(String key) async => values.remove(key);
  @override
  Future<String?> read(String key) async => values[key];
  @override
  Future<void> write(String key, String value) async => values[key] = value;
}
