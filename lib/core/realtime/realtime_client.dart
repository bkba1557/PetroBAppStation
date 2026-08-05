import 'package:nnexoris_customer/core/realtime/realtime_event.dart';

enum RealtimeConnectionState {
  disconnected,
  connecting,
  connected,
  reconnecting,
  polling,
  failed,
}

abstract interface class RealtimeClient {
  Stream<RealtimeEvent> events({String? sessionId});
  Stream<RealtimeConnectionState> get connectionStates;
  Future<void> connect();
  Future<void> disconnect();
}

class RealtimeSequenceGate {
  final Map<String, int> _lastSequence = {};
  final Set<String> _eventIds = {};

  bool accept(RealtimeEvent event) {
    if (_eventIds.contains(event.eventId)) return false;
    final last = _lastSequence[event.entityId];
    if (last != null && event.sequence <= last) return false;
    _eventIds.add(event.eventId);
    _lastSequence[event.entityId] = event.sequence;
    return true;
  }

  void resetEntity(String entityId) => _lastSequence.remove(entityId);
}
