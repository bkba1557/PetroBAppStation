import 'package:nnexoris_customer/core/security/secure_storage_service.dart';
import 'package:uuid/uuid.dart';

class DeviceIdentityService {
  DeviceIdentityService(this._storage, {Uuid? uuid}) : _uuid = uuid ?? const Uuid();

  static const _key = 'customer_device_id_v1';
  final SecureStorageService _storage;
  final Uuid _uuid;

  Future<String> getOrCreate() async {
    final existing = await _storage.read(_key);
    if (existing != null && existing.isNotEmpty) return existing;
    final value = _uuid.v4();
    await _storage.write(_key, value);
    return value;
  }
}
