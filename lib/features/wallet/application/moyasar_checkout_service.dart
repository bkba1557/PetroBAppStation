import 'dart:io' show Platform;

import 'package:flutter/material.dart';
import 'package:moyasar/moyasar.dart';
import 'package:nnexoris_customer/features/wallet/domain/models/wallet.dart'
    show WalletTopUp;
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';

class MoyasarCheckoutService {
  Future<String?> present(BuildContext context, WalletTopUp topUp) {
    final key = topUp.publishableKey;
    if (key == null || key.isEmpty) {
      throw StateError('Moyasar publishable key is unavailable');
    }
    return Navigator.of(context).push<String>(
      MaterialPageRoute<String>(
        builder: (_) => _MoyasarCardPage(
          amount: topUp.amount,
          publishableKey: key,
          description: 'PETRO B APP Wallet Top Up ${topUp.id}',
          topUpId: topUp.id,
        ),
      ),
    );
  }
}

class _MoyasarCardPage extends StatelessWidget {
  const _MoyasarCardPage({
    required this.amount,
    required this.publishableKey,
    required this.description,
    required this.topUpId,
  });
  final double amount;
  final String publishableKey;
  final String description;
  final String topUpId;

  @override
  Widget build(BuildContext context) {
    final config = PaymentConfig(
      publishableApiKey: publishableKey,
      amount: (amount * 100).round(),
      currency: 'SAR',
      description: description,
      metadata: {'topup_id': topUpId},
      creditCard: CreditCardConfig(saveCard: false, manual: false),
      applePay: Platform.isIOS
          ? ApplePayConfig(
              merchantId: const String.fromEnvironment(
                'APPLE_PAY_MERCHANT_ID',
                defaultValue: 'merchant.com.petrob.app',
              ),
              label: 'PETRO B APP',
              manual: false,
              saveCard: false,
            )
          : null,
      supportedNetworks: const [
        PaymentNetwork.mada,
        PaymentNetwork.visa,
        PaymentNetwork.masterCard,
        PaymentNetwork.unionPay,
      ],
    );
    return Scaffold(
      appBar: AppBar(title: const Text('الدفع الآمن عبر Moyasar')),
      body: BrandedPageBackground(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 20, 18, 36),
          children: [
            Directionality(
              textDirection: TextDirection.rtl,
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF087F6E), Color(0xFF123548)],
                  ),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'PETRO B APP',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1.2,
                      ),
                    ),
                    SizedBox(height: 10),
                    Text(
                      'دفع آمن ومستقر',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 21,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'بيانات البطاقة تُرسل مباشرة إلى Moyasar ولا تُحفظ داخل التطبيق.',
                      style: TextStyle(color: Colors.white70, height: 1.4),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            if (Platform.isIOS) ...[
              ApplePay(
                config: config,
                onPaymentResult: (result) => _handle(context, result),
              ),
              const SizedBox(height: 12),
              const Center(child: Text('أو ادفع بالبطاقة البنكية')),
              const SizedBox(height: 12),
            ],
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: CreditCard(
                  config: config,
                  locale: const Localization.ar(),
                  onPaymentResult: (result) => _handle(context, result),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handle(BuildContext context, dynamic result) {
    if (result is PaymentResponse &&
        (result.status == PaymentStatus.paid ||
            result.status == PaymentStatus.authorized ||
            result.status == PaymentStatus.captured)) {
      Navigator.of(context).pop(result.id);
    } else if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تعذر إتمام الدفع عبر Moyasar')),
      );
    }
  }
}
