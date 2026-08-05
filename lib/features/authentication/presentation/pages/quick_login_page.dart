import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/app/localization/locale_controller.dart';
import 'package:nnexoris_customer/app/theme/theme_controller.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/core/security/quick_login_service.dart';
import 'package:nnexoris_customer/features/authentication/presentation/auth_controller.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';

String _quickText(BuildContext context, String ar, String en) =>
    Localizations.localeOf(context).languageCode == 'ar' ? ar : en;

const _brandGreen = Color(0xFF087F6E);
const _brandMint = Color(0xFF20C997);
const _brandNavy = Color(0xFF123548);

class QuickLoginPage extends ConsumerStatefulWidget {
  const QuickLoginPage({super.key});

  @override
  ConsumerState<QuickLoginPage> createState() => _QuickLoginPageState();
}

class _QuickLoginPageState extends ConsumerState<QuickLoginPage> {
  int length = 4;
  String pin = '';
  String? customerName;
  bool busy = false;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadQuickLoginIdentity();
  }

  Future<void> _loadQuickLoginIdentity() async {
    final quickLogin = ref.read(quickLoginServiceProvider);
    final configuredLength = await quickLogin.pinLength();
    var name = (await quickLogin.displayName())?.trim();

    if (name == null || name.isEmpty) {
      final token = await ref.read(tokenManagerProvider).accessToken();
      name = _nameFromAccessToken(token);
    }

    if (name == null || name.isEmpty) {
      try {
        name = (await ref.read(authRepositoryProvider).getCurrentUser())
            .displayName
            .trim();
      } on Object {
        // The PIN screen remains usable offline. The verified account name is
        // cached on the next successful session restoration.
      }
    }

    if (name?.isNotEmpty == true) {
      await quickLogin.updateDisplayName(name!);
    }
    if (!mounted) return;
    setState(() {
      if (configuredLength != null) length = configuredLength;
      customerName = name?.isNotEmpty == true ? name : null;
    });
  }

  String? _nameFromAccessToken(String? token) {
    if (token == null) return null;
    try {
      final parts = token.split('.');
      if (parts.length != 3) return null;
      final payload = Map<String, dynamic>.from(
        jsonDecode(utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))))
            as Map,
      );
      for (final key in const [
        'displayName',
        'display_name',
        'full_name',
        'name',
      ]) {
        final value = payload[key]?.toString().trim();
        if (value?.isNotEmpty == true) return value;
      }
    } on Object {
      return null;
    }
    return null;
  }

  void _digit(String value) {
    if (busy || pin.length >= length) return;
    setState(() {
      pin += value;
      error = null;
    });
    if (pin.length == length) submit();
  }

  void _backspace() {
    if (busy || pin.isEmpty) return;
    setState(() {
      pin = pin.substring(0, pin.length - 1);
      error = null;
    });
  }

  Future<void> _useAccountLogin() async {
    if (busy) return;
    await ref.read(quickLoginServiceProvider).disable();
    await ref.read(tokenManagerProvider).clear();
    await ref.read(authStateProvider.notifier).restoreSession();
  }

  Future<void> submit() async {
    if (pin.length != length || busy) return;
    final submittedPin = pin;
    setState(() {
      busy = true;
      error = null;
    });
    final result = await ref
        .read(authStateProvider.notifier)
        .unlockWithPin(submittedPin);
    if (!mounted) return;
    setState(() {
      busy = false;
      pin = '';
      error = switch (result) {
        QuickLoginResult.invalidPin => _quickText(
          context,
          'رمز الدخول السريع غير صحيح.',
          'The quick-login PIN is incorrect.',
        ),
        QuickLoginResult.temporarilyLocked => _quickText(
          context,
          'محاولات كثيرة. حاول مرة أخرى بعد دقيقة.',
          'Too many attempts. Try again in one minute.',
        ),
        QuickLoginResult.notConfigured => _quickText(
          context,
          'الدخول السريع غير مُعد على هذا الجهاز.',
          'Quick login is not configured on this device.',
        ),
        QuickLoginResult.success => null,
      };
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final screenHeight = MediaQuery.sizeOf(context).height;
    final compact = screenHeight < 730;

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: BrandedPageBackground(
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) => SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: EdgeInsets.fromLTRB(22, 12, 22, compact ? 16 : 24),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight - (compact ? 28 : 36),
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 430),
                    child: TweenAnimationBuilder<double>(
                      duration: const Duration(milliseconds: 720),
                      curve: Curves.easeOutCubic,
                      tween: Tween(begin: 0, end: 1),
                      builder: (context, value, child) => Opacity(
                        opacity: value,
                        child: Transform.translate(
                          offset: Offset(0, 22 * (1 - value)),
                          child: child,
                        ),
                      ),
                      child: Column(
                        children: [
                          _TopActions(isDark: isDark),
                          SizedBox(height: compact ? 20 : 34),
                          _BrandMark(isDark: isDark),
                          SizedBox(height: compact ? 14 : 20),
                          Text(
                            _quickText(context, 'أهلًا بعودتك', 'Welcome back'),
                            style: theme.textTheme.titleMedium?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 5),
                          AnimatedSize(
                            duration: const Duration(milliseconds: 220),
                            child: customerName == null
                                ? const SizedBox.shrink()
                                : Padding(
                                    padding: const EdgeInsets.only(top: 5),
                                    child: Text(
                                      customerName!,
                                      textAlign: TextAlign.center,
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                      style: theme.textTheme.headlineMedium
                                          ?.copyWith(
                                            color: isDark
                                                ? Colors.white
                                                : _brandNavy,
                                            fontWeight: FontWeight.w900,
                                            letterSpacing: -0.25,
                                          ),
                                    ),
                                  ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _quickText(
                              context,
                              'أدخل رمز الدخول المكوّن من $length أرقام',
                              'Enter your $length-digit access PIN',
                            ),
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                          SizedBox(height: compact ? 22 : 32),
                          AnimatedSwitcher(
                            duration: const Duration(milliseconds: 180),
                            child: _PinDots(
                              key: ValueKey('$length-${pin.length}'),
                              length: length,
                              entered: pin.length,
                              hasError: error != null,
                            ),
                          ),
                          SizedBox(height: error == null ? 10 : 6),
                          AnimatedSize(
                            duration: const Duration(milliseconds: 180),
                            child: error == null
                                ? const SizedBox(height: 18)
                                : Text(
                                    error!,
                                    textAlign: TextAlign.center,
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      color: theme.colorScheme.error,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                          ),
                          TextButton(
                            onPressed: busy ? null : _useAccountLogin,
                            style: TextButton.styleFrom(
                              foregroundColor: isDark
                                  ? const Color(0xFF69E0BD)
                                  : _brandGreen,
                            ),
                            child: Text(
                              _quickText(
                                context,
                                'نسيت رمز الدخول السريع؟',
                                'Forgot your quick-login PIN?',
                              ),
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                          SizedBox(height: compact ? 10 : 18),
                          _NumberPad(
                            enabled: !busy,
                            compact: compact,
                            onDigit: _digit,
                            onBackspace: _backspace,
                          ),
                          const SizedBox(height: 12),
                          AnimatedSwitcher(
                            duration: const Duration(milliseconds: 180),
                            child: busy
                                ? const SizedBox(
                                    key: ValueKey('loading'),
                                    width: 22,
                                    height: 22,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.4,
                                      color: _brandMint,
                                    ),
                                  )
                                : Row(
                                    key: const ValueKey('secure'),
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Icon(
                                        Icons.lock_outline_rounded,
                                        size: 14,
                                        color: theme
                                            .colorScheme
                                            .onSurfaceVariant
                                            .withValues(alpha: 0.72),
                                      ),
                                      const SizedBox(width: 6),
                                      Text(
                                        _quickText(
                                          context,
                                          'دخول آمن ومشفّر',
                                          'Secure encrypted access',
                                        ),
                                        style: theme.textTheme.labelMedium
                                            ?.copyWith(
                                              color: theme
                                                  .colorScheme
                                                  .onSurfaceVariant,
                                            ),
                                      ),
                                    ],
                                  ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _TopActions extends ConsumerWidget {
  const _TopActions({required this.isDark});

  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = Localizations.localeOf(context);
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _HeaderButton(
          label: locale.languageCode == 'ar' ? 'EN' : 'عربي',
          onPressed: () => ref
              .read(localeProvider.notifier)
              .setLocale(Locale(locale.languageCode == 'ar' ? 'en' : 'ar')),
        ),
        _HeaderButton(
          icon: isDark ? Icons.light_mode_rounded : Icons.dark_mode_outlined,
          tooltip: isDark ? 'Light mode' : 'Dark mode',
          onPressed: () => ref
              .read(themeModeProvider.notifier)
              .setThemeMode(isDark ? ThemeMode.light : ThemeMode.dark),
        ),
      ],
    );
  }
}

class _HeaderButton extends StatelessWidget {
  const _HeaderButton({
    this.label,
    this.icon,
    this.tooltip,
    required this.onPressed,
  });

  final String? label;
  final IconData? icon;
  final String? tooltip;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Material(
      color: isDark
          ? const Color(0xFF102B35).withValues(alpha: 0.92)
          : Colors.white.withValues(alpha: 0.86),
      borderRadius: BorderRadius.circular(15),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(15),
        child: Tooltip(
          message: tooltip ?? '',
          child: Container(
            constraints: const BoxConstraints(minWidth: 42, minHeight: 42),
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(15),
              border: Border.all(
                color: _brandMint.withValues(alpha: isDark ? 0.22 : 0.16),
              ),
            ),
            child: icon != null
                ? Icon(icon, size: 20, color: isDark ? _brandMint : _brandGreen)
                : Text(
                    label!,
                    style: TextStyle(
                      color: isDark ? _brandMint : _brandGreen,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
          ),
        ),
      ),
    );
  }
}

class _BrandMark extends StatelessWidget {
  const _BrandMark({required this.isDark});

  final bool isDark;

  @override
  Widget build(BuildContext context) => Container(
    width: 82,
    height: 82,
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: isDark
          ? const Color(0xFF102B35).withValues(alpha: 0.92)
          : Colors.white.withValues(alpha: 0.92),
      borderRadius: BorderRadius.circular(25),
      border: Border.all(color: _brandMint.withValues(alpha: 0.20)),
      boxShadow: [
        BoxShadow(
          color: _brandGreen.withValues(alpha: isDark ? 0.18 : 0.12),
          blurRadius: 30,
          offset: const Offset(0, 12),
        ),
      ],
    ),
    child: Image.asset('assets/branding/logo.png', fit: BoxFit.contain),
  );
}

class _PinDots extends StatelessWidget {
  const _PinDots({
    required this.length,
    required this.entered,
    required this.hasError,
    super.key,
  });

  final int length;
  final int entered;
  final bool hasError;

  @override
  Widget build(BuildContext context) => Row(
    mainAxisAlignment: MainAxisAlignment.center,
    children: List.generate(length, (index) {
      final filled = index < entered;
      final color = hasError
          ? Theme.of(context).colorScheme.error
          : _brandGreen;
      return AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
        width: filled ? 18 : 14,
        height: filled ? 18 : 14,
        margin: EdgeInsets.symmetric(horizontal: length == 6 ? 9 : 13),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: filled ? color : color.withValues(alpha: 0.13),
          border: Border.all(color: color.withValues(alpha: 0.68), width: 1.5),
          boxShadow: filled
              ? [BoxShadow(color: color.withValues(alpha: 0.24), blurRadius: 9)]
              : null,
        ),
      );
    }),
  );
}

class _NumberPad extends StatelessWidget {
  const _NumberPad({
    required this.enabled,
    required this.compact,
    required this.onDigit,
    required this.onBackspace,
  });

  final bool enabled;
  final bool compact;
  final ValueChanged<String> onDigit;
  final VoidCallback onBackspace;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', 'back'];

    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 10 : 14,
        vertical: compact ? 8 : 12,
      ),
      decoration: BoxDecoration(
        color: isDark
            ? const Color(0xFF0C252F).withValues(alpha: 0.52)
            : Colors.white.withValues(alpha: 0.42),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: _brandMint.withValues(alpha: 0.10)),
      ),
      child: Directionality(
        textDirection: TextDirection.ltr,
        child: GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            mainAxisExtent: compact ? 54 : 62,
            crossAxisSpacing: compact ? 18 : 24,
            mainAxisSpacing: compact ? 5 : 8,
          ),
          itemCount: keys.length,
          itemBuilder: (context, index) {
            final key = keys[index];
            if (key.isEmpty) return const SizedBox.shrink();
            final isBackspace = key == 'back';
            return Center(
              child: Material(
                color: Colors.transparent,
                shape: const CircleBorder(),
                child: InkWell(
                  onTap: !enabled
                      ? null
                      : isBackspace
                      ? onBackspace
                      : () => onDigit(key),
                  customBorder: const CircleBorder(),
                  child: AnimatedOpacity(
                    duration: const Duration(milliseconds: 150),
                    opacity: enabled ? 1 : 0.45,
                    child: SizedBox.square(
                      dimension: compact ? 50 : 56,
                      child: Center(
                        child: isBackspace
                            ? Icon(
                                Icons.backspace_outlined,
                                size: 24,
                                color: isDark
                                    ? const Color(0xFFB7CAC6)
                                    : _brandNavy.withValues(alpha: 0.72),
                              )
                            : Text(
                                key,
                                style: theme.textTheme.headlineSmall?.copyWith(
                                  color: isDark ? Colors.white : _brandNavy,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
