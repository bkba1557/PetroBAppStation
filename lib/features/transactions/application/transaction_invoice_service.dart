import 'package:flutter/services.dart';
import 'package:nnexoris_customer/features/transactions/domain/customer_transaction.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

class TransactionInvoiceService {
  const TransactionInvoiceService();

  Future<Uint8List> build(CustomerTransaction transaction) async {
    final fontData = await rootBundle.load('assets/fonts/NotoSansArabic.ttf');
    final logoData = await rootBundle.load('assets/branding/logo.png');
    final font = pw.Font.ttf(fontData);
    final logo = pw.MemoryImage(logoData.buffer.asUint8List());
    final document = pw.Document(
      title: 'PETRO B - ${transaction.reference}',
      author: 'PETRO B',
      subject: 'Electronic transaction invoice',
    );

    final details = _invoiceDetails(transaction);
    final primary = PdfColor.fromInt(0xFF087F6E);
    final navy = PdfColor.fromInt(0xFF071823);
    final pale = PdfColor.fromInt(0xFFEAF8F3);
    final muted = PdfColor.fromInt(0xFF667085);

    document.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        theme: pw.ThemeData.withFont(base: font, bold: font),
        textDirection: pw.TextDirection.rtl,
        header: (context) => pw.Container(
          padding: const pw.EdgeInsets.only(bottom: 14),
          decoration: pw.BoxDecoration(
            border: pw.Border(
              bottom: pw.BorderSide(color: primary, width: 1.5),
            ),
          ),
          child: pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text(
                    'فاتورة إلكترونية',
                    style: pw.TextStyle(
                      color: navy,
                      fontSize: 20,
                      fontWeight: pw.FontWeight.bold,
                    ),
                  ),
                  pw.Text(
                    'ELECTRONIC INVOICE',
                    textDirection: pw.TextDirection.ltr,
                    style: pw.TextStyle(color: muted, fontSize: 8),
                  ),
                ],
              ),
              pw.Container(
                width: 72,
                height: 46,
                alignment: pw.Alignment.center,
                child: pw.Image(logo, fit: pw.BoxFit.contain),
              ),
            ],
          ),
        ),
        footer: (context) => pw.Container(
          padding: const pw.EdgeInsets.only(top: 10),
          decoration: pw.BoxDecoration(
            border: pw.Border(
              top: pw.BorderSide(color: PdfColors.grey300, width: .6),
            ),
          ),
          child: pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Text(
                'تم إنشاء هذه الفاتورة إلكترونيًا من بيانات المعاملة الموثقة.',
                style: pw.TextStyle(color: muted, fontSize: 7),
              ),
              pw.Text(
                '${context.pageNumber} / ${context.pagesCount}',
                textDirection: pw.TextDirection.ltr,
                style: pw.TextStyle(color: muted, fontSize: 7),
              ),
            ],
          ),
        ),
        build: (context) => [
          pw.SizedBox(height: 22),
          pw.Container(
            padding: const pw.EdgeInsets.all(20),
            decoration: pw.BoxDecoration(
              color: pale,
              borderRadius: pw.BorderRadius.circular(12),
            ),
            child: pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                _pdfValue(
                  'إجمالي المعاملة',
                  '${transaction.amount.toStringAsFixed(2)} ${transaction.currency}',
                  primary,
                  large: true,
                ),
                _pdfValue('الحالة', _statusLabel(transaction.status), navy),
                _pdfValue(
                  'التاريخ',
                  _formatDate(transaction.createdAt.toLocal()),
                  navy,
                ),
              ],
            ),
          ),
          pw.SizedBox(height: 20),
          pw.Text(
            'بيانات الفاتورة',
            style: pw.TextStyle(
              color: navy,
              fontSize: 14,
              fontWeight: pw.FontWeight.bold,
            ),
          ),
          pw.SizedBox(height: 8),
          pw.Container(
            decoration: pw.BoxDecoration(
              border: pw.Border.all(color: PdfColors.grey300, width: .7),
              borderRadius: pw.BorderRadius.circular(10),
            ),
            child: pw.Column(
              children: [
                _pdfRow('رقم المرجع', transaction.reference, pale, true),
                ...details.indexed.map(
                  (entry) => _pdfRow(
                    entry.$2.$1,
                    entry.$2.$2,
                    entry.$1.isOdd ? PdfColors.white : pale,
                    false,
                  ),
                ),
              ],
            ),
          ),
          pw.SizedBox(height: 18),
          pw.Container(
            padding: const pw.EdgeInsets.all(12),
            decoration: pw.BoxDecoration(
              color: PdfColor.fromInt(0xFFF8FAFC),
              borderRadius: pw.BorderRadius.circular(8),
            ),
            child: pw.Row(
              children: [
                pw.Container(
                  width: 8,
                  height: 8,
                  decoration: pw.BoxDecoration(
                    color: primary,
                    shape: pw.BoxShape.circle,
                  ),
                ),
                pw.SizedBox(width: 8),
                pw.Expanded(
                  child: pw.Text(
                    'إيصال إلكتروني صادر عن تطبيق PETRO B، ويمكن الاحتفاظ به كمرجع للمعاملة.',
                    style: pw.TextStyle(color: muted, fontSize: 8),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );

    return document.save();
  }

  Future<void> share(CustomerTransaction transaction) async {
    final bytes = await build(transaction);
    final safeReference = transaction.reference.replaceAll(
      RegExp(r'[^a-zA-Z0-9_-]'),
      '-',
    );
    await Printing.sharePdf(
      bytes: bytes,
      filename: 'PETRO-B-Invoice-$safeReference.pdf',
    );
  }
}

pw.Widget _pdfValue(
  String label,
  String value,
  PdfColor color, {
  bool large = false,
}) => pw.Column(
  crossAxisAlignment: pw.CrossAxisAlignment.start,
  children: [
    pw.Text(label, style: const pw.TextStyle(fontSize: 8)),
    pw.SizedBox(height: 3),
    pw.Text(
      value,
      style: pw.TextStyle(
        color: color,
        fontSize: large ? 16 : 10,
        fontWeight: pw.FontWeight.bold,
      ),
    ),
  ],
);

pw.Widget _pdfRow(
  String label,
  String value,
  PdfColor background,
  bool emphasize,
) => pw.Container(
  color: background,
  padding: const pw.EdgeInsets.symmetric(horizontal: 14, vertical: 10),
  child: pw.Row(
    children: [
      pw.Expanded(
        flex: 2,
        child: pw.Text(label, style: const pw.TextStyle(fontSize: 9)),
      ),
      pw.Expanded(
        flex: 3,
        child: pw.Text(
          value,
          textAlign: pw.TextAlign.left,
          style: pw.TextStyle(
            fontSize: 9,
            fontWeight: emphasize ? pw.FontWeight.bold : null,
          ),
        ),
      ),
    ],
  ),
);

List<(String, String)> _invoiceDetails(CustomerTransaction transaction) {
  final d = transaction.details;
  final candidates = <(String, Object?)>[
    ('رقم المعاملة', d['transactionId'] ?? transaction.id),
    ('نوع المعاملة', _typeLabel(transaction.type)),
    ('المحطة', d['station'] ?? transaction.station),
    ('الشركة', d['company']),
    ('نوع الوقود', d['fuelType'] ?? transaction.fuelType),
    ('المضخة', d['pump']),
    ('الفوهة', d['nozzle']),
    ('الكمية', _withUnit(d['liters'] ?? transaction.liters, 'لتر')),
    (
      'سعر اللتر',
      _withUnit(d['unitPrice'] ?? transaction.unitPrice, transaction.currency),
    ),
    ('المبلغ الفعلي', _withUnit(d['actualAmount'], transaction.currency)),
    ('المبلغ المحصّل', _withUnit(d['capturedAmount'], transaction.currency)),
    ('المبلغ المحرر', _withUnit(d['releasedAmount'], transaction.currency)),
    ('وقت الاكتمال', d['completionTime']),
  ];

  return candidates
      .where((row) => row.$2 != null && '${row.$2}'.trim().isNotEmpty)
      .map((row) => (row.$1, '${row.$2}'))
      .toList();
}

String? _withUnit(Object? value, String unit) {
  if (value == null) return null;
  final number = value is num ? value.toStringAsFixed(2) : '$value';
  return '$number $unit';
}

String _formatDate(DateTime date) {
  String two(int value) => value.toString().padLeft(2, '0');
  return '${date.year}/${two(date.month)}/${two(date.day)} - ${two(date.hour)}:${two(date.minute)}';
}

String _statusLabel(String status) => switch (status.toUpperCase()) {
  'SUCCESS' || 'COMPLETED' || 'CAPTURED' => 'مكتملة',
  'PENDING' || 'PROCESSING' || 'HELD' => 'قيد التنفيذ',
  'FAILED' || 'CANCELLED' || 'REJECTED' => 'غير مكتملة',
  _ => status,
};

String _typeLabel(String type) => switch (type) {
  'TOPUP_CREDIT' => 'شحن المحفظة',
  'FUELING_HOLD' => 'حجز مبلغ',
  'FUELING_CAPTURE' => 'تعبئة وقود',
  'HOLD_RELEASE' => 'تحرير حجز',
  'REFUND' => 'استرداد',
  'MANUAL_ADJUSTMENT' => 'تسوية',
  _ => type,
};
