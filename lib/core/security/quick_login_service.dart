import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:nnexoris_customer/core/security/secure_storage_service.dart';

enum QuickLoginResult { success, invalidPin, temporarilyLocked, notConfigured }

class QuickLoginService {
  QuickLoginService(this._storage, {DateTime Function()? clock})
    : _clock = clock ?? DateTime.now;

  static const _key = 'customer_quick_login_v1';
  static const _iterations = 120000;
  static const _maxAttempts = 5;
  final SecureStorageService _storage;
  final DateTime Function() _clock;

  Future<Map<String, dynamic>?> _config() async {
    final raw = await _storage.read(_key);
    if (raw == null) return null;
    try {
      return Map<String, dynamic>.from(jsonDecode(raw) as Map);
    } on Object {
      await _storage.delete(_key);
      return null;
    }
  }

  Future<bool> isEnabled() async => await _config() != null;
  Future<int?> pinLength() async => (await _config())?['length'] as int?;
  Future<String?> displayName() async =>
      (await _config())?['displayName'] as String?;

  Future<void> enable(String pin, {String? displayName}) async {
    if (!RegExp(r'^(?:\d{4}|\d{6})$').hasMatch(pin)) {
      throw ArgumentError('PIN must contain exactly 4 or 6 digits');
    }
    final salt = List<int>.generate(16, (_) => Random.secure().nextInt(256));
    await _storage.write(
      _key,
      jsonEncode({
        'version': 1,
        'length': pin.length,
        'salt': base64UrlEncode(salt),
        'digest': base64UrlEncode(_derive(pin, salt)),
        if (displayName?.trim().isNotEmpty ?? false)
          'displayName': displayName!.trim(),
        'failedAttempts': 0,
        'lockedUntil': null,
      }),
    );
  }

  Future<void> updateDisplayName(String displayName) async {
    final config = await _config();
    if (config == null || displayName.trim().isEmpty) return;
    config['displayName'] = displayName.trim();
    await _storage.write(_key, jsonEncode(config));
  }

  Future<void> disable() => _storage.delete(_key);

  Future<QuickLoginResult> verify(String pin) async {
    final config = await _config();
    if (config == null) return QuickLoginResult.notConfigured;
    final now = _clock().toUtc();
    final lockedUntilRaw = config['lockedUntil'] as String?;
    if (lockedUntilRaw != null &&
        now.isBefore(DateTime.parse(lockedUntilRaw).toUtc())) {
      return QuickLoginResult.temporarilyLocked;
    }
    final expected = base64Url.decode(config['digest'] as String);
    final actual = _derive(pin, base64Url.decode(config['salt'] as String));
    if (_constantTimeEquals(expected, actual)) {
      config['failedAttempts'] = 0;
      config['lockedUntil'] = null;
      await _storage.write(_key, jsonEncode(config));
      return QuickLoginResult.success;
    }
    final attempts = (config['failedAttempts'] as int? ?? 0) + 1;
    config['failedAttempts'] = attempts;
    if (attempts >= _maxAttempts) {
      config['failedAttempts'] = 0;
      config['lockedUntil'] = now
          .add(const Duration(minutes: 1))
          .toIso8601String();
    }
    await _storage.write(_key, jsonEncode(config));
    return attempts >= _maxAttempts
        ? QuickLoginResult.temporarilyLocked
        : QuickLoginResult.invalidPin;
  }

  List<int> _derive(String pin, List<int> salt) {
    final hmac = Hmac(sha256, utf8.encode(pin));
    var value = hmac.convert(<int>[...salt, 0, 0, 0, 1]).bytes;
    final result = List<int>.from(value);
    for (var i = 1; i < _iterations; i++) {
      value = hmac.convert(value).bytes;
      for (var j = 0; j < result.length; j++) {
        result[j] ^= value[j];
      }
    }
    return result;
  }

  bool _constantTimeEquals(List<int> left, List<int> right) {
    if (left.length != right.length) return false;
    var difference = 0;
    for (var i = 0; i < left.length; i++) {
      difference |= left[i] ^ right[i];
    }
    return difference == 0;
  }
}
