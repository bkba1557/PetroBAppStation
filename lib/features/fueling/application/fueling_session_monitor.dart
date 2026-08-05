import 'dart:async';

import 'package:nnexoris_customer/core/realtime/realtime_client.dart';
import 'package:nnexoris_customer/features/fueling/domain/models/fueling_session.dart';
import 'package:nnexoris_customer/features/fueling/domain/repositories/fueling_repository.dart';

class FuelingSessionMonitor {
  FuelingSessionMonitor(this._repository, this._realtime);

  final FuelingSessionRepository _repository;
  final RealtimeClient _realtime;

  Stream<FuelingSession> watch(String sessionId) {
    late final StreamController<FuelingSession> controller;
    StreamSubscription<dynamic>? eventsSubscription;
    StreamSubscription<RealtimeConnectionState>? stateSubscription;
    Timer? pollingTimer;

    Future<void> reconcile() async {
      try {
        controller.add(await _repository.getSession(sessionId));
      } on Object catch (error, stackTrace) {
        if (!controller.isClosed) controller.addError(error, stackTrace);
      }
    }

    controller = StreamController<FuelingSession>(
      onListen: () {
        unawaited(reconcile());
        eventsSubscription = _realtime.events(sessionId: sessionId).listen((event) {
          if (event.eventType == 'FUELING_SESSION_UPDATED' ||
              event.eventType == 'SETTLED' ||
              event.eventType == 'FAILED') {
            unawaited(reconcile());
          }
        });
        stateSubscription = _realtime.connectionStates.listen((state) {
          if (state == RealtimeConnectionState.connected) {
            pollingTimer?.cancel();
            unawaited(reconcile());
          } else if (state == RealtimeConnectionState.polling) {
            pollingTimer?.cancel();
            pollingTimer = Timer.periodic(
              const Duration(seconds: 5),
              (_) => unawaited(reconcile()),
            );
          }
        });
      },
      onCancel: () async {
        pollingTimer?.cancel();
        await eventsSubscription?.cancel();
        await stateSubscription?.cancel();
      },
    );
    return controller.stream;
  }
}
