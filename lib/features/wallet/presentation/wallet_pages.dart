import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/wallet/application/stripe_payment_sheet_service.dart';
import 'package:nnexoris_customer/features/wallet/domain/models/wallet.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';
import 'package:nnexoris_customer/shared/widgets/branded_wallet_card.dart';
import 'package:uuid/uuid.dart';

class WalletPage extends ConsumerWidget {
  const WalletPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
    backgroundColor: Colors.transparent,
    appBar: AppBar(
      title: Text(
        context.l10n.wallet,
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
      backgroundColor: Colors.transparent,
    ),
    body: BrandedPageBackground(
      child: FutureBuilder(
        future: ref.read(walletRepositoryProvider).getWallet(),
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || !snapshot.hasData) {
            return const Center(child: Text('تعذر تحميل المحفظة'));
          }
          final wallet = snapshot.data!;
          final balance = wallet.balance;
          return ListView(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 108),
            children: [
              BrandedWalletCard(
                available:
                    '${balance.available.toStringAsFixed(2)} ${balance.currency}',
                reserved:
                    '${balance.reserved.toStringAsFixed(2)} ${balance.currency}',
                onTopUp: () => context.push(AppRoutes.walletTopUp),
              ),
              const SizedBox(height: 14),
              Card(
                child: ListTile(
                  dense: true,
                  leading: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(13),
                    ),
                    child: Icon(
                      Icons.receipt_long_outlined,
                      size: 20,
                      color: Theme.of(context).colorScheme.onPrimaryContainer,
                    ),
                  ),
                  title: const Text(
                    'كل المعاملات',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                  ),
                  subtitle: const Text(
                    'الشحن والتعبئات والحجوزات والاستردادات',
                    style: TextStyle(fontSize: 10),
                  ),
                  trailing: const Icon(Icons.chevron_right_rounded, size: 19),
                  onTap: () => context.push(AppRoutes.transactions),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _WalletMetric('إجمالي الشحن', wallet.totalCredited),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _WalletMetric('إجمالي الإنفاق', wallet.totalSpent),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              _WalletMetric('إجمالي المسترد', wallet.totalRefunded),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Row(
                        children: [
                          Icon(
                            Icons.shield_outlined,
                            color: Colors.greenAccent,
                          ),
                          SizedBox(width: 10),
                          Text(
                            'محفظة محمية',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 8),
                      Text(
                        'الرصيد محسوب من سجل مالي غير قابل للتعديل. لا يتم اعتماد الشحن إلا بعد Webhook موثّق من Stripe.',
                        style: TextStyle(fontSize: 11, height: 1.5),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    ),
  );
}

class _WalletMetric extends StatelessWidget {
  const _WalletMetric(this.label, this.value);
  final String label;
  final double value;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelSmall),
          const SizedBox(height: 4),
          Text(
            '${value.toStringAsFixed(2)} SAR',
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
        ],
      ),
    ),
  );
}

class WalletTopUpPage extends ConsumerStatefulWidget {
  const WalletTopUpPage({super.key});
  @override
  ConsumerState<WalletTopUpPage> createState() => _WalletTopUpPageState();
}

class _WalletTopUpPageState extends ConsumerState<WalletTopUpPage> {
  final amount = TextEditingController();
  bool busy = false;
  String? message;
  final presets = const [50.0, 100.0, 200.0, 500.0];

  Future<void> submit() async {
    final value = double.tryParse(amount.text);
    if (value == null || value < 1) {
      setState(() => message = 'أدخل مبلغًا صحيحًا');
      return;
    }
    setState(() {
      busy = true;
      message = null;
    });
    try {
      final topUp = await ref
          .read(walletRepositoryProvider)
          .createTopUp(
            amount: value,
            paymentMethodId: 'payment_sheet',
            idempotencyKey: const Uuid().v4(),
          );
      await StripePaymentSheetService().present(topUp);
      // PaymentSheet completion is not financial proof. The webhook updates
      // the ledger; this GET only reconciles the trusted server state.
      var verified = await ref
          .read(walletRepositoryProvider)
          .getTopUp(topUp.id);
      for (
        var attempt = 0;
        attempt < 10 && verified.status != WalletTopUpStatus.paid;
        attempt += 1
      ) {
        await Future<void>.delayed(const Duration(seconds: 2));
        verified = await ref.read(walletRepositoryProvider).getTopUp(topUp.id);
      }
      setState(
        () => message = verified.status == WalletTopUpStatus.paid
            ? 'تم تحديث المحفظة عبر Webhook موثوق'
            : 'الدفع قيد التحقق',
      );
    } on Object {
      setState(() => message = 'تعذر إكمال عملية الدفع');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void dispose() {
    amount.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(context.l10n.topUp)),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text('اختر مبلغ الشحن', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 14),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: presets
              .map(
                (value) => ChoiceChip(
                  label: Text('${value.toInt()} SAR'),
                  selected: amount.text == value.toStringAsFixed(0),
                  onSelected: (_) =>
                      setState(() => amount.text = value.toStringAsFixed(0)),
                ),
              )
              .toList(),
        ),
        const SizedBox(height: 18),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  controller: amount,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    labelText: 'المبلغ بالريال',
                  ),
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: busy ? null : submit,
                  child: busy
                      ? const CircularProgressIndicator()
                      : const Text('الدفع التجريبي'),
                ),
                if (message != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 16),
                    child: Text(message!),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        const ListTile(
          leading: Icon(Icons.lock_outline),
          title: Text('Stripe PaymentSheet · Test Mode'),
          subtitle: Text('لا تُخزّن بيانات البطاقة داخل NNEXORIS.'),
        ),
      ],
    ),
  );
}

class WalletTransactionsPage extends ConsumerWidget {
  const WalletTransactionsPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
    appBar: AppBar(title: Text(context.l10n.transactions)),
    body: FutureBuilder(
      future: ref.read(walletRepositoryProvider).getTransactions(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        return ListView.builder(
          itemCount: snapshot.data!.length,
          itemBuilder: (_, index) {
            final item = snapshot.data![index];
            return ListTile(
              title: Text(item.type),
              subtitle: Text(item.createdAt.toLocal().toString()),
              trailing: Text(
                '${item.amount.toStringAsFixed(2)} ${item.currency}',
              ),
            );
          },
        );
      },
    ),
  );
}
