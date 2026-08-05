import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/realtime/realtime_client.dart';
import 'package:nnexoris_customer/core/realtime/realtime_event.dart';

void main() {
  test('rejects duplicate and stale events per entity', () {
    final gate = RealtimeSequenceGate();
    RealtimeEvent event(String id, int sequence) => RealtimeEvent(
          eventId: id, eventType: 'fueling.progress', entityId: 'session-1',
          sequence: sequence, occurredAt: DateTime.utc(2026), payload: const {},
        );
    expect(gate.accept(event('e2', 2)), isTrue);
    expect(gate.accept(event('e1', 1)), isFalse);
    expect(gate.accept(event('e2', 3)), isFalse);
    expect(gate.accept(event('e3', 3)), isTrue);
  });
}
