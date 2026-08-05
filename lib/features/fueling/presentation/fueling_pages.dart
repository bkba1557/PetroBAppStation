import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/fueling/domain/models/fueling_session.dart';
import 'package:nnexoris_customer/features/qr_scanner/domain/models/qr_resolution.dart';
import 'package:nnexoris_customer/shared/widgets/branded_app_bar_background.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';
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
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final pageColor = dark ? const Color(0xFF071823) : const Color(0xFFF8FCFB);
    final resolution = widget.resolution;
    final fuel = resolution == null
        ? null
        : _fuelPresentation(context, resolution.fuelProductId);

    return Scaffold(
      backgroundColor: pageColor,
      appBar: AppBar(
        toolbarHeight: 60,
        foregroundColor: Theme.of(context).colorScheme.primary,
        backgroundColor: pageColor,
        title: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(11),
              ),
              child: const Icon(Icons.tune_rounded, size: 19),
            ),
            const SizedBox(width: 10),
            Text(
              context.l10n.fuelingSetup,
              style: const TextStyle(fontWeight: FontWeight.w900),
            ),
          ],
        ),
        flexibleSpace: const BrandedAppBarBackground(),
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
        ),
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      body: BrandedPageBackground(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 100),
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF087F6E), Color(0xFF075F58)],
                ),
                borderRadius: BorderRadius.circular(22),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF087F6E).withValues(alpha: .2),
                    blurRadius: 18,
                    offset: const Offset(0, 7),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: .16),
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: const Icon(
                      Icons.verified_user_outlined,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _text(
                            context,
                            'راجع بيانات التعبئة قبل المتابعة',
                            'Review fueling details before continuing',
                          ),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _text(
                            context,
                            'سيُحجز المبلغ مؤقتًا، ولن يُخصم سوى المبلغ الفعلي بعد اكتمال التعبئة.',
                            'The amount is reserved temporarily; only the actual fueled amount is charged.',
                          ),
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: .86),
                            fontSize: 11,
                            height: 1.45,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            if (resolution == null)
              Card(
                margin: EdgeInsets.zero,
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    children: [
                      const Icon(Icons.qr_code_scanner_rounded, size: 42),
                      const SizedBox(height: 10),
                      Text(
                        _text(
                          context,
                          'امسح باركود المضخة أولًا لعرض بيانات الوقود',
                          'Scan the pump QR code to view fueling details',
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 14),
                      FilledButton.icon(
                        onPressed: () => context.go(AppRoutes.scan),
                        icon: const Icon(Icons.qr_code_scanner_rounded),
                        label: Text(
                          _text(context, 'مسح الباركود', 'Scan QR code'),
                        ),
                      ),
                    ],
                  ),
                ),
              )
            else ...[
              Card(
                margin: EdgeInsets.zero,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 42,
                            height: 42,
                            decoration: BoxDecoration(
                              color: fuel!.color.withValues(alpha: .13),
                              borderRadius: BorderRadius.circular(13),
                            ),
                            child: Icon(
                              Icons.local_gas_station_rounded,
                              color: fuel.color,
                            ),
                          ),
                          const SizedBox(width: 11),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _text(context, 'نوع الوقود', 'Fuel type'),
                                  style: Theme.of(context).textTheme.labelSmall,
                                ),
                                Text(
                                  fuel.label,
                                  style: TextStyle(
                                    color: fuel.color,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(
                            Icons.verified_rounded,
                            color: Color(0xFF087F6E),
                          ),
                        ],
                      ),
                      const SizedBox(height: 13),
                      Divider(
                        color: Theme.of(
                          context,
                        ).dividerColor.withValues(alpha: .4),
                        height: 1,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _SetupDetail(
                              icon: Icons.ev_station_outlined,
                              label: _text(context, 'المضخة', 'Pump'),
                              value: resolution.pumpId,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _SetupDetail(
                              icon: Icons.settings_input_component_outlined,
                              label: _text(context, 'الفوهة', 'Nozzle'),
                              value: resolution.nozzleId,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Card(
                margin: EdgeInsets.zero,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _text(
                          context,
                          'حدد مبلغ التعبئة',
                          'Choose fueling amount',
                        ),
                        style: const TextStyle(fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [50, 100, 150, 200]
                            .map(
                              (value) => ActionChip(
                                side: BorderSide.none,
                                backgroundColor: Theme.of(context)
                                    .colorScheme
                                    .primaryContainer
                                    .withValues(alpha: .62),
                                label: Text(
                                  '$value SAR',
                                  style: TextStyle(
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.primary,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                onPressed: busy
                                    ? null
                                    : () {
                                        amount.text = '$value';
                                        setState(() => error = null);
                                      },
                              ),
                            )
                            .toList(),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: amount,
                        enabled: !busy,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: dark
                              ? const Color(0xFF0E2B2A)
                              : const Color(0xFFEAF8F3),
                          labelText: _text(
                            context,
                            'المبلغ المطلوب (SAR)',
                            'Requested amount (SAR)',
                          ),
                          prefixIcon: const Icon(Icons.payments_outlined),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (error != null) ...[
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(11),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.errorContainer,
                    borderRadius: BorderRadius.circular(13),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded),
                      const SizedBox(width: 8),
                      Expanded(child: Text(error!)),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 14),
              SizedBox(
                height: 50,
                child: FilledButton.icon(
                  onPressed: busy ? null : create,
                  icon: busy
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.lock_outline_rounded),
                  label: Text(
                    _text(
                      context,
                      'متابعة وحجز المبلغ',
                      'Continue and reserve amount',
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                height: 46,
                child: OutlinedButton.icon(
                  onPressed: busy ? null : () => context.go(AppRoutes.scan),
                  icon: const Icon(Icons.qr_code_scanner_rounded),
                  label: Text(
                    _text(
                      context,
                      'رجوع لمسح باركود آخر',
                      'Scan another QR code',
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SetupDetail extends StatelessWidget {
  const _SetupDetail({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(13),
    ),
    child: Row(
      children: [
        Icon(icon, size: 17, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 7),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: Theme.of(context).textTheme.labelSmall),
              Text(
                value,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

({String label, Color color}) _fuelPresentation(
  BuildContext context,
  String raw,
) {
  final code = raw.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '');
  return switch (code) {
    '91' || 'gasoline91' || 'petrol91' => (
      label: _text(context, 'بنزين 91', 'Gasoline 91'),
      color: const Color(0xFF16A34A),
    ),
    '95' || 'gasoline95' || 'petrol95' => (
      label: _text(context, 'بنزين 95', 'Gasoline 95'),
      color: const Color(0xFFDC2626),
    ),
    '98' || 'gasoline98' || 'petrol98' => (
      label: _text(context, 'بنزين 98', 'Gasoline 98'),
      color: const Color(0xFF2563EB),
    ),
    'diesel' => (
      label: _text(context, 'ديزل', 'Diesel'),
      color: const Color(0xFFEAB308),
    ),
    'kerosene' => (
      label: _text(context, 'كيروسين', 'Kerosene'),
      color: const Color(0xFFF97316),
    ),
    _ => (label: raw, color: Theme.of(context).colorScheme.primary),
  };
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
