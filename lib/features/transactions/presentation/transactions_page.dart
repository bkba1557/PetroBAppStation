import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/transactions/application/transaction_invoice_service.dart';
import 'package:nnexoris_customer/features/transactions/domain/customer_transaction.dart';
import 'package:nnexoris_customer/shared/widgets/branded_app_bar_background.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';

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

  Future<List<CustomerTransaction>> load() => ref
      .read(transactionRepositoryProvider)
      .list(type: type, search: search.text.trim());

  void reload() => setState(() => future = load());

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final pageColor = dark ? const Color(0xFF071823) : const Color(0xFFF8FCFB);

    return Scaffold(
      backgroundColor: pageColor,
      appBar: _transactionAppBar(
        context,
        title: context.l10n.transactions,
        icon: Icons.receipt_long_rounded,
      ),
      body: BrandedPageBackground(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
              child: TextField(
                controller: search,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => reload(),
                decoration: InputDecoration(
                  filled: true,
                  fillColor: dark
                      ? const Color(0xFF0E2B2A)
                      : const Color(0xFFEAF8F3),
                  prefixIcon: Icon(
                    Icons.search_rounded,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  hintText: 'ابحث بالمرجع أو نوع المعاملة',
                  suffixIcon: IconButton(
                    tooltip: 'بحث',
                    onPressed: reload,
                    icon: const Icon(Icons.arrow_forward_rounded),
                  ),
                ),
              ),
            ),
            SizedBox(
              height: 46,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 18),
                children: _types.entries
                    .map(
                      (entry) => Padding(
                        padding: const EdgeInsetsDirectional.only(end: 8),
                        child: ChoiceChip(
                          showCheckmark: false,
                          selectedColor: const Color(0xFF087F6E),
                          backgroundColor: Theme.of(
                            context,
                          ).colorScheme.primaryContainer.withValues(alpha: .62),
                          labelStyle: TextStyle(
                            color: type == entry.key
                                ? Colors.white
                                : Theme.of(context).colorScheme.primary,
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                          ),
                          label: Text(entry.value),
                          selected: type == entry.key,
                          onSelected: (_) {
                            type = entry.key;
                            reload();
                          },
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
            const SizedBox(height: 6),
            Expanded(
              child: FutureBuilder<List<CustomerTransaction>>(
                future: future,
                builder: (context, snapshot) {
                  if (snapshot.connectionState != ConnectionState.done) {
                    return const _ListSkeleton();
                  }
                  if (snapshot.hasError) {
                    return _State(
                      icon: Icons.cloud_off_outlined,
                      text: 'تعذر تحميل المعاملات',
                      action: reload,
                    );
                  }

                  final rows = snapshot.data ?? const [];
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
                    child: CustomScrollView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      slivers: [
                        SliverPadding(
                          padding: const EdgeInsets.fromLTRB(18, 2, 18, 10),
                          sliver: SliverToBoxAdapter(
                            child: _TransactionsSummary(rows: rows),
                          ),
                        ),
                        SliverPadding(
                          padding: const EdgeInsets.fromLTRB(18, 0, 18, 100),
                          sliver: SliverList.separated(
                            itemCount: rows.length,
                            separatorBuilder: (_, _) =>
                                const SizedBox(height: 8),
                            itemBuilder: (_, index) =>
                                _TransactionCard(rows[index]),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TransactionsSummary extends StatelessWidget {
  const _TransactionsSummary({required this.rows});

  final List<CustomerTransaction> rows;

  @override
  Widget build(BuildContext context) {
    final incoming = rows
        .where((row) => row.amount > 0)
        .fold<double>(0, (sum, row) => sum + row.amount);
    final outgoing = rows
        .where((row) => row.amount < 0)
        .fold<double>(0, (sum, row) => sum + row.amount.abs());
    final currency = rows.first.currency;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: .13),
        ),
      ),
      child: Row(
        children: [
          _SummaryMetric(
            label: 'الوارد',
            value: '${incoming.toStringAsFixed(0)} $currency',
            icon: Icons.south_west_rounded,
            color: const Color(0xFF087F6E),
          ),
          _summaryDivider(context),
          _SummaryMetric(
            label: 'المدفوع',
            value: '${outgoing.toStringAsFixed(0)} $currency',
            icon: Icons.north_east_rounded,
            color: const Color(0xFFE76F51),
          ),
          _summaryDivider(context),
          _SummaryMetric(
            label: 'المعاملات',
            value: '${rows.length}',
            icon: Icons.receipt_outlined,
            color: const Color(0xFF3A78C2),
          ),
        ],
      ),
    );
  }
}

Widget _summaryDivider(BuildContext context) => Container(
  width: 1,
  height: 34,
  color: Theme.of(context).dividerColor.withValues(alpha: .45),
);

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 15, color: color),
        const SizedBox(height: 3),
        Text(
          value,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900),
        ),
        Text(label, style: Theme.of(context).textTheme.labelSmall),
      ],
    ),
  );
}

class _TransactionCard extends StatelessWidget {
  const _TransactionCard(this.row);

  final CustomerTransaction row;

  @override
  Widget build(BuildContext context) {
    final positive = row.amount >= 0;
    final accent = _transactionColor(row.type, positive);

    return Card(
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => context.push(AppRoutes.transaction(row.id)),
        child: Padding(
          padding: const EdgeInsets.all(13),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: .12),
                  borderRadius: BorderRadius.circular(13),
                ),
                child: Icon(
                  _transactionIcon(row.type),
                  color: accent,
                  size: 20,
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            _types[row.type] ?? row.type,
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                        _StatusBadge(status: row.status),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${row.station ?? 'PETRO B'} · ${DateFormat('d MMM، HH:mm', 'ar').format(row.createdAt.toLocal())}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    const SizedBox(height: 5),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            row.reference,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.labelSmall,
                          ),
                        ),
                        Text(
                          '${positive ? '+' : ''}${row.amount.toStringAsFixed(2)} ${row.currency}',
                          style: TextStyle(
                            color: positive
                                ? const Color(0xFF087F6E)
                                : Theme.of(context).colorScheme.onSurface,
                            fontSize: 13,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 4),
              Icon(
                Icons.chevron_right_rounded,
                size: 18,
                color: Theme.of(context).colorScheme.primary,
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
  Widget build(BuildContext context, WidgetRef ref) {
    final pageColor = Theme.of(context).brightness == Brightness.dark
        ? const Color(0xFF071823)
        : const Color(0xFFF8FCFB);

    return Scaffold(
      backgroundColor: pageColor,
      appBar: _transactionAppBar(
        context,
        title: 'تفاصيل المعاملة',
        icon: Icons.description_outlined,
      ),
      body: BrandedPageBackground(
        child: FutureBuilder<CustomerTransaction>(
          future: ref.read(transactionRepositoryProvider).detail(id),
          builder: (context, snapshot) {
            if (!snapshot.hasData) {
              return snapshot.hasError
                  ? const _State(
                      icon: Icons.error_outline_rounded,
                      text: 'تعذر تحميل تفاصيل المعاملة',
                    )
                  : const Center(child: CircularProgressIndicator());
            }

            final transaction = snapshot.data!;
            final rows = _detailRows(transaction);

            return ListView(
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 100),
              children: [
                _InvoiceHero(transaction: transaction),
                const SizedBox(height: 12),
                _DetailsSection(rows: rows),
                const SizedBox(height: 12),
                _InvoiceDownloadButton(transaction: transaction),
                const SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.verified_user_outlined,
                      size: 15,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 6),
                    Flexible(
                      child: Text(
                        'فاتورة إلكترونية منشأة من بيانات المعاملة الموثقة',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.labelSmall,
                      ),
                    ),
                  ],
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _InvoiceHero extends StatelessWidget {
  const _InvoiceHero({required this.transaction});

  final CustomerTransaction transaction;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topRight,
        end: Alignment.bottomLeft,
        colors: [Color(0xFF087F6E), Color(0xFF075F58)],
      ),
      borderRadius: BorderRadius.circular(22),
      boxShadow: [
        BoxShadow(
          color: const Color(0xFF087F6E).withValues(alpha: .22),
          blurRadius: 18,
          offset: const Offset(0, 8),
        ),
      ],
    ),
    child: Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .14),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                _types[transaction.type] ?? transaction.type,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            _StatusBadge(status: transaction.status, onDark: true),
          ],
        ),
        const SizedBox(height: 18),
        const Icon(Icons.verified_rounded, color: Colors.white, size: 34),
        const SizedBox(height: 6),
        Text(
          '${transaction.amount.toStringAsFixed(2)} ${transaction.currency}',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            color: Colors.white,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          transaction.reference,
          textDirection: ui.TextDirection.ltr,
          style: TextStyle(
            color: Colors.white.withValues(alpha: .82),
            fontSize: 12,
          ),
        ),
        const SizedBox(height: 14),
        Divider(color: Colors.white.withValues(alpha: .18), height: 1),
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _HeroMeta(
              icon: Icons.calendar_today_outlined,
              value: DateFormat(
                'd MMMM yyyy',
                'ar',
              ).format(transaction.createdAt.toLocal()),
            ),
            _HeroMeta(
              icon: Icons.schedule_rounded,
              value: DateFormat(
                'HH:mm',
                'ar',
              ).format(transaction.createdAt.toLocal()),
            ),
          ],
        ),
      ],
    ),
  );
}

class _HeroMeta extends StatelessWidget {
  const _HeroMeta({required this.icon, required this.value});

  final IconData icon;
  final String value;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Icon(icon, size: 14, color: Colors.white.withValues(alpha: .82)),
      const SizedBox(width: 5),
      Text(
        value,
        style: TextStyle(
          color: Colors.white.withValues(alpha: .9),
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    ],
  );
}

class _DetailsSection extends StatelessWidget {
  const _DetailsSection({required this.rows});

  final List<(String, String, IconData)> rows;

  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  Icons.list_alt_rounded,
                  size: 17,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const SizedBox(width: 9),
              const Text(
                'بيانات الفاتورة',
                style: TextStyle(fontWeight: FontWeight.w900),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ...rows.indexed.map(
            (entry) => Container(
              padding: const EdgeInsets.symmetric(vertical: 9),
              decoration: BoxDecoration(
                border: entry.$1 == rows.length - 1
                    ? null
                    : Border(
                        bottom: BorderSide(
                          color: Theme.of(
                            context,
                          ).dividerColor.withValues(alpha: .35),
                        ),
                      ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    entry.$2.$3,
                    size: 16,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      entry.$2.$1,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                  Expanded(
                    child: Text(
                      entry.$2.$2,
                      textAlign: TextAlign.end,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

class _InvoiceDownloadButton extends StatefulWidget {
  const _InvoiceDownloadButton({required this.transaction});

  final CustomerTransaction transaction;

  @override
  State<_InvoiceDownloadButton> createState() => _InvoiceDownloadButtonState();
}

class _InvoiceDownloadButtonState extends State<_InvoiceDownloadButton> {
  bool loading = false;

  Future<void> download() async {
    setState(() => loading = true);
    try {
      await const TransactionInvoiceService().share(widget.transaction);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('تعذر إنشاء الفاتورة، حاول مرة أخرى.')),
        );
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => SizedBox(
    height: 50,
    child: FilledButton.icon(
      onPressed: loading ? null : download,
      icon: loading
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.picture_as_pdf_outlined),
      label: Text(loading ? 'جاري تجهيز الفاتورة...' : 'تنزيل الفاتورة PDF'),
    ),
  );
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status, this.onDark = false});

  final String status;
  final bool onDark;

  @override
  Widget build(BuildContext context) {
    final normalized = status.toUpperCase();
    final success = const {
      'SUCCESS',
      'COMPLETED',
      'CAPTURED',
    }.contains(normalized);
    final pending = const {
      'PENDING',
      'PROCESSING',
      'HELD',
    }.contains(normalized);
    final color = success
        ? const Color(0xFF087F6E)
        : pending
        ? const Color(0xFFE09F3E)
        : const Color(0xFFD1495B);
    final label = success
        ? 'مكتملة'
        : pending
        ? 'قيد التنفيذ'
        : status;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
      decoration: BoxDecoration(
        color: onDark
            ? Colors.white.withValues(alpha: .16)
            : color.withValues(alpha: .11),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 5,
            height: 5,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: onDark ? Colors.white : color,
            ),
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: onDark ? Colors.white : color,
              fontSize: 9,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}

PreferredSizeWidget _transactionAppBar(
  BuildContext context, {
  required String title,
  required IconData icon,
}) {
  final pageColor = Theme.of(context).brightness == Brightness.dark
      ? const Color(0xFF071823)
      : const Color(0xFFF8FCFB);

  return AppBar(
    toolbarHeight: 60,
    foregroundColor: Theme.of(context).colorScheme.primary,
    backgroundColor: pageColor,
    title: Row(
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(11),
          ),
          child: Icon(icon, size: 19),
        ),
        const SizedBox(width: 10),
        Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
      ],
    ),
    flexibleSpace: const BrandedAppBarBackground(),
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
    ),
    elevation: 0,
    scrolledUnderElevation: 0,
    surfaceTintColor: Colors.transparent,
  );
}

List<(String, String, IconData)> _detailRows(CustomerTransaction transaction) {
  final details = transaction.details;
  final candidates = <(String, Object?, IconData)>[
    ('رقم المرجع', transaction.reference, Icons.tag_rounded),
    ('رقم المعاملة', details['transactionId'] ?? transaction.id, Icons.numbers),
    (
      'المحطة',
      details['station'] ?? transaction.station,
      Icons.local_gas_station,
    ),
    ('الشركة', details['company'], Icons.business_outlined),
    (
      'نوع الوقود',
      details['fuelType'] ?? transaction.fuelType,
      Icons.water_drop_outlined,
    ),
    ('المضخة', details['pump'], Icons.ev_station_outlined),
    ('الفوهة', details['nozzle'], Icons.settings_input_component_outlined),
    (
      'الكمية',
      _detailUnit(details['liters'] ?? transaction.liters, 'لتر'),
      Icons.opacity,
    ),
    (
      'سعر اللتر',
      _detailUnit(
        details['unitPrice'] ?? transaction.unitPrice,
        transaction.currency,
      ),
      Icons.price_change_outlined,
    ),
    (
      'المبلغ المطلوب',
      _detailUnit(details['requestedAmount'], transaction.currency),
      Icons.request_quote_outlined,
    ),
    (
      'المبلغ الفعلي',
      _detailUnit(details['actualAmount'], transaction.currency),
      Icons.payments_outlined,
    ),
    ('وقت الاكتمال', details['completionTime'], Icons.schedule_rounded),
    ('الحالة النهائية', details['finalStatus'], Icons.verified_outlined),
  ];

  return candidates
      .where((row) => row.$2 != null && '${row.$2}'.trim().isNotEmpty)
      .map((row) => (row.$1, '${row.$2}', row.$3))
      .toList();
}

String? _detailUnit(Object? value, String unit) {
  if (value == null) return null;
  final formatted = value is num ? value.toStringAsFixed(2) : '$value';
  return '$formatted $unit';
}

Color _transactionColor(String type, bool positive) => switch (type) {
  'TOPUP_CREDIT' => const Color(0xFF087F6E),
  'FUELING_CAPTURE' => const Color(0xFFE76F51),
  'FUELING_HOLD' => const Color(0xFFE09F3E),
  'REFUND' || 'HOLD_RELEASE' => const Color(0xFF3A78C2),
  _ => positive ? const Color(0xFF087F6E) : const Color(0xFF6B7280),
};

IconData _transactionIcon(String type) => switch (type) {
  'TOPUP_CREDIT' => Icons.account_balance_wallet_outlined,
  'FUELING_CAPTURE' => Icons.local_gas_station_outlined,
  'FUELING_HOLD' => Icons.lock_clock_outlined,
  'HOLD_RELEASE' => Icons.lock_open_outlined,
  'REFUND' => Icons.replay_rounded,
  _ => Icons.receipt_long_outlined,
};

class _State extends StatelessWidget {
  const _State({required this.icon, required this.text, this.action});

  final IconData icon;
  final String text;
  final VoidCallback? action;

  @override
  Widget build(BuildContext context) => Center(
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
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(18),
    children: List.generate(
      6,
      (_) => Container(
        height: 82,
        margin: const EdgeInsets.only(bottom: 9),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(18),
        ),
      ),
    ),
  );
}
