import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/fueling/domain/models/fueling_session.dart';
import 'package:nnexoris_customer/features/qr_scanner/domain/models/qr_resolution.dart';
import 'package:uuid/uuid.dart';

String _text(BuildContext context, String ar, String en) =>
    Localizations.localeOf(context).languageCode == 'ar' ? ar : en;

class FuelingSetupPage extends ConsumerStatefulWidget {
  const FuelingSetupPage({this.resolution, super.key});

  final QrResolution? resolution;

  @override
  ConsumerState<FuelingSetupPage> createState() => _FuelingSetupPageState();
}

class _FuelingSetupPageState extends ConsumerState<FuelingSetupPage> {
  final amount = TextEditingController();
  bool busy = false;
  String? error;

  Future<void> create() async {
    final value = double.tryParse(amount.text.trim());
    if (widget.resolution == null ||
        value == null ||
        value < 1 ||
        value > 1000) {
      setState(
        () => error = _text(
          context,
          'امسح رمز QR صالحًا وأدخل مبلغًا صحيحًا.',
          'Scan a valid QR code and enter a valid amount.',
        ),
      );
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final session = await ref
          .read(fuelingSessionRepositoryProvider)
          .createSession(
            selection: FuelingSelection(
              qrResolutionId: widget.resolution!.resolutionId,
              requestedMode: FuelingMode.fixedAmount,
              requestedAmount: value,
            ),
            idempotencyKey: const Uuid().v4(),
          );
      if (mounted) context.go(AppRoutes.fueling(session.sessionId));
    } on Object {
      if (mounted) {
        setState(
          () => error = _text(
            context,
            'تعذر إنشاء جلسة التعبئة أو حجز المبلغ.',
            'Could not create the fueling session or reserve the amount.',
          ),
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void dispose() {
    amount.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(context.l10n.fuelingSetup)),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Card(
          child: ListTile(
            leading: const Icon(Icons.verified_user_outlined),
            title: Text(
              _text(
                context,
                'تعبئة فعلية بتفويض واحد',
                'Real fueling with one authorization',
              ),
            ),
            subtitle: Text(
              _text(
                context,
                'بعد حجز المبلغ ستؤكد البدء مرة واحدة. لن ينشئ تكرار الضغط أمرًا جديدًا.',
                'After reserving the amount, confirm once. Repeated taps cannot create another command.',
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        if (widget.resolution == null)
          FilledButton.icon(
            onPressed: () => context.go(AppRoutes.scan),
            icon: const Icon(Icons.qr_code_scanner),
            label: Text(_text(context, 'مسح QR أولًا', 'Scan QR first')),
          )
        else
          Card(
            child: ListTile(
              leading: const Icon(Icons.local_gas_station_outlined),
              title: Text(
                '${_text(context, 'المضخة', 'Pump')}: ${widget.resolution!.pumpId}',
              ),
              subtitle: Text(
                '${_text(context, 'الفوهة', 'Nozzle')}: ${widget.resolution!.nozzleId}',
              ),
            ),
          ),
        const SizedBox(height: 16),
        TextField(
          controller: amount,
          enabled: !busy,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: _text(
              context,
              'المبلغ المطلوب (SAR)',
              'Requested amount (SAR)',
            ),
            prefixIcon: const Icon(Icons.payments_outlined),
          ),
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: busy ? null : create,
          icon: busy
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.lock_outline),
          label: Text(
            _text(
              context,
              'إنشاء الجلسة وحجز المبلغ',
              'Create session and reserve amount',
            ),
          ),
        ),
        if (error != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(
              error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
      ],
    ),
  );
}

class FuelingProgressPage extends ConsumerStatefulWidget {
  const FuelingProgressPage({required this.sessionId, super.key});

  final String sessionId;

  @override
  ConsumerState<FuelingProgressPage> createState() =>
      _FuelingProgressPageState();
}

class _FuelingProgressPageState extends ConsumerState<FuelingProgressPage> {
  bool authorizing = false;
  bool authorizationSubmitted = false;

  String _authorizationKey(FuelingSession session) =>
      '${session.idempotencyKey}:authorize';

  Future<void> _authorize(FuelingSession session) async {
    if (authorizing || authorizationSubmitted) return;
    final confirmed =
        await showDialog<bool>(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            icon: const Icon(Icons.local_gas_station),
            title: Text(
              _text(context, 'تأكيد بدء التعبئة', 'Confirm fueling start'),
            ),
            content: Text(
              _text(
                context,
                'تأكد أنك أمام المضخة والفوهة الظاهرتين. سيُرسل تفويض تعبئة فعلي واحد فقط.',
                'Confirm that you are at the displayed pump and nozzle. One real fueling authorization will be sent.',
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: Text(_text(context, 'رجوع', 'Back')),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text(_text(context, 'تأكيد مرة واحدة', 'Confirm once')),
              ),
            ],
          ),
        ) ??
        false;
    if (!confirmed || !mounted) return;
    setState(() {
      authorizing = true;
      authorizationSubmitted = true;
    });
    try {
      await ref
          .read(fuelingSessionRepositoryProvider)
          .authorizeSession(session.sessionId, _authorizationKey(session));
    } on Object {
      // Reconcile before allowing another attempt. A lost response may still
      // mean that Cloud safely created the single command.
      try {
        final fresh = await ref
            .read(fuelingSessionRepositoryProvider)
            .getSession(session.sessionId);
        if (fresh.status == FuelingSessionStatus.fundsHeld && mounted) {
          setState(() => authorizationSubmitted = false);
        }
      } on Object {
        // Keep the button locked while the result is unknown.
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              _text(
                context,
                'تعذر تأكيد النتيجة. تم قفل الإرسال لمنع التكرار وسيستمر التطبيق في التحقق.',
                'The result could not be confirmed. Sending is locked to prevent duplication while the app reconciles.',
              ),
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => authorizing = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(context.l10n.fuelingProgress)),
    body: StreamBuilder<FuelingSession>(
      stream: ref.read(fuelingSessionMonitorProvider).watch(widget.sessionId),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          if (snapshot.hasError) {
            return Center(
              child: Text(
                _text(
                  context,
                  'تعذر تحديث جلسة التعبئة.',
                  'Could not update the fueling session.',
                ),
              ),
            );
          }
          return const Center(child: CircularProgressIndicator());
        }
        final session = snapshot.data!;
        if (session.status != FuelingSessionStatus.fundsHeld) {
          authorizationSubmitted = true;
        }
        return ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              session.status.name,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            LinearProgressIndicator(
              value:
                  session.requestedAmount == null ||
                      session.requestedAmount == 0
                  ? null
                  : (session.dispensedAmount / session.requestedAmount!)
                        .clamp(0.0, 1.0)
                        .toDouble(),
            ),
            const SizedBox(height: 12),
            Text(
              '${_text(context, 'المبلغ المصروف', 'Dispensed amount')}: ${session.dispensedAmount.toStringAsFixed(2)} SAR',
            ),
            Text(
              '${_text(context, 'الكمية', 'Volume')}: ${session.dispensedVolume.toStringAsFixed(3)} L',
            ),
            Text(
              '${_text(context, 'المبلغ المحجوز', 'Reserved amount')}: ${session.reservedAmount.toStringAsFixed(2)} SAR',
            ),
            const SizedBox(height: 20),
            if (session.status == FuelingSessionStatus.fundsHeld)
              FilledButton.icon(
                onPressed: authorizing || authorizationSubmitted
                    ? null
                    : () => _authorize(session),
                icon: authorizing
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.local_gas_station),
                label: Text(
                  authorizing
                      ? _text(
                          context,
                          'جارٍ إرسال التفويض…',
                          'Sending authorization…',
                        )
                      : _text(
                          context,
                          'بدء التعبئة مرة واحدة',
                          'Start fueling once',
                        ),
                ),
              ),
            if ({
              FuelingSessionStatus.created,
              FuelingSessionStatus.awaitingFunds,
              FuelingSessionStatus.fundsHeld,
              FuelingSessionStatus.qrResolved,
            }.contains(session.status))
              OutlinedButton(
                onPressed: authorizing
                    ? null
                    : () => ref
                          .read(fuelingSessionRepositoryProvider)
                          .cancelSession(widget.sessionId, const Uuid().v4()),
                child: Text(
                  _text(
                    context,
                    'إلغاء الجلسة وتحرير الحجز',
                    'Cancel session and release hold',
                  ),
                ),
              ),
            Card(
              child: ListTile(
                leading: const Icon(Icons.shield_outlined),
                title: Text(
                  _text(
                    context,
                    'Cloud يمنع إنشاء أكثر من أمر لنفس الجلسة.',
                    'Cloud prevents more than one command for this session.',
                  ),
                ),
              ),
            ),
          ],
        );
      },
    ),
  );
}

