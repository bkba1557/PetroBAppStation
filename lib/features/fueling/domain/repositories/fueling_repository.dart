import 'package:nnexoris_customer/features/fueling/domain/models/fueling_session.dart';

abstract interface class FuelingSessionRepository {
  Future<FuelingSession> createSession({
    required FuelingSelection selection,
    required String idempotencyKey,
  });
  Future<FuelingSession> getSession(String sessionId);

  /// Requests the single semantic authorization after the customer explicitly
  /// confirms the reviewed session.  This is deliberately separate from the
  /// wallet-hold/session creation request.
  Future<FuelingSession> authorizeSession(
    String sessionId,
    String idempotencyKey,
  );
  Future<FuelingSession> cancelSession(String sessionId, String idempotencyKey);
}
