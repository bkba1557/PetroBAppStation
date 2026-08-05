import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/core/network/retry_interceptor.dart';

void main() {
  final interceptor = RetryInterceptor(Dio());

  test('never retries a sensitive mutation without idempotency key', () {
    final request = RequestOptions(
      path: '/api/customer/fueling-sessions',
      method: 'POST',
    );
    expect(interceptor.canRetry(request), isFalse);
    request.headers['Idempotency-Key'] = 'same-semantic-operation';
    expect(interceptor.canRetry(request), isTrue);
  });
}
