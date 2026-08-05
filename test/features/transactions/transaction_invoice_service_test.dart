import 'package:flutter_test/flutter_test.dart';
import 'package:nnexoris_customer/features/transactions/application/transaction_invoice_service.dart';
import 'package:nnexoris_customer/features/transactions/domain/customer_transaction.dart';

void main() {
  testWidgets('builds a downloadable PDF invoice from transaction data', (
    tester,
  ) async {
    final transaction = CustomerTransaction(
      id: 'transaction-1',
      type: 'FUELING_CAPTURE',
      amount: -95.5,
      currency: 'SAR',
      createdAt: DateTime.utc(2026, 8, 5, 12, 30),
      status: 'COMPLETED',
      reference: 'PB-2026-0001',
      station: 'محطة PETRO B',
      fuelType: 'بنزين 95',
      liters: 40,
      unitPrice: 2.39,
      details: {'pump': 'P-01', 'nozzle': 'N-02', 'actualAmount': 95.5},
    );

    final bytes = await const TransactionInvoiceService().build(transaction);

    expect(bytes.length, greaterThan(1000));
    expect(String.fromCharCodes(bytes.take(4)), '%PDF');
  });
}
