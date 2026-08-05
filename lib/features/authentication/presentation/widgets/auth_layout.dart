import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/app/localization/locale_controller.dart';
import 'package:nnexoris_customer/app/theme/theme_controller.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';

class AuthLayout extends ConsumerWidget {
  const AuthLayout({
    required this.title,
    required this.subtitle,
    required this.child,
    required this.footer,
    super.key,
    this.showBackButton = false,
    this.onBack,
    this.formWidthFactor = 1,
    this.backgroundGlowOffset = 0,
    this.logoSize = 104,
    this.contentTopSpacing = 52,
  });

  final String title;
  final String subtitle;
  final Widget child;
  final Widget footer;
  final bool showBackButton;
  final VoidCallback? onBack;
  final double formWidthFactor;
  final double backgroundGlowOffset;
  final double logoSize;
  final double contentTopSpacing;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final locale = Localizations.localeOf(context);

    return Scaffold(
      body: AnimatedContainer(
        duration: const Duration(milliseconds: 450),
        curve: Curves.easeOutCubic,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: AlignmentDirectional.topStart,
            end: AlignmentDirectional.bottomEnd,
            colors: isDark
                ? const [
                    Color(0xFF061722),
                    Color(0xFF0B2B32),
                    Color(0xFF07131D),
                  ]
                : const [
                    Color(0xFFF9FCFB),
                    Color(0xFFE8F7F2),
                    Color(0xFFF1F8FC),
                  ],
          ),
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: _AnimatedGlowLayer(verticalOffset: backgroundGlowOffset),
            ),
            SafeArea(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 30),
                child: Align(
                  alignment: Alignment.topCenter,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 460),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SizedBox(
                          height: 38,
                          child: Stack(
                            children: [
                              Align(
                                alignment: AlignmentDirectional.centerStart,
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    _PreferenceAction(
                                      label: locale.languageCode == 'ar'
                                          ? 'English'
                                          : 'عربي',
                                      onPressed: () => ref
                                          .read(localeProvider.notifier)
                                          .setLocale(
                                            Locale(
                                              locale.languageCode == 'ar'
                                                  ? 'en'
                                                  : 'ar',
                                            ),
                                          ),
                                    ),
                                    const SizedBox(width: 6),
                                    _RoundAction(
                                      tooltip: isDark
                                          ? context.l10n.lightTheme
                                          : context.l10n.darkTheme,
                                      icon: isDark
                                          ? Icons.light_mode_rounded
                                          : Icons.dark_mode_rounded,
                                      onPressed: () => ref
                                          .read(themeModeProvider.notifier)
                                          .setThemeMode(
                                            isDark
                                                ? ThemeMode.light
                                                : ThemeMode.dark,
                                          ),
                                    ),
                                  ],
                                ),
                              ),
                              if (showBackButton)
                                Align(
                                  alignment: AlignmentDirectional.centerEnd,
                                  child: _RoundAction(
                                    tooltip: MaterialLocalizations.of(
                                      context,
                                    ).backButtonTooltip,
                                    icon: Icons.arrow_back_rounded,
                                    onPressed: onBack,
                                  ),
                                ),
                            ],
                          ),
                        ),
                        SizedBox(height: contentTopSpacing),
                        Center(
                          child: Container(
                            width: logoSize,
                            height: logoSize,
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: isDark
                                  ? Colors.white.withValues(alpha: 0.08)
                                  : Colors.white.withValues(alpha: 0.88),
                              borderRadius: BorderRadius.circular(24),
                              border: Border.all(
                                color: Colors.white.withValues(
                                  alpha: isDark ? 0.10 : 0.80,
                                ),
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(
                                    0xFF087F6E,
                                  ).withValues(alpha: 0.14),
                                  blurRadius: 28,
                                  offset: const Offset(0, 12),
                                ),
                              ],
                            ),
                            child: Image.asset(
                              'assets/branding/logo.png',
                              fit: BoxFit.contain,
                            ),
                          ),
                        ),
                        const SizedBox(height: 18),
                        Text(
                          title,
                          textAlign: TextAlign.center,
                          style: theme.textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                            letterSpacing: -0.5,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          subtitle,
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                            height: 1.45,
                          ),
                        ),
                        const SizedBox(height: 26),
                        Center(
                          child: FractionallySizedBox(
                            widthFactor: formWidthFactor,
                            child: Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: isDark
                                    ? const Color(
                                        0xFF0D222D,
                                      ).withValues(alpha: 0.94)
                                    : Colors.white.withValues(alpha: 0.94),
                                borderRadius: BorderRadius.circular(26),
                                border: Border.all(
                                  color: isDark
                                      ? const Color(0xFF203A46)
                                      : Colors.white,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: const Color(
                                      0xFF123D45,
                                    ).withValues(alpha: isDark ? 0.28 : 0.10),
                                    blurRadius: 38,
                                    offset: const Offset(0, 18),
                                  ),
                                ],
                              ),
                              child: child,
                            ),
                          ),
                        ),
                        const SizedBox(height: 18),
                        footer,
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class AuthTextField extends StatelessWidget {
  const AuthTextField({
    required this.controller,
    required this.label,
    required this.icon,
    super.key,
    this.keyboardType,
    this.validator,
    this.obscureText = false,
    this.onToggleVisibility,
    this.autofillHints,
    this.textInputAction,
    this.prefix,
  });

  final TextEditingController controller;
  final String label;
  final IconData icon;
  final TextInputType? keyboardType;
  final String? Function(String?)? validator;
  final bool obscureText;
  final VoidCallback? onToggleVisibility;
  final Iterable<String>? autofillHints;
  final TextInputAction? textInputAction;
  final Widget? prefix;

  @override
  Widget build(BuildContext context) => TextFormField(
    controller: controller,
    keyboardType: keyboardType,
    validator: validator,
    obscureText: obscureText,
    autofillHints: autofillHints,
    textInputAction: textInputAction,
    decoration: InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon),
      prefix: prefix,
      suffixIcon: onToggleVisibility == null
          ? null
          : IconButton(
              tooltip: obscureText
                  ? context.l10n.showPassword
                  : context.l10n.hidePassword,
              onPressed: onToggleVisibility,
              icon: Icon(
                obscureText
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined,
              ),
            ),
    ),
  );
}

class AuthPrimaryButton extends StatelessWidget {
  const AuthPrimaryButton({
    required this.label,
    required this.loading,
    required this.onPressed,
    super.key,
    this.height = 56,
  });

  final String label;
  final bool loading;
  final VoidCallback? onPressed;
  final double height;

  @override
  Widget build(BuildContext context) => SizedBox(
    height: height,
    child: FilledButton(
      onPressed: loading ? null : onPressed,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 200),
        child: loading
            ? const SizedBox(
                key: ValueKey('loading'),
                width: 22,
                height: 22,
                child: CircularProgressIndicator(strokeWidth: 2.4),
              )
            : Text(key: const ValueKey('label'), label),
      ),
    ),
  );
}

class _PreferenceAction extends StatelessWidget {
  const _PreferenceAction({required this.label, required this.onPressed});

  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => OutlinedButton(
    onPressed: onPressed,
    style: OutlinedButton.styleFrom(
      minimumSize: const Size(0, 36),
      padding: const EdgeInsets.symmetric(horizontal: 11),
      backgroundColor: Theme.of(context).inputDecorationTheme.fillColor,
      side: BorderSide(
        color: Theme.of(
          context,
        ).colorScheme.outlineVariant.withValues(alpha: 0.65),
      ),
    ),
    child: Text(
      label,
      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
    ),
  );
}

class _RoundAction extends StatelessWidget {
  const _RoundAction({
    required this.tooltip,
    required this.icon,
    required this.onPressed,
  });

  final String tooltip;
  final IconData icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => IconButton.outlined(
    tooltip: tooltip,
    onPressed: onPressed,
    icon: Icon(icon, size: 18),
    style: IconButton.styleFrom(
      minimumSize: const Size.square(36),
      maximumSize: const Size.square(36),
      padding: EdgeInsets.zero,
      backgroundColor: Theme.of(context).inputDecorationTheme.fillColor,
      side: BorderSide(
        color: Theme.of(
          context,
        ).colorScheme.outlineVariant.withValues(alpha: 0.65),
      ),
    ),
  );
}

class _GlowOrb extends StatelessWidget {
  const _GlowOrb({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) => IgnorePointer(
    child: Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(
          colors: [
            color.withValues(
              alpha: Theme.of(context).brightness == Brightness.dark
                  ? 0.18
                  : 0.22,
            ),
            color.withValues(alpha: 0),
          ],
        ),
      ),
    ),
  );
}

class _AnimatedGlowLayer extends StatefulWidget {
  const _AnimatedGlowLayer({required this.verticalOffset});

  final double verticalOffset;

  @override
  State<_AnimatedGlowLayer> createState() => _AnimatedGlowLayerState();
}

class _AnimatedGlowLayerState extends State<_AnimatedGlowLayer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _progress;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1700),
    );
    _progress = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    );
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => IgnorePointer(
    child: AnimatedBuilder(
      animation: _progress,
      builder: (context, child) {
        final progress = _progress.value;
        return Opacity(
          opacity: progress,
          child: Transform.translate(
            offset: Offset(0, widget.verticalOffset + (190 * (1 - progress))),
            child: Transform.scale(
              scale: 0.82 + (0.18 * progress),
              child: child,
            ),
          ),
        );
      },
      child: Stack(
        children: [
          const Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  stops: [0.52, 1],
                  colors: [Color(0x0020C997), Color(0x1820C997)],
                ),
              ),
            ),
          ),
          PositionedDirectional(
            top: 105,
            end: -32,
            child: _GlowOrb(size: 280, color: Color(0xFF20C997)),
          ),
          PositionedDirectional(
            top: 390,
            start: -70,
            child: _GlowOrb(size: 320, color: Color(0xFF5DADE2)),
          ),
          PositionedDirectional(
            bottom: -widget.verticalOffset - 20,
            end: -45,
            child: _GlowOrb(size: 330, color: Color(0xFF7BDFAE)),
          ),
        ],
      ),
    ),
  );
}
