import 'package:flutter/material.dart';

class BrandedAppBarBackground extends StatelessWidget {
  const BrandedAppBarBackground({this.radius = 18, super.key});

  final double radius;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        color: isDark
            ? const Color(0xFF0B202B).withValues(alpha: 0.97)
            : Colors.white.withValues(alpha: 0.97),
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(radius)),
        border: Border(
          bottom: BorderSide(
            color: isDark ? const Color(0xFF1D3945) : const Color(0xFFDDEBE7),
          ),
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(
              0xFF062F2A,
            ).withValues(alpha: isDark ? 0.26 : 0.10),
            blurRadius: 18,
            offset: const Offset(0, 6),
          ),
        ],
      ),
    );
  }
}
