import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/network/network_info.dart';
import 'package:nnexoris_customer/core/providers.dart';

class MobileNavigationShell extends ConsumerWidget {
  const MobileNavigationShell({required this.navigationShell, super.key});

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final network = ref.watch(networkConnectionStateProvider).asData?.value;

    return Scaffold(
      extendBody: true,
      body: Column(
        children: [
          if (network == NetworkConnectionState.offline)
            MaterialBanner(
              leading: const Icon(Icons.cloud_off_outlined),
              content: Text(context.l10n.offlineNotice),
              actions: const [SizedBox.shrink()],
            ),
          Expanded(child: navigationShell),
        ],
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        minimum: const EdgeInsets.fromLTRB(18, 0, 18, 8),
        child: Container(
          decoration: BoxDecoration(
            color: isDark
                ? const Color(0xFF0B202B).withValues(alpha: 0.97)
                : Colors.white.withValues(alpha: 0.97),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(
              color: isDark ? const Color(0xFF1D3945) : const Color(0xFFDDEBE7),
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(
                  0xFF062F2A,
                ).withValues(alpha: isDark ? 0.32 : 0.14),
                blurRadius: 24,
                offset: const Offset(0, 9),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(21),
            child: NavigationBarTheme(
              data: NavigationBarThemeData(
                indicatorColor: theme.colorScheme.primary.withValues(
                  alpha: 0.14,
                ),
                indicatorShape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                iconTheme: WidgetStateProperty.resolveWith((states) {
                  final selected = states.contains(WidgetState.selected);
                  return IconThemeData(
                    size: selected ? 23 : 21,
                    color: selected
                        ? theme.colorScheme.primary
                        : theme.colorScheme.onSurfaceVariant,
                  );
                }),
                labelTextStyle: WidgetStateProperty.resolveWith((states) {
                  final selected = states.contains(WidgetState.selected);
                  return TextStyle(
                    fontSize: selected ? 11.5 : 10.5,
                    fontWeight: selected ? FontWeight.w800 : FontWeight.w600,
                    color: selected
                        ? theme.colorScheme.primary
                        : theme.colorScheme.onSurfaceVariant,
                  );
                }),
              ),
              child: NavigationBar(
                height: 66,
                backgroundColor: Colors.transparent,
                selectedIndex: navigationShell.currentIndex,
                labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
                onDestinationSelected: (index) => navigationShell.goBranch(
                  index,
                  initialLocation: index == navigationShell.currentIndex,
                ),
                destinations: [
                  NavigationDestination(
                    icon: const Icon(Icons.home_outlined),
                    selectedIcon: const Icon(Icons.home_rounded),
                    label: context.l10n.home,
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.local_gas_station_outlined),
                    selectedIcon: const Icon(Icons.local_gas_station_rounded),
                    label: context.l10n.stations,
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.account_balance_wallet_outlined),
                    selectedIcon: const Icon(
                      Icons.account_balance_wallet_rounded,
                    ),
                    label: context.l10n.wallet,
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.person_outline_rounded),
                    selectedIcon: const Icon(Icons.person_rounded),
                    label: context.l10n.profile,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
