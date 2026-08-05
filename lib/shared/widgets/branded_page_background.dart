import 'package:flutter/material.dart';

class BrandedPageBackground extends StatelessWidget {
  const BrandedPageBackground({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: isDark
              ? const [Color(0xFF071823), Color(0xFF091E28), Color(0xFF07131D)]
              : const [Color(0xFFF8FCFB), Color(0xFFF0F8F5), Color(0xFFF5F9FC)],
        ),
      ),
      child: Stack(
        children: [
          PositionedDirectional(
            top: -100,
            end: -100,
            child: _AmbientCircle(
              size: 280,
              color: const Color(
                0xFF20C997,
              ).withValues(alpha: isDark ? 0.10 : 0.12),
            ),
          ),
          PositionedDirectional(
            top: 330,
            start: -160,
            child: _AmbientCircle(
              size: 340,
              color: const Color(
                0xFF5DADE2,
              ).withValues(alpha: isDark ? 0.07 : 0.08),
            ),
          ),
          Positioned.fill(child: child),
        ],
      ),
    );
  }
}

class _AmbientCircle extends StatelessWidget {
  const _AmbientCircle({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) => IgnorePointer(
    child: Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(colors: [color, color.withValues(alpha: 0)]),
      ),
    ),
  );
}
