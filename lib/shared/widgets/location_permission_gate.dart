import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/stations/domain/repositories/station_repository.dart';

class LocationPermissionGate extends ConsumerStatefulWidget {
  const LocationPermissionGate({required this.child, super.key});

  final Widget child;

  @override
  ConsumerState<LocationPermissionGate> createState() =>
      _LocationPermissionGateState();
}

class _LocationPermissionGateState
    extends ConsumerState<LocationPermissionGate> {
  bool _checked = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_checked) return;
    _checked = true;
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkAccess());
  }

  Future<void> _checkAccess() async {
    final service = ref.read(locationServiceProvider);
    final status = await service.accessStatus();
    if (!mounted || status == LocationAccessStatus.granted) return;

    final accepted = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => AlertDialog(
        icon: Container(
          width: 58,
          height: 58,
          decoration: BoxDecoration(
            color: Theme.of(dialogContext).colorScheme.primaryContainer,
            shape: BoxShape.circle,
          ),
          child: Icon(
            Icons.near_me_rounded,
            color: Theme.of(dialogContext).colorScheme.primary,
          ),
        ),
        title: Text(
          dialogContext.l10n.locationPermissionTitle,
          textAlign: TextAlign.center,
        ),
        content: Text(
          status == LocationAccessStatus.serviceDisabled
              ? '${dialogContext.l10n.locationPermissionReason}\n\n'
                    '${dialogContext.l10n.locationSettingsReason}'
              : dialogContext.l10n.locationPermissionReason,
          textAlign: TextAlign.center,
        ),
        actionsAlignment: MainAxisAlignment.center,
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(dialogContext.l10n.notNow),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.pop(dialogContext, true),
            icon: Icon(
              status == LocationAccessStatus.denied
                  ? Icons.location_on_rounded
                  : Icons.settings_rounded,
            ),
            label: Text(
              status == LocationAccessStatus.denied
                  ? dialogContext.l10n.allowLocation
                  : dialogContext.l10n.openSettings,
            ),
          ),
        ],
      ),
    );
    if (accepted != true) return;

    switch (status) {
      case LocationAccessStatus.denied:
        await service.requestAccess();
      case LocationAccessStatus.deniedForever:
        await service.openAppSettings();
      case LocationAccessStatus.serviceDisabled:
        await service.openLocationSettings();
      case LocationAccessStatus.granted:
        break;
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
