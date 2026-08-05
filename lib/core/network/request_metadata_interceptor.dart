import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

typedef LocaleTagReader = String Function();

class RequestMetadataInterceptor extends Interceptor {
  RequestMetadataInterceptor({
    required this.localeTag,
    required this.appVersion,
    required this.deviceId,
    Uuid? uuid,
  }) : _uuid = uuid ?? const Uuid();

  final LocaleTagReader localeTag;
  final String appVersion;
  final String deviceId;
  final Uuid _uuid;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers.addAll({
      'Accept': 'application/json',
      'Accept-Language': localeTag(),
      'X-App-Version': appVersion,
      'X-Device-Id': deviceId,
      'X-Correlation-Id': _uuid.v4(),
    });
    handler.next(options);
  }
}
