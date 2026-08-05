import 'package:json_annotation/json_annotation.dart';

part 'error_payload_dto.g.dart';

@JsonSerializable(createToJson: false)
class ErrorPayloadDto {
  const ErrorPayloadDto({this.code, this.error, this.correlationId});
  final String? code;
  final String? error;
  final String? correlationId;

  factory ErrorPayloadDto.fromJson(Map<String, dynamic> json) =>
      _$ErrorPayloadDtoFromJson(json);
}
