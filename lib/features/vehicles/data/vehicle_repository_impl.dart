import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/vehicles/domain/models/vehicle.dart';
import 'package:nnexoris_customer/features/vehicles/domain/repositories/vehicle_repository.dart';

class VehicleRepositoryImpl implements VehicleRepository {
  VehicleRepositoryImpl(this._client);
  final HttpClient _client;

  @override
  Future<List<Vehicle>> getVehicles() async =>
      (await _client.get<List<Vehicle>>(
        ApiEndpoints.vehicles,
        decode: (json) => (json as List<dynamic>)
            .map((item) => Vehicle.fromJson(item as Map<String, dynamic>))
            .toList(growable: false),
      ))
          .data;

  @override
  Future<Vehicle> addVehicle(Vehicle vehicle) async =>
      (await _client.post<Vehicle>(
        ApiEndpoints.vehicles,
        data: vehicle.toJson(),
        decode: (json) => Vehicle.fromJson(json as Map<String, dynamic>),
      ))
          .data;

  @override
  Future<void> removeVehicle(String vehicleId) async {
    await _client.delete('${ApiEndpoints.vehicles}/$vehicleId');
  }

  @override
  Future<Vehicle> updateVehicle(Vehicle vehicle) async =>
      (await _client.patch<Vehicle>(
        '${ApiEndpoints.vehicles}/${vehicle.id}',
        data: vehicle.toJson(),
        decode: (json) => Vehicle.fromJson(json as Map<String, dynamic>),
      )).data;
}
