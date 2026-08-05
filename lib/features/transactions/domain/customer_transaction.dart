class CustomerTransaction {
  const CustomerTransaction({required this.id, required this.type, required this.amount, required this.currency,
    required this.createdAt, required this.status, required this.reference, this.station, this.fuelType,
    this.liters, this.unitPrice, this.details = const {}});
  final String id,type,currency,status,reference; final double amount; final DateTime createdAt;
  final String? station,fuelType; final double? liters,unitPrice; final Map<String,dynamic> details;
  factory CustomerTransaction.fromJson(Map<String,dynamic> j)=>CustomerTransaction(
    id:'${j['id']}',type:'${j['type']}',amount:(j['amount'] as num).toDouble(),currency:'${j['currency']}',
    createdAt:DateTime.parse(j['createdAt'] as String),status:'${j['status']}',reference:'${j['referenceNumber']}',
    station:j['station'] as String?,fuelType:j['fuelType'] as String?,liters:(j['liters'] as num?)?.toDouble(),
    unitPrice:(j['unitPrice'] as num?)?.toDouble(),details:j);
}
