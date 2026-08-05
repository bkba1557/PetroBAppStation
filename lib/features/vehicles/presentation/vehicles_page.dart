import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/vehicles/domain/models/vehicle.dart';

class VehiclesPage extends ConsumerStatefulWidget {
  const VehiclesPage({super.key});

  @override
  ConsumerState<VehiclesPage> createState() => _VehiclesPageState();
}

class _VehiclesPageState extends ConsumerState<VehiclesPage> {
  late Future<List<Vehicle>> vehicles;

  @override
  void initState() {
    super.initState();
    vehicles = load();
  }

  Future<List<Vehicle>> load() =>
      ref.read(vehicleRepositoryProvider).getVehicles();

  void reload() => setState(() => vehicles = load());

  Future<void> edit([Vehicle? current]) async {
    final plate = TextEditingController(text: current?.plateNumber);
    final name = TextEditingController(text: current?.nickname);
    final model = TextEditingController(text: current?.model);
    var fuel = current?.fuelCode ?? 'unspecified';
    var isDefault = current?.isDefault ?? false;

    final result = await showModalBottomSheet<Vehicle>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheet) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            20,
            20,
            MediaQuery.viewInsetsOf(sheetContext).bottom + 24,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  current == null ? 'إضافة مركبة' : 'تعديل المركبة',
                  style: Theme.of(sheetContext).textTheme.titleLarge,
                ),
                const SizedBox(height: 18),
                TextField(
                  controller: name,
                  decoration: const InputDecoration(labelText: 'اسم المركبة'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: plate,
                  decoration: const InputDecoration(labelText: 'رقم اللوحة'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: model,
                  decoration: const InputDecoration(labelText: 'الموديل'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  initialValue: fuel,
                  decoration: const InputDecoration(labelText: 'نوع الوقود'),
                  items: const [
                    DropdownMenuItem(
                      value: 'unspecified',
                      child: Text('غير محدد'),
                    ),
                    DropdownMenuItem(
                      value: 'gasoline91',
                      child: Text('بنزين 91'),
                    ),
                    DropdownMenuItem(
                      value: 'gasoline95',
                      child: Text('بنزين 95'),
                    ),
                    DropdownMenuItem(value: 'diesel', child: Text('ديزل')),
                  ],
                  onChanged: (v) => fuel = v ?? fuel,
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  value: isDefault,
                  onChanged: (v) => setSheet(() => isDefault = v),
                  title: const Text('المركبة الافتراضية'),
                ),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () {
                    if (plate.text.trim().isEmpty) return;
                    Navigator.pop(
                      sheetContext,
                      Vehicle(
                        id: current?.id ?? '',
                        plateNumber: plate.text.trim(),
                        registrationNumber: current?.registrationNumber ?? '',
                        nickname: name.text.trim(),
                        model: model.text.trim(),
                        fuelCode: fuel,
                        isDefault: isDefault,
                      ),
                    );
                  },
                  child: const Text('حفظ'),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    plate.dispose();
    name.dispose();
    model.dispose();

    if (result == null) return;
    if (current == null) {
      await ref.read(vehicleRepositoryProvider).addVehicle(result);
    } else {
      await ref.read(vehicleRepositoryProvider).updateVehicle(result);
    }
    reload();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(context.l10n.vehicles)),
    floatingActionButton: FloatingActionButton.extended(
      onPressed: () => edit(),
      icon: const Icon(Icons.add),
      label: const Text('مركبة'),
    ),
    body: FutureBuilder<List<Vehicle>>(
      future: vehicles,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return const Center(child: Text('تعذر تحميل المركبات'));
        }

        final rows = snapshot.data ?? const [];
        if (rows.isEmpty) {
          return const Center(
            child: Text('أضف مركبتك الأولى لبدء التعبئة الآمنة'),
          );
        }

        return RefreshIndicator(
          onRefresh: () async {
            reload();
            await vehicles;
          },
          child: ListView.separated(
            padding: const EdgeInsets.fromLTRB(18, 10, 18, 100),
            itemCount: rows.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (_, index) {
              final vehicle = rows[index];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 26,
                        backgroundColor: Theme.of(
                          context,
                        ).colorScheme.primaryContainer,
                        child: const Icon(Icons.directions_car),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Flexible(
                                  child: Text(
                                    vehicle.nickname?.isNotEmpty == true
                                        ? vehicle.nickname!
                                        : vehicle.plateNumber,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                if (vehicle.isDefault)
                                  const Padding(
                                    padding: EdgeInsetsDirectional.only(
                                      start: 8,
                                    ),
                                    child: Chip(label: Text('افتراضية')),
                                  ),
                              ],
                            ),
                            Text(
                              '${vehicle.plateNumber} · ${vehicle.model ?? '—'}',
                            ),
                            Text(
                              vehicle.fuelCode,
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      PopupMenuButton<String>(
                        onSelected: (value) async {
                          if (value == 'edit') {
                            await edit(vehicle);
                          }
                          if (value == 'default') {
                            await ref
                                .read(vehicleRepositoryProvider)
                                .updateVehicle(
                                  Vehicle(
                                    id: vehicle.id,
                                    plateNumber: vehicle.plateNumber,
                                    registrationNumber:
                                        vehicle.registrationNumber,
                                    nickname: vehicle.nickname,
                                    model: vehicle.model,
                                    fuelCode: vehicle.fuelCode,
                                    isDefault: true,
                                  ),
                                );
                          }
                          if (value == 'archive') {
                            await ref
                                .read(vehicleRepositoryProvider)
                                .removeVehicle(vehicle.id);
                          }
                          reload();
                        },
                        itemBuilder: (_) => const [
                          PopupMenuItem(value: 'edit', child: Text('تعديل')),
                          PopupMenuItem(
                            value: 'default',
                            child: Text('تعيين افتراضية'),
                          ),
                          PopupMenuItem(value: 'archive', child: Text('أرشفة')),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        );
      },
    ),
  );
}
