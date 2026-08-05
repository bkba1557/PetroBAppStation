import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/security/quick_login_service.dart';

import '../../helpers/fakes.dart';

void main() {
  test('supports only 4 or 6 digit PIN and never stores plaintext', () async {
    final storage = FakeSecureStorage();
    final service = QuickLoginService(storage);
    await service.enable('1234', displayName: 'Mohamed Arafat');
    expect(await service.pinLength(), 4);
    expect(await service.displayName(), 'Mohamed Arafat');
    expect(storage.values.values.single, isNot(contains('1234')));
    expect(await service.verify('1234'), QuickLoginResult.success);
    await service.enable('123456');
    expect(await service.pinLength(), 6);
    expect(service.enable('12345'), throwsArgumentError);
  });

  test('locks for one minute after five failed attempts', () async {
    final storage = FakeSecureStorage();
    var now = DateTime.utc(2026, 8, 4);
    final service = QuickLoginService(storage, clock: () => now);
    await service.enable('1234');
    for (var i = 0; i < 4; i++) {
      expect(await service.verify('9999'), QuickLoginResult.invalidPin);
    }
    expect(await service.verify('9999'), QuickLoginResult.temporarilyLocked);
    expect(await service.verify('1234'), QuickLoginResult.temporarilyLocked);
    now = now.add(const Duration(minutes: 1, seconds: 1));
    expect(await service.verify('1234'), QuickLoginResult.success);
  });
}
