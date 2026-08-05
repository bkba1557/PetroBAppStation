import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/fueling/domain/models/fueling_session.dart';
import 'package:nnexoris_customer/features/fueling/domain/repositories/fueling_repository.dart';

class FuelingRepositoryImpl implements FuelingSessionRepository {
  FuelingRepositoryImpl(this._client);
  final HttpClient _client;

  FuelingSession _decode(Object? json) =>
      FuelingSession.fromJson(json as Map<String, dynamic>);

  @override
  Future<FuelingSession> createSession({
    required FuelingSelection selection,
    required String idempotencyKey,
  }) async =>
      (await _client.post<FuelingSession>(
        ApiEndpoints.fuelingSessions,
        data: selection.toJson(),
        idempotencyKey: idempotencyKey,
        decode: _decode,
      )).data;

  @override
  Future<FuelingSession> getSession(String sessionId) async =>
      (await _client.get<FuelingSession>(
        '${ApiEndpoints.fuelingSessions}/$sessionId',
        decode: _decode,
      )).data;

  @override
  Future<FuelingSession> authorizeSession(
    String sessionId,
    String idempotencyKey,
  ) async =>
      (await _client.post<FuelingSession>(
        ApiEndpoints.authorizeFuelingSession(sessionId),
        idempotencyKey: idempotencyKey,
        decode: _decode,
      )).data;

  @override
  Future<FuelingSession> cancelSession(
    String sessionId,
    String idempotencyKey,
  ) async =>
      (await _client.post<FuelingSession>(
        '${ApiEndpoints.fuelingSessions}/$sessionId/cancel',
        idempotencyKey: idempotencyKey,
        decode: _decode,
      )).data;
}
