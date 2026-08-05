import 'package:flutter/material.dart';

class BrandedWalletCard extends StatelessWidget {
  const BrandedWalletCard({
    required this.available,
    required this.reserved,
    required this.onTopUp,
    super.key,
    this.updatedLabel,
  });

  final String available;
  final String reserved;
  final String? updatedLabel;
  final VoidCallback onTopUp;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(19),
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: AlignmentDirectional.topStart,
        end: AlignmentDirectional.bottomEnd,
        colors: [Color(0xFF098572), Color(0xFF0A5A54), Color(0xFF123548)],
      ),
      borderRadius: BorderRadius.circular(24),
      border: Border.all(color: Colors.white.withValues(alpha: 0.10)),
      boxShadow: const [
        BoxShadow(
          color: Color(0x3815C795),
          blurRadius: 26,
          offset: Offset(0, 12),
        ),
      ],
    ),
    child: Stack(
      children: [
        PositionedDirectional(
          end: -25,
          bottom: -42,
          child: Icon(
            Icons.account_balance_wallet_rounded,
            size: 150,
            color: Colors.white.withValues(alpha: 0.055),
          ),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.account_balance_wallet_outlined,
                    size: 19,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'محفظة PetroB',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.lock_outline_rounded,
                        size: 13,
                        color: Colors.white,
                      ),
                      SizedBox(width: 4),
                      Text(
                        'آمنة',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Text(
              'الرصيد المتاح',
              style: TextStyle(color: Color(0xFFCCEEE5), fontSize: 12),
            ),
            const SizedBox(height: 2),
            Text(
              available,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 30,
                height: 1.15,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'المحجوز $reserved',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Color(0xFFD4F5EB),
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (updatedLabel != null) ...[
                        const SizedBox(height: 3),
                        Text(
                          updatedLabel!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Colors.white60,
                            fontSize: 9,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                FilledButton.icon(
                  onPressed: onTopUp,
                  icon: const Icon(Icons.add_rounded, size: 17),
                  label: const Text('إضافة رصيد'),
                  style: FilledButton.styleFrom(
                    minimumSize: const Size(0, 42),
                    padding: const EdgeInsets.symmetric(horizontal: 13),
                    backgroundColor: Colors.white,
                    foregroundColor: const Color(0xFF076F61),
                    textStyle: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ],
    ),
  );
}
