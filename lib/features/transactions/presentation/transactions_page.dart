import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/transactions/domain/customer_transaction.dart';

const _types = {
  'ALL': 'الكل',
  'TOPUP_CREDIT': 'شحن المحفظة',
  'FUELING_HOLD': 'حجز',
  'FUELING_CAPTURE': 'تعبئة',
  'HOLD_RELEASE': 'تحرير حجز',
  'REFUND': 'استرداد',
  'MANUAL_ADJUSTMENT': 'تسوية',
};

class TransactionsPage extends ConsumerStatefulWidget {
  const TransactionsPage({super.key});

  @override
  ConsumerState<TransactionsPage> createState() => _TransactionsPageState();
}

class _TransactionsPageState extends ConsumerState<TransactionsPage> {
  String type = 'ALL';
  final search = TextEditingController();
  late Future<List<CustomerTransaction>> future;

  @override
  void initState() {
    super.initState();
    future = load();
  }

  Future<List<CustomerTransaction>> load() {
    return ref
        .read(transactionRepositoryProvider)
        .list(type: type, search: search.text.trim());
  }

  void reload() => setState(() => future = load());

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext c) => Scaffold(
    appBar: AppBar(title: const Text('المعاملات')),
    body: Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 8, 18, 10),
          child: TextField(
            controller: search,
            onSubmitted: (_) => reload(),
            decoration: InputDecoration(
              prefixIcon: const Icon(Icons.search),
              hintText: 'ابحث بالمرجع أو النوع',
              suffixIcon: IconButton(
                onPressed: reload,
                icon: const Icon(Icons.tune),
              ),
            ),
          ),
        ),
        SizedBox(
          height: 48,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 18),
            children: _types.entries
                .map(
                  (e) => Padding(
                    padding: const EdgeInsetsDirectional.only(end: 8),
                    child: ChoiceChip(
                      label: Text(e.value),
                      selected: type == e.key,
                      onSelected: (_) {
                        type = e.key;
                        reload();
                      },
                    ),
                  ),
                )
                .toList(),
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: FutureBuilder<List<CustomerTransaction>>(
            future: future,
            builder: (c, s) {
              if (s.connectionState != ConnectionState.done) {
                return const _ListSkeleton();
              }
              if (s.hasError) {
                return _State(
                  icon: Icons.cloud_off_outlined,
                  text: 'تعذر تحميل المعاملات',
                  action: reload,
                );
              }

              final rows = s.data ?? const [];
              if (rows.isEmpty) {
                return const _State(
                  icon: Icons.receipt_long_outlined,
                  text: 'لا توجد معاملات مطابقة',
                );
              }

              return RefreshIndicator(
                onRefresh: () async {
                  reload();
                  await future;
                },
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(18, 8, 18, 100),
                  itemCount: rows.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (_, i) => _TransactionCard(rows[i]),
                ),
              );
            },
          ),
        ),
      ],
    ),
  );
}

class _TransactionCard extends StatelessWidget {
  const _TransactionCard(this.row);

  final CustomerTransaction row;

  @override
  Widget build(BuildContext c) {
    final positive = row.amount >= 0;

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: () => c.push(AppRoutes.transaction(row.id)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: (positive ? Colors.green : Colors.orange)
                    .withValues(alpha: .15),
                child: Icon(
                  positive ? Icons.south_west : Icons.north_east,
                  color: positive ? Colors.greenAccent : Colors.orangeAccent,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _types[row.type] ?? row.type,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${row.station ?? 'NNEXORIS'} · ${DateFormat('d MMM، HH:mm', 'ar').format(row.createdAt.toLocal())}',
                      style: Theme.of(c).textTheme.bodySmall,
                    ),
                    if (row.fuelType != null)
                      Text(
                        '${row.fuelType} · ${(row.liters ?? 0).toStringAsFixed(3)} لتر',
                        style: Theme.of(c).textTheme.bodySmall,
                      ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${row.amount.toStringAsFixed(2)} ${row.currency}',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      color: positive ? Colors.greenAccent : null,
                    ),
                  ),
                  Text(row.status, style: Theme.of(c).textTheme.labelSmall),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class TransactionDetailsPage extends ConsumerWidget {
  const TransactionDetailsPage({required this.id, super.key});

  final String id;

  @override
  Widget build(BuildContext c, WidgetRef ref) => Scaffold(
    appBar: AppBar(title: const Text('تفاصيل المعاملة')),
    body: FutureBuilder<CustomerTransaction>(
      future: ref.read(transactionRepositoryProvider).detail(id),
      builder: (c, s) {
        if (!s.hasData) {
          return s.hasError
              ? const _State(
                  icon: Icons.error_outline,
                  text: 'تعذر تحميل التفاصيل',
                )
              : const Center(child: CircularProgressIndicator());
        }

        final r = s.data!;
        final d = r.details;
        final rows = <String, Object?>{
          'رقم المعاملة': d['transactionId'],
          'جلسة التعبئة': d['fuelingSessionId'],
          'المحطة': d['station'],
          'الشركة': d['company'],
          'المضخة': d['pump'],
          'الفوهة': d['nozzle'],
          'نوع الوقود': d['fuelType'],
          'المبلغ المطلوب': d['requestedAmount'],
          'المبلغ الفعلي': d['actualAmount'],
          'اللترات': d['liters'],
          'سعر اللتر': d['unitPrice'],
          'وقت التفويض': d['authorizationTime'],
          'بدء التعبئة': d['fuelingStartTime'],
          'الاكتمال': d['completionTime'],
          'التسوية': d['settlementTime'],
          'الحجز': d['walletHold'],
          'المحصّل': d['capturedAmount'],
          'المحرر': d['releasedAmount'],
          'الحالة': d['finalStatus'],
        };

        return ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 100),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const Icon(
                      Icons.verified_rounded,
                      color: Colors.greenAccent,
                      size: 42,
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '${r.amount.toStringAsFixed(2)} ${r.currency}',
                      style: Theme.of(c).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text(r.reference),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  children: rows.entries
                      .map(
                        (e) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: Text(
                                  e.key,
                                  style: Theme.of(c).textTheme.bodySmall,
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  '${e.value ?? '—'}',
                                  textAlign: TextAlign.end,
                                ),
                              ),
                            ],
                          ),
                        ),
                      )
                      .toList(),
                ),
              ),
            ),
            const SizedBox(height: 14),
            OutlinedButton.icon(
              onPressed: () {
                ScaffoldMessenger.of(c).showSnackBar(
                  const SnackBar(
                    content: Text('يمكن تنزيل الإيصال من رابط الحساب الآمن.'),
                  ),
                );
              },
              icon: const Icon(Icons.download_outlined),
              label: const Text('تنزيل الإيصال'),
            ),
          ],
        );
      },
    ),
  );
}

class _State extends StatelessWidget {
  const _State({required this.icon, required this.text, this.action});

  final IconData icon;
  final String text;
  final VoidCallback? action;

  @override
  Widget build(BuildContext c) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 52),
        const SizedBox(height: 12),
        Text(text),
        if (action != null)
          TextButton(onPressed: action, child: const Text('إعادة المحاولة')),
      ],
    ),
  );
}

class _ListSkeleton extends StatelessWidget {
  const _ListSkeleton();

  @override
  Widget build(BuildContext c) => ListView(
    padding: const EdgeInsets.all(18),
    children: List.generate(
      6,
      (_) => Container(
        height: 92,
        margin: const EdgeInsets.only(bottom: 10),
        decoration: BoxDecoration(
          color: Theme.of(c).cardColor,
          borderRadius: BorderRadius.circular(22),
        ),
      ),
    ),
  );
}
