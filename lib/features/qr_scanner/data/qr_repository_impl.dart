import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/qr_scanner/domain/models/qr_resolution.dart';
import 'package:nnexoris_customer/features/qr_scanner/domain/repositories/qr_repository.dart';

class QrRepositoryImpl implements QrRepository {
  QrRepositoryImpl(this._client);
  final HttpClient _client;

  @override
  Future<QrValidationResult> resolve(QrPayloadReference reference) async {
    final response = await _client.post<Map<String, dynamic>>(
      ApiEndpoints.qrResolve,
      data: {'token': reference.token},
    );
    final json = response.data;
    final valid = json['valid'] as bool? ?? false;
    return QrValidationResult(
      isValid: valid,
      resolution: valid
          ? QrResolution.fromJson(json['resolution'] as Map<String, dynamic>)
          : null,
      code: json['code'] as String?,
    );
  }
}
