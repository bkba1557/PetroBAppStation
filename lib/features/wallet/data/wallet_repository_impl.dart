import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/wallet/domain/models/wallet.dart';
import 'package:nnexoris_customer/features/wallet/domain/repositories/wallet_repository.dart';

class WalletRepositoryImpl implements WalletRepository {
  WalletRepositoryImpl(this._client);
  final HttpClient _client;

  @override
  Future<Wallet> getWallet() async => (await _client.get<Wallet>(
    ApiEndpoints.wallet,
    decode: (json) => Wallet.fromJson(json as Map<String, dynamic>),
  )).data;

  @override
  Future<List<WalletTransaction>> getTransactions({String? cursor}) async =>
      (await _client.get<List<WalletTransaction>>(
        ApiEndpoints.walletTransactions,
        query: {?cursor: cursor},
        decode: (json) => (json as List<dynamic>)
            .map(
              (item) =>
                  WalletTransaction.fromJson(item as Map<String, dynamic>),
            )
            .toList(growable: false),
      )).data;

  @override
  Future<WalletTopUp> createTopUp({
    required double amount,
    required String paymentMethodId,
    required String idempotencyKey,
  }) async => (await _client.post<WalletTopUp>(
    ApiEndpoints.walletTopUps,
    data: {'amount': amount, 'paymentMethodId': paymentMethodId},
    idempotencyKey: idempotencyKey,
    decode: (json) => WalletTopUp.fromJson(json as Map<String, dynamic>),
  )).data;

  @override
  Future<WalletTopUp> getTopUp(String topUpId) async =>
      (await _client.get<WalletTopUp>(
        '${ApiEndpoints.walletTopUps}/$topUpId',
        decode: (json) => WalletTopUp.fromJson(json as Map<String, dynamic>),
      )).data;
}
