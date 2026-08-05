import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_controller.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';

class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  Future<void> _configureQuickLogin() async {
    final service = ref.read(quickLoginServiceProvider);
    final enabled = await service.isEnabled();
    if (!mounted) return;
    if (enabled) {
      final disable = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('إيقاف الدخول السريع؟'),
          content: const Text(
            'ستحتاج إلى البريد وكلمة المرور عند الدخول القادم.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('إلغاء'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('إيقاف'),
            ),
          ],
        ),
      );
      if (disable == true) await service.disable();
    } else {
      final pin = await showDialog<String>(
        context: context,
        barrierDismissible: false,
        builder: (_) => const _QuickLoginSetupDialog(),
      );
      if (pin != null) {
        await service.enable(
          pin,
          displayName: ref.read(authStateProvider).customer?.displayName,
        );
      }
    }
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final customer = ref.watch(authStateProvider).customer;
    final name = customer?.displayName ?? context.l10n.profile;

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: BrandedPageBackground(
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 120),
            children: [
              Text(
                context.l10n.profile,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: AlignmentDirectional.topStart,
                    end: AlignmentDirectional.bottomEnd,
                    colors: [Color(0xFF087F6E), Color(0xFF123548)],
                  ),
                  borderRadius: BorderRadius.circular(26),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x3315C795),
                      blurRadius: 26,
                      offset: Offset(0, 12),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Container(
                      width: 68,
                      height: 68,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.16),
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.22),
                        ),
                      ),
                      child: Text(
                        name.isEmpty ? 'P' : name.characters.first,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 26,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            name,
                            style: Theme.of(context).textTheme.titleLarge
                                ?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w800,
                                ),
                          ),
                          if (customer != null) ...[
                            const SizedBox(height: 4),
                            Text(
                              customer.email,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(color: Color(0xFFD4F5EB)),
                            ),
                          ],
                        ],
                      ),
                    ),
                    const Icon(
                      Icons.verified_rounded,
                      color: Color(0xFFBFF3DF),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              _ProfileAction(
                icon: Icons.directions_car_outlined,
                title: context.l10n.vehicles,
                subtitle: 'إدارة المركبات المرتبطة بحسابك',
                onTap: () => context.push(AppRoutes.vehicles),
              ),
              const SizedBox(height: 12),
              FutureBuilder<bool>(
                future: ref.read(quickLoginServiceProvider).isEnabled(),
                builder: (context, snapshot) => _ProfileAction(
                  icon: Icons.pin_outlined,
                  title: 'الدخول السريع',
                  subtitle: snapshot.data == true
                      ? 'مفعّل على هذا الجهاز — اضغط للإيقاف أو التغيير'
                      : 'أنشئ رمزًا من 4 أو 6 أرقام لفتح التطبيق بسرعة',
                  onTap: _configureQuickLogin,
                ),
              ),
              const SizedBox(height: 12),
              _ProfileAction(
                icon: Icons.settings_outlined,
                title: context.l10n.settings,
                subtitle: 'اللغة والمظهر وتفضيلات التطبيق',
                onTap: () => context.push(AppRoutes.settings),
              ),
              const SizedBox(height: 12),
              _ProfileAction(
                icon: Icons.logout_rounded,
                title: context.l10n.logout,
                subtitle: 'إنهاء الجلسة الحالية بأمان',
                isDestructive: true,
                onTap: () => ref.read(authStateProvider.notifier).logout(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickLoginSetupDialog extends StatefulWidget {
  const _QuickLoginSetupDialog();

  @override
  State<_QuickLoginSetupDialog> createState() => _QuickLoginSetupDialogState();
}

class _QuickLoginSetupDialogState extends State<_QuickLoginSetupDialog> {
  final pin = TextEditingController();
  final confirmation = TextEditingController();
  int length = 4;
  String? error;

  @override
  void dispose() {
    pin.dispose();
    confirmation.dispose();
    super.dispose();
  }

  void save() {
    final valid = RegExp('^\\d{$length}\$').hasMatch(pin.text);
    if (!valid || pin.text != confirmation.text) {
      setState(() => error = 'أدخل $length أرقام متطابقة.');
      return;
    }
    Navigator.pop(context, pin.text);
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('إعداد الدخول السريع'),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SegmentedButton<int>(
          segments: const [
            ButtonSegment(value: 4, label: Text('4 أرقام')),
            ButtonSegment(value: 6, label: Text('6 أرقام')),
          ],
          selected: {length},
          onSelectionChanged: (value) => setState(() {
            length = value.single;
            pin.clear();
            confirmation.clear();
            error = null;
          }),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: pin,
          obscureText: true,
          maxLength: length,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'الرمز'),
        ),
        TextField(
          controller: confirmation,
          obscureText: true,
          maxLength: length,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'تأكيد الرمز'),
        ),
        if (error != null)
          Text(
            error!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
      ],
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('إلغاء'),
      ),
      FilledButton(onPressed: save, child: const Text('حفظ')),
    ],
  );
}

class _ProfileAction extends StatelessWidget {
  const _ProfileAction({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.isDestructive = false,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final bool isDestructive;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final accent = isDestructive ? colors.error : colors.primary;
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: colors.outlineVariant.withValues(alpha: 0.55)),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.11),
                  borderRadius: BorderRadius.circular(15),
                ),
                child: Icon(icon, color: accent),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: colors.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: colors.outline),
            ],
          ),
        ),
      ),
    );
  }
}
