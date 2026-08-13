import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// Saudi Riyal sign with broad Android/iOS font support.
/// U+20C1 is missing from many device fonts and renders as a square.
const String saudiRiyalSymbol = '\uFDFC';

String formatSaudiRiyal(num amount, {int fractionDigits = 2}) =>
    '${amount.toStringAsFixed(fractionDigits)} $saudiRiyalSymbol';

class SaudiRiyalMark extends StatelessWidget {
  const SaudiRiyalMark({super.key, this.size = 17, this.color});

  final double size;
  final Color? color;

  @override
  Widget build(BuildContext context) => SvgPicture.asset(
        'assets/branding/saudi_riyal_symbol.svg',
        width: size,
        height: size,
        fit: BoxFit.contain,
        colorFilter: color == null
            ? null
            : ColorFilter.mode(color!, BlendMode.srcIn),
      );
}

class SaudiRiyalAmount extends StatelessWidget {
  const SaudiRiyalAmount(this.amount, {super.key, this.style, this.markSize});

  final num amount;
  final TextStyle? style;
  final double? markSize;

  @override
  Widget build(BuildContext context) {
    final effectiveColor = style?.color ??
        DefaultTextStyle.of(context).style.color ??
        Theme.of(context).colorScheme.onSurface;
    return Row(
      mainAxisSize: MainAxisSize.min,
      textDirection: TextDirection.ltr,
      children: [
        Text(amount.toStringAsFixed(2), style: style),
        const SizedBox(width: 4),
        SaudiRiyalMark(size: markSize ?? (style?.fontSize ?? 16), color: effectiveColor),
      ],
    );
  }
}
