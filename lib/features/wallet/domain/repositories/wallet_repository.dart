import 'package:nnexoris_customer/features/wallet/domain/models/wallet.dart';

abstract interface class WalletRepository {
  Future<Wallet> getWallet();
  Future<List<WalletTransaction>> getTransactions({String? cursor});
  Future<WalletTopUp> createTopUp({
    required double amount,
    required String paymentMethodId,
    required String idempotencyKey,
  });
  Future<WalletTopUp> getTopUp(String topUpId);
  Future<void> completeTopUp(String topUpId, String paymentId);
}
