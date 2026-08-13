import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/formatters/currency.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/wallet/application/moyasar_checkout_service.dart';
import 'package:nnexoris_customer/features/wallet/domain/models/wallet.dart';
import 'package:nnexoris_customer/shared/widgets/branded_app_bar_background.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';
import 'package:nnexoris_customer/shared/widgets/branded_wallet_card.dart';
import 'package:uuid/uuid.dart';

class WalletPage extends ConsumerWidget {
  const WalletPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
    backgroundColor: Theme.of(context).brightness == Brightness.dark
        ? const Color(0xFF071823)
        : const Color(0xFFF8FCFB),
    appBar: AppBar(
      toolbarHeight: 60,
      foregroundColor: Theme.of(context).colorScheme.primary,
      title: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(11),
            ),
            child: const Icon(Icons.account_balance_wallet_rounded, size: 19),
          ),
          const SizedBox(width: 10),
          Text(
            context.l10n.wallet,
            style: const TextStyle(fontWeight: FontWeight.w900),
          ),
        ],
      ),
      backgroundColor: Theme.of(context).brightness == Brightness.dark
          ? const Color(0xFF071823)
          : const Color(0xFFF8FCFB),
      flexibleSpace: const BrandedAppBarBackground(),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
      ),
      elevation: 0,
      scrolledUnderElevation: 0,
      surfaceTintColor: Colors.transparent,
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
                available: balance.available,
                reserved: balance.reserved,
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
                        'الرصيد محسوب من سجل مالي غير قابل للتعديل. لا يتم اعتماد الشحن إلا بعد تحقق آمن من Moyasar.',
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
            formatSaudiRiyal(value),
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
  bool messageIsError = false;
  final presets = const [50.0, 100.0, 200.0, 500.0];

  Future<void> submit() async {
    final value = double.tryParse(amount.text);
    if (value == null || value < 1) {
      setState(() {
        message = 'أدخل مبلغًا صحيحًا';
        messageIsError = true;
      });
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() {
      busy = true;
      message = null;
      messageIsError = false;
    });
    try {
      final topUp = await ref
          .read(walletRepositoryProvider)
          .createTopUp(
            amount: value,
            paymentMethodId: 'payment_sheet',
            idempotencyKey: const Uuid().v4(),
          );
      if (!mounted) return;
      final paymentId = await MoyasarCheckoutService().present(context, topUp);
      if (paymentId != null && mounted) {
        await ref.read(walletRepositoryProvider).completeTopUp(topUp.id, paymentId);
      }
      // PaymentSheet completion is not financial proof. The webhook updates
      // the ledger; this GET only reconciles the trusted server state.
      var verified = await ref
          .read(walletRepositoryProvider)
          .getTopUp(topUp.id);
      for (
        var attempt = 0;
        attempt < 30 && verified.status != WalletTopUpStatus.paid;
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
      setState(() {
        message = 'تعذر إكمال عملية الدفع';
        messageIsError = true;
      });
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
    backgroundColor: Theme.of(context).brightness == Brightness.dark
        ? const Color(0xFF071823)
        : const Color(0xFFF8FCFB),
    appBar: AppBar(
      toolbarHeight: 60,
      foregroundColor: Theme.of(context).colorScheme.primary,
      title: Text(
        context.l10n.topUp,
        style: const TextStyle(fontWeight: FontWeight.w900),
      ),
      backgroundColor: Theme.of(context).brightness == Brightness.dark
          ? const Color(0xFF071823)
          : const Color(0xFFF8FCFB),
      flexibleSpace: const BrandedAppBarBackground(),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
      ),
      elevation: 0,
      scrolledUnderElevation: 0,
      surfaceTintColor: Colors.transparent,
    ),
    body: BrandedPageBackground(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 34),
        children: [
          _TopUpHero(
            title: context.l10n.topUpTitle,
            subtitle: context.l10n.topUpSubtitle,
          ),
          const SizedBox(height: 18),
          Text(
            context.l10n.chooseTopUpAmount,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 10),
          Row(
            children: presets
                .map((value) {
                  final selected = amount.text == value.toStringAsFixed(0);
                  final colors = Theme.of(context).colorScheme;
                  return Expanded(
                    child: Padding(
                      padding: EdgeInsetsDirectional.only(
                        end: value == presets.last ? 0 : 7,
                      ),
                      child: ChoiceChip(
                        showCheckmark: false,
                        selectedColor: const Color(0xFF087F6E),
                        backgroundColor: colors.primaryContainer.withValues(
                          alpha: 0.72,
                        ),
                        side: BorderSide(
                          color: selected
                              ? const Color(0xFF087F6E)
                              : colors.primary.withValues(alpha: 0.24),
                        ),
                        labelStyle: TextStyle(
                          color: selected ? Colors.white : colors.primary,
                          fontWeight: FontWeight.w900,
                        ),
                        label: SizedBox(
                          width: double.infinity,
                          child: Text(
                            '${value.toInt()}',
                            textAlign: TextAlign.center,
                          ),
                        ),
                        selected: selected,
                        onSelected: (_) => setState(
                          () => amount.text = value.toStringAsFixed(0),
                        ),
                      ),
                    ),
                  );
                })
                .toList(growable: false),
          ),
          const SizedBox(height: 16),
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
              side: BorderSide(
                color: Theme.of(
                  context,
                ).colorScheme.outlineVariant.withValues(alpha: 0.55),
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    context.l10n.customAmount,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 11),
                  TextField(
                    controller: amount,
                    enabled: !busy,
                    onChanged: (_) => setState(() {}),
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                    ),
                    decoration: InputDecoration(
                      labelText: context.l10n.amountInSar,
                      prefixIcon: const Icon(Icons.payments_rounded),
                      suffix: SaudiRiyalMark(
                        size: 19,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ),
                  ),
                  if (message != null) ...[
                    const SizedBox(height: 12),
                    _PaymentMessage(message: message!, isError: messageIsError),
                  ],
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: busy ? null : submit,
                      icon: busy
                          ? const SizedBox(
                              width: 19,
                              height: 19,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.2,
                              ),
                            )
                          : const Icon(Icons.arrow_forward_rounded),
                      label: Text(context.l10n.continueToPayment),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          _SecurePaymentNote(
            title: context.l10n.securePayment,
            description: context.l10n.securePaymentDescription,
          ),
        ],
      ),
    ),
  );
}

class _TopUpHero extends StatelessWidget {
  const _TopUpHero({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: AlignmentDirectional.topStart,
        end: AlignmentDirectional.bottomEnd,
        colors: [Color(0xFF087F6E), Color(0xFF16A085)],
      ),
      borderRadius: BorderRadius.circular(22),
      boxShadow: [
        BoxShadow(
          color: const Color(0xFF087F6E).withValues(alpha: 0.22),
          blurRadius: 24,
          offset: const Offset(0, 10),
        ),
      ],
    ),
    child: Row(
      children: [
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.17),
            borderRadius: BorderRadius.circular(17),
          ),
          child: const Icon(
            Icons.add_card_rounded,
            color: Colors.white,
            size: 27,
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.white.withValues(alpha: 0.84),
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _PaymentMessage extends StatelessWidget {
  const _PaymentMessage({required this.message, required this.isError});

  final String message;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    final color = isError
        ? Theme.of(context).colorScheme.error
        : const Color(0xFF087F6E);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 9),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.22)),
      ),
      child: Row(
        children: [
          Icon(
            isError ? Icons.error_outline_rounded : Icons.check_circle_outline,
            size: 19,
            color: color,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: color,
                fontSize: 11,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SecurePaymentNote extends StatelessWidget {
  const _SecurePaymentNote({required this.title, required this.description});

  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest.withValues(alpha: 0.52),
        borderRadius: BorderRadius.circular(17),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: colors.primaryContainer,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.lock_rounded, size: 19, color: colors.primary),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  description,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: colors.onSurfaceVariant,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 6),
          const Text(
            'Moyasar',
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900),
          ),
        ],
      ),
    );
  }
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
