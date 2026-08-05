import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> with TickerProviderStateMixin {
  late final AnimationController _entrance;
  late final AnimationController _ambient;

  @override
  void initState() {
    super.initState();
    _entrance = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1050),
    )..forward();
    _ambient = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2200),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _entrance.dispose();
    _ambient.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isArabic = Localizations.localeOf(context).languageCode == 'ar';
    return Scaffold(
      backgroundColor: const Color(0xFF061B25),
      body: Semantics(
        label: context.l10n.loading,
        child: Stack(
          fit: StackFit.expand,
          children: [
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Color(0xFF061722),
                    Color(0xFF073B38),
                    Color(0xFF092735),
                    Color(0xFF06131D),
                  ],
                  stops: [0, 0.38, 0.72, 1],
                ),
              ),
            ),
            AnimatedBuilder(
              animation: _ambient,
              builder: (context, child) {
                final movement = _ambient.value;
                return Stack(
                  children: [
                    Positioned(
                      top: -120 + (movement * 34),
                      right: -95 + (movement * 18),
                      child: const _SplashGlow(
                        size: 330,
                        color: Color(0xFF20C997),
                        opacity: 0.22,
                      ),
                    ),
                    Positioned(
                      bottom: -155 + (movement * 42),
                      left: -130 + (movement * 20),
                      child: const _SplashGlow(
                        size: 390,
                        color: Color(0xFF4E8F2A),
                        opacity: 0.20,
                      ),
                    ),
                    Positioned(
                      top: 250 - (movement * 22),
                      left: -175,
                      child: const _SplashGlow(
                        size: 300,
                        color: Color(0xFF0B7D68),
                        opacity: 0.14,
                      ),
                    ),
                  ],
                );
              },
            ),
            Center(
              child: AnimatedBuilder(
                animation: _entrance,
                builder: (context, child) {
                  final curved = Curves.easeOutBack.transform(_entrance.value);
                  return Opacity(
                    opacity: _entrance.value.clamp(0, 1),
                    child: Transform.translate(
                      offset: Offset(0, 30 * (1 - _entrance.value)),
                      child: Transform.scale(
                        scale: 0.76 + (0.24 * curved),
                        child: child,
                      ),
                    ),
                  );
                },
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    AnimatedBuilder(
                      animation: _ambient,
                      builder: (context, child) => Container(
                        width: 152,
                        height: 152,
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          color: const Color(
                            0xFF0A2830,
                          ).withValues(alpha: 0.82),
                          borderRadius: BorderRadius.circular(42),
                          border: Border.all(
                            color: const Color(
                              0xFF40D7A9,
                            ).withValues(alpha: 0.24 + (_ambient.value * 0.18)),
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFF20C997).withValues(
                                alpha: 0.18 + (_ambient.value * 0.12),
                              ),
                              blurRadius: 38 + (_ambient.value * 18),
                              spreadRadius: 1 + (_ambient.value * 4),
                            ),
                            const BoxShadow(
                              color: Color(0x66000000),
                              blurRadius: 28,
                              offset: Offset(0, 18),
                            ),
                          ],
                        ),
                        child: child,
                      ),
                      child: Image.asset(
                        'assets/branding/logo.png',
                        fit: BoxFit.contain,
                      ),
                    ),
                    const SizedBox(height: 28),
                    const Text(
                      'PETRO B',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 4.2,
                      ),
                    ),
                    const SizedBox(height: 9),
                    Text(
                      isArabic
                          ? 'طاقة أذكى · تجربة أسرع'
                          : 'Smarter energy · Faster experience',
                      style: TextStyle(
                        color: const Color(0xFFC7E5DB).withValues(alpha: 0.88),
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        letterSpacing: isArabic ? 0 : 0.6,
                      ),
                    ),
                    const SizedBox(height: 42),
                    const _SplashLoadingIndicator(),
                  ],
                ),
              ),
            ),
            Positioned(
              left: 0,
              right: 0,
              bottom: 30,
              child: Text(
                isArabic ? 'آمن · سريع · متصل' : 'SECURE · FAST · CONNECTED',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.42),
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: isArabic ? 0.2 : 1.8,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SplashGlow extends StatelessWidget {
  const _SplashGlow({
    required this.size,
    required this.color,
    required this.opacity,
  });

  final double size;
  final Color color;
  final double opacity;

  @override
  Widget build(BuildContext context) => IgnorePointer(
    child: SizedBox.square(
      dimension: size,
      child: DecoratedBox(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [
              color.withValues(alpha: opacity),
              color.withValues(alpha: 0),
            ],
          ),
        ),
      ),
    ),
  );
}

class _SplashLoadingIndicator extends StatefulWidget {
  const _SplashLoadingIndicator();

  @override
  State<_SplashLoadingIndicator> createState() =>
      _SplashLoadingIndicatorState();
}

class _SplashLoadingIndicatorState extends State<_SplashLoadingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: _controller,
    builder: (context, _) => Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (index) {
        final distance = (_controller.value - (index * 0.22)).abs();
        final pulse = (1 - (distance.clamp(0, 0.5) * 2))
            .clamp(0.25, 1.0)
            .toDouble();
        return Container(
          width: 7,
          height: 7,
          margin: const EdgeInsets.symmetric(horizontal: 5),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: const Color(0xFF42DFAF).withValues(alpha: pulse),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF20C997).withValues(alpha: pulse * 0.45),
                blurRadius: 9,
              ),
            ],
          ),
        );
      }),
    ),
  );
}

class OnboardingPage extends StatelessWidget {
  const OnboardingPage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.local_gas_station, size: 72),
            const SizedBox(height: 24),
            Text(context.l10n.onboardingTitle),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => context.go(AppRoutes.login),
              child: Text(context.l10n.continueLabel),
            ),
          ],
        ),
      ),
    ),
  );
}

class VerifyEmailPage extends StatelessWidget {
  const VerifyEmailPage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(context.l10n.verifyEmail)),
    body: Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.mark_email_unread_outlined, size: 64),
            const SizedBox(height: 20),
            Text(context.l10n.verifyEmailHint, textAlign: TextAlign.center),
            const SizedBox(height: 20),
            const Text(
              'التحقق بالبريد لم يُفعّل على Customer API بعد. '
              'التعبئة الميدانية معطلة بغض النظر عن حالة البريد.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => context.go(AppRoutes.home),
              child: Text(context.l10n.continueLabel),
            ),
          ],
        ),
      ),
    ),
  );
}
