import 'package:nnexoris_customer/core/config/api_endpoints.dart';
import 'package:nnexoris_customer/core/network/http_client.dart';
import 'package:nnexoris_customer/features/home/domain/dashboard.dart';

class DashboardRepository {
  DashboardRepository(this.client);
  final HttpClient client;
  Future<DashboardData> dashboard() async => (await client.get<DashboardData>(ApiEndpoints.dashboard,
    decode: (json) => DashboardData.fromJson(json as Map<String, dynamic>))).data;
  Future<AnalyticsData> analytics(String period, {DateTime? from, DateTime? to}) async =>
      (await client.get<AnalyticsData>(ApiEndpoints.analytics,
        query: {'period': period, if (from != null) 'from': from.toUtc().toIso8601String(),
          if (to != null) 'to': to.toUtc().toIso8601String()},
        decode: (json) => AnalyticsData.fromJson(json as Map<String, dynamic>))).data;
}
