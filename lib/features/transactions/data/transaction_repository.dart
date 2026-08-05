import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/transactions/domain/customer_transaction.dart';

class TransactionRepository {
  TransactionRepository(this.client); final HttpClient client;
  Future<List<CustomerTransaction>> list({String type='ALL',String search=''}) async =>
    (await client.get<List<CustomerTransaction>>(ApiEndpoints.transactions,query:{'type':type,if(search.isNotEmpty)'search':search},decode:(json){
      final items=(json as Map<String,dynamic>)['items'] as List<dynamic>;
      return items.map((e)=>CustomerTransaction.fromJson(Map<String,dynamic>.from(e as Map))).toList(growable:false);
    })).data;
  Future<CustomerTransaction> detail(String id) async => (await client.get<CustomerTransaction>('${ApiEndpoints.transactions}/$id',
    decode:(json)=>CustomerTransaction.fromJson(json as Map<String,dynamic>))).data;
}
