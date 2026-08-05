class DashboardData {
  const DashboardData({required this.customer, required this.wallet, required this.summary});
  final Map<String, dynamic> customer;
  final Map<String, dynamic> wallet;
  final Map<String, dynamic> summary;
  factory DashboardData.fromJson(Map<String, dynamic> json) => DashboardData(
    customer: Map<String, dynamic>.from(json['customer'] as Map),
    wallet: Map<String, dynamic>.from(json['wallet'] as Map),
    summary: Map<String, dynamic>.from(json['monthlySummary'] as Map),
  );
}

class AnalyticsData {
  const AnalyticsData({required this.timeSeries, required this.fuels, required this.stations,
    required this.vehicles, required this.averages, required this.statuses, required this.topUps});
  final List<Map<String, dynamic>> timeSeries, fuels, stations, vehicles, statuses, topUps;
  final Map<String, dynamic> averages;
  factory AnalyticsData.fromJson(Map<String, dynamic> json) => AnalyticsData(
    timeSeries: _list(json['timeSeries']), fuels: _list(json['fuelDistribution']),
    stations: _list(json['topStations']), vehicles: _list(json['topVehicles']),
    averages: Map<String, dynamic>.from(json['averages'] as Map),
    statuses: _list(json['sessionStatuses']), topUps: _list(json['topUps']),
  );
  static List<Map<String, dynamic>> _list(Object? value) =>
      (value as List? ?? const []).map((e) => Map<String, dynamic>.from(e as Map)).toList(growable: false);
}
