import 'dart:async';

import 'package:nnexoris_customer/core/realtime/realtime_client.dart';
import 'package:nnexoris_customer/core/realtime/realtime_event.dart';

/// Adapter boundary for a future authenticated SSE transport. The presentation
/// layer depends only on [RealtimeClient], so transport selection remains a
/// composition-root decision.
class SseRealtimeClient implements RealtimeClient {
  SseRealtimeClient(this._source);

  final Stream<RealtimeEvent> Function() _source;
  final _states = StreamController<RealtimeConnectionState>.broadcast();
  final _events = StreamController<RealtimeEvent>.broadcast();
  StreamSubscription<RealtimeEvent>? _subscription;

  @override
  Future<void> connect() async {
    _states.add(RealtimeConnectionState.connecting);
    await _subscription?.cancel();
    _subscription = _source().listen(
      _events.add,
      onError: _events.addError,
      onDone: () => _states.add(RealtimeConnectionState.reconnecting),
    );
    _states.add(RealtimeConnectionState.connected);
  }

  @override
  Stream<RealtimeConnectionState> get connectionStates => _states.stream;

  @override
  Future<void> disconnect() async {
    await _subscription?.cancel();
    _subscription = null;
    _states.add(RealtimeConnectionState.disconnected);
  }

  @override
  Stream<RealtimeEvent> events({String? sessionId}) =>
      _events.stream.where(
        (event) => sessionId == null || event.entityId == sessionId,
      );
}
