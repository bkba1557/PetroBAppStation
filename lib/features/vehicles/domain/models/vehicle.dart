import 'package:equatable/equatable.dart';

class Vehicle extends Equatable {
  const Vehicle({
    required this.id,
    required this.plateNumber,
    required this.registrationNumber,
    this.nickname,
    this.vehicleType,
    this.fuelCode = 'unspecified',
    this.model,
    this.year,
    this.imageUrl,
    this.isDefault = false,
  });
  final String id;
  final String plateNumber;
  final String registrationNumber;
  final String? nickname;
  final String? vehicleType, model, imageUrl;
  final String fuelCode;
  final int? year;
  final bool isDefault;
  factory Vehicle.fromJson(Map<String, dynamic> json) => Vehicle(
        id: json['id'] as String,
        plateNumber: json['plateNumber'] as String,
        registrationNumber: json['registrationNumber'] as String? ?? '',
        nickname: json['nickname'] as String?,
        vehicleType: json['vehicleType'] as String?, fuelCode: json['fuelCode'] as String? ?? 'unspecified',
        model: json['model'] as String?, year: json['year'] as int?, imageUrl: json['imageUrl'] as String?,
        isDefault: json['isDefault'] as bool? ?? false,
      );
  Map<String, dynamic> toJson() => {
        'plateNumber': plateNumber,
        'registrationNumber': registrationNumber,
        if (nickname != null) 'nickname': nickname,
        if (vehicleType != null) 'vehicleType': vehicleType, 'fuelCode': fuelCode,
        if (model != null) 'model': model, if (year != null) 'year': year,
        if (imageUrl != null) 'imageUrl': imageUrl, 'isDefault': isDefault,
      };
  @override
  List<Object?> get props => [id, plateNumber, registrationNumber, nickname, vehicleType, fuelCode, model, year, imageUrl, isDefault];
}
