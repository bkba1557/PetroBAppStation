import 'package:nnexoris_customer/features/vehicles/domain/models/vehicle.dart';

abstract interface class VehicleRepository {
  Future<List<Vehicle>> getVehicles();
  Future<Vehicle> addVehicle(Vehicle vehicle);
  Future<Vehicle> updateVehicle(Vehicle vehicle);
  Future<void> removeVehicle(String vehicleId);
}
