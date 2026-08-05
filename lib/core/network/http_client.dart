import 'package:dio/dio.dart';
import 'package:nnexoris_customer/core/network/api_response.dart';

abstract interface class HttpClient {
  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? query,
    T Function(Object? json)? decode,
  });

  Future<ApiResponse<T>> post<T>(
    String path, {
    Object? data,
    String? idempotencyKey,
    T Function(Object? json)? decode,
  });

  Future<ApiResponse<T>> patch<T>(
    String path, {
    Object? data,
    T Function(Object? json)? decode,
  });

  Future<ApiResponse<void>> delete(String path);
}

extension ResponseMetadata on Response<dynamic> {
  String? get correlationId => headers.value('x-correlation-id');
  int? get eventVersion => int.tryParse(headers.value('x-event-version') ?? '');
}
