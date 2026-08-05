import 'package:nnexoris_customer/features/qr_scanner/domain/models/qr_resolution.dart';

abstract interface class QrRepository {
  Future<QrValidationResult> resolve(QrPayloadReference reference);
}
