import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/vehicles/domain/models/vehicle.dart';

class VehiclesPage extends ConsumerStatefulWidget {
  const VehiclesPage({super.key});
  @override
  ConsumerState<VehiclesPage> createState() => _VehiclesPageState();
}

class _VehiclesPageState extends ConsumerState<VehiclesPage> {
  late Future<List<Vehicle>> rows;
  @override
  void initState() {
    super.initState();
    rows = _load();
  }

  Future<List<Vehicle>> _load() =>
      ref.read(vehicleRepositoryProvider).getVehicles();
  void _refresh() => setState(() => rows = _load());

  Future<void> _edit([Vehicle? current]) async {
    final name = TextEditingController(text: current?.nickname);
    final model = TextEditingController(text: current?.model);
    final digits = TextEditingController();
    final l1 = TextEditingController();
    final l2 = TextEditingController();
    final l3 = TextEditingController();
    var fuel = current?.fuelCode ?? 'unspecified';
    var isDefault = current?.isDefault ?? false;
    final result = await showModalBottomSheet<Vehicle>(
      context: context,
      isScrollControlled: true,
      builder: (sheet) => StatefulBuilder(
        builder: (sheet, setSheet) => Padding(
          padding: EdgeInsets.fromLTRB(
            20,
            20,
            20,
            MediaQuery.viewInsetsOf(sheet).bottom + 24,
          ),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  current == null ? 'إضافة مركبة' : 'تعديل المركبة',
                  style: Theme.of(sheet).textTheme.titleLarge,
                ),
                const SizedBox(height: 18),
                TextField(
                  controller: name,
                  decoration: const InputDecoration(labelText: 'اسم المركبة'),
                ),
                const SizedBox(height: 12),
                const Text(
                  'حروف اللوحة',
                  textAlign: TextAlign.right,
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: l1,
                        maxLength: 1,
                        textAlign: TextAlign.center,
                        decoration: const InputDecoration(
                          labelText: 'حرف 1',
                          counterText: '',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: l2,
                        maxLength: 1,
                        textAlign: TextAlign.center,
                        decoration: const InputDecoration(
                          labelText: 'حرف 2',
                          counterText: '',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: l3,
                        maxLength: 1,
                        textAlign: TextAlign.center,
                        decoration: const InputDecoration(
                          labelText: 'حرف 3',
                          counterText: '',
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: digits,
                  maxLength: 4,
                  keyboardType: TextInputType.number,
                  textAlign: TextAlign.center,
                  decoration: const InputDecoration(
                    labelText: 'أرقام اللوحة',
                    counterText: '',
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: model,
                  decoration: const InputDecoration(labelText: 'الموديل'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: fuel,
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
                const SizedBox(height: 10),
                FilledButton(
                  onPressed: () {
                    final letters = [
                      l1.text.trim(),
                      l2.text.trim(),
                      l3.text.trim(),
                    ].where((x) => x.isNotEmpty).join('');
                    final number = digits.text.trim();
                    if (letters.isEmpty && number.isEmpty) return;
                    Navigator.pop(
                      sheet,
                      Vehicle(
                        id: current?.id ?? '',
                        plateNumber: [
                          number,
                          letters,
                        ].where((x) => x.isNotEmpty).join(' · '),
                        registrationNumber: current?.registrationNumber ?? '',
                        nickname: name.text.trim(),
                        model: model.text.trim(),
                        fuelCode: fuel,
                        isDefault: isDefault,
                      ),
                    );
                  },
                  child: const Text('حفظ المركبة'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    for (final c in [name, model, digits, l1, l2, l3]) {
      c.dispose();
    }
    if (result == null) return;
    if (current == null) {
      await ref.read(vehicleRepositoryProvider).addVehicle(result);
    } else {
      await ref.read(vehicleRepositoryProvider).updateVehicle(result);
    }
    _refresh();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('المركبات')),
    floatingActionButton: FloatingActionButton.extended(
      onPressed: _edit,
      icon: const Icon(Icons.add),
      label: const Text('إضافة مركبة'),
    ),
    body: FutureBuilder<List<Vehicle>>(
      future: rows,
      builder: (context, snap) {
        if (!snap.hasData)
          return const Center(child: CircularProgressIndicator());
        final list = snap.data!;
        if (list.isEmpty)
          return const Center(child: Text('أضف مركبتك الأولى للبدء'));
        return ListView.separated(
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 100),
          itemCount: list.length,
          separatorBuilder: (_, _) => const SizedBox(height: 12),
          itemBuilder: (_, i) {
            final v = list[i];
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    SizedBox(
                      width: 118,
                      height: 66,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          Image.asset(
                            'assets/branding/saudi_license_plate.png',
                            fit: BoxFit.fill,
                          ),
                          Center(
                            child: Text(
                              v.plateNumber,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                fontWeight: FontWeight.w900,
                                fontSize: 11,
                                color: Colors.black87,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            v.nickname?.isNotEmpty == true
                                ? v.nickname!
                                : 'مركبة',
                            style: const TextStyle(fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 5),
                          Text(
                            v.model?.isNotEmpty == true
                                ? v.model!
                                : 'بدون موديل',
                          ),
                          Text(
                            v.fuelCode,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                    PopupMenuButton<String>(
                      onSelected: (x) async {
                        if (x == 'edit') await _edit(v);
                        if (x == 'delete') {
                          await ref
                              .read(vehicleRepositoryProvider)
                              .removeVehicle(v.id);
                          _refresh();
                        }
                      },
                      itemBuilder: (_) => const [
                        PopupMenuItem(value: 'edit', child: Text('تعديل')),
                        PopupMenuItem(value: 'delete', child: Text('حذف')),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    ),
  );
}
