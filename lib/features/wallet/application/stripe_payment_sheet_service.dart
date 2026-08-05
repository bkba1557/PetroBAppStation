import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:nnexoris_customer/features/wallet/domain/models/wallet.dart';

class StripePaymentSheetService {
  Future<void> present(WalletTopUp topUp) async {
    final publishableKey = topUp.publishableKey;
    final clientSecret = topUp.clientSecret;
    if (publishableKey == null || clientSecret == null) {
      throw StateError('PaymentIntent client configuration is missing');
    }
    if (!publishableKey.startsWith('pk_test_')) {
      throw StateError('Only Stripe test mode is enabled');
    }
    Stripe.publishableKey = publishableKey;
    await Stripe.instance.applySettings();
    await Stripe.instance.initPaymentSheet(
      paymentSheetParameters: SetupPaymentSheetParameters(
        paymentIntentClientSecret: clientSecret,
        merchantDisplayName: 'NNEXORIS',
      ),
    );
    await Stripe.instance.presentPaymentSheet();
  }
}
