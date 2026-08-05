import 'package:dio/dio.dart';
import 'package:nnexoris_customer/core/errors/error_mapper.dart';
import 'package:nnexoris_customer/core/network/api_response.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';

class ApiClient implements HttpClient {
  ApiClient(this._dio);

  final Dio _dio;

  Future<ApiResponse<T>> _execute<T>(
    Future<Response<dynamic>> Function() action, {
    T Function(Object? json)? decode,
  }) async {
    try {
      final response = await action();
      final value = decode != null ? decode(response.data) : response.data as T;
      return ApiResponse<T>(
        data: value,
        correlationId: response.correlationId,
        eventVersion: response.eventVersion,
      );
    } on Object catch (error) {
      throw ErrorMapper.toException(error);
    }
  }

  @override
  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? query,
    T Function(Object? json)? decode,
  }) => _execute(
    () => _dio.get<dynamic>(path, queryParameters: query),
    decode: decode,
  );

  @override
  Future<ApiResponse<T>> post<T>(
    String path, {
    Object? data,
    String? idempotencyKey,
    T Function(Object? json)? decode,
  }) => _execute(
    () => _dio.post<dynamic>(
      path,
      data: data,
      options: Options(
        headers: idempotencyKey == null
            ? null
            : {'Idempotency-Key': idempotencyKey},
        extra: {'idempotent': idempotencyKey != null},
      ),
    ),
    decode: decode,
  );

  @override
  Future<ApiResponse<T>> patch<T>(
    String path, {
    Object? data,
    T Function(Object? json)? decode,
  }) => _execute(() => _dio.patch<dynamic>(path, data: data), decode: decode);

  @override
  Future<ApiResponse<void>> delete(String path) =>
      _execute<void>(() => _dio.delete<dynamic>(path), decode: (_) {});
}
