import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/qr_scanner/domain/models/qr_resolution.dart';

class QrScannerPage extends ConsumerStatefulWidget {
  const QrScannerPage({super.key});
  @override
  ConsumerState<QrScannerPage> createState() => _QrScannerPageState();
}

class _QrScannerPageState extends ConsumerState<QrScannerPage> {
  final controller = MobileScannerController(formats: const [BarcodeFormat.qrCode]);
  bool resolving = false;
  String? error;

  Future<void> detected(BarcodeCapture capture) async {
    if (resolving || capture.barcodes.isEmpty) return;
    final value = capture.barcodes.first.rawValue;
    if (value == null || value.isEmpty) return;
    setState(() { resolving = true; error = null; });
    await controller.stop();
    try {
      final result = await ref.read(qrRepositoryProvider).resolve(
            QrPayloadReference(token: value),
          );
      if (!mounted) return;
      if (!result.isValid || result.resolution == null) {
        setState(() { error = result.code ?? 'رمز QR غير صالح'; resolving = false; });
        await controller.start();
        return;
      }
      context.go(AppRoutes.fuelingSetup, extra: result.resolution);
    } on Object {
      if (!mounted) return;
      setState(() { error = 'تعذر التحقق من رمز QR'; resolving = false; });
      await controller.start();
    }
  }

  @override
  void dispose() { controller.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(context.l10n.scanQr)),
        body: Stack(
          fit: StackFit.expand,
          children: [
            MobileScanner(controller: controller, onDetect: detected),
            Center(
              child: Container(
                width: 260,
                height: 260,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.white, width: 3),
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
            ),
            Align(
              alignment: Alignment.bottomCenter,
              child: Container(
                width: double.infinity,
                color: Colors.black87,
                padding: const EdgeInsets.all(20),
                child: Text(
                  error ?? (resolving ? 'جارٍ التحقق…' : context.l10n.scanQrHint),
                  textAlign: TextAlign.center,
                  style: TextStyle(color: error == null ? Colors.white : Colors.redAccent),
                ),
              ),
            ),
          ],
        ),
      );
}
