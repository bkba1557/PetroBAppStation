import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/errors/error_mapper.dart';

void main() {
  test('maps connection errors to safe retryable failure', () {
    final failure = ErrorMapper.toFailure(
      DioException(
        requestOptions: RequestOptions(path: '/wallet'),
        type: DioExceptionType.connectionError,
      ),
    );
    expect(failure.code, 'OFFLINE');
    expect(failure.messageKey, 'errorOffline');
    expect(failure.isRetryable, isTrue);
  });
}
