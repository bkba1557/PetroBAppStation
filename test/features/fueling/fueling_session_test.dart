import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/features/fueling/domain/models/fueling_session.dart';

void main() {
  test('only settled is a successful final session', () {
    FuelingSession make(FuelingSessionStatus status) => FuelingSession(
          sessionId: 's', transactionId: 't', idempotencyKey: 'i',
          customerId: 'c', stationId: 'st', pumpId: 'p', nozzleId: 'n',
          fuelProductId: 'f', requestedMode: FuelingMode.fixedAmount,
          requestedAmount: 100, reservedAmount: 100, dispensedAmount: 95,
          dispensedVolume: 40, unitPrice: 2.36, status: status,
          createdAt: DateTime.utc(2026), expiresAt: DateTime.utc(2026, 1, 2),
        );
    expect(make(FuelingSessionStatus.completed).isSuccessful, isFalse);
    expect(make(FuelingSessionStatus.settled).isSuccessful, isTrue);
    expect(make(FuelingSessionStatus.settled).isFinal, isTrue);
  });
}
