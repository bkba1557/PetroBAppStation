import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/stations/domain/models/station.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';

class StationsPage extends ConsumerStatefulWidget {
  const StationsPage({super.key});

  @override
  ConsumerState<StationsPage> createState() => _StationsPageState();
}

class _StationsPageState extends ConsumerState<StationsPage> {
  late Future<List<Station>> _stationsFuture;
  DateTime? _lastUpdated;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _stationsFuture = _loadStations();
  }

  Future<List<Station>> _loadStations() async {
    final stations = await ref.read(stationRepositoryProvider).getStations();
    _lastUpdated = DateTime.now();
    return stations;
  }

  Future<void> _refresh() async {
    final next = _loadStations();
    setState(() => _stationsFuture = next);
    await next;
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: Colors.transparent,
    appBar: AppBar(
      title: Text(
        context.l10n.stations,
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
      backgroundColor: Colors.transparent,
    ),
    body: BrandedPageBackground(
      child: FutureBuilder<List<Station>>(
        future: _stationsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _RefreshMessage(
              icon: Icons.cloud_off_outlined,
              message: context.l10n.stationsLoadFailed,
              onRefresh: _refresh,
            );
          }
          final stations = snapshot.data ?? const <Station>[];
          if (stations.isEmpty) {
            return _RefreshMessage(
              icon: Icons.local_gas_station_outlined,
              message: context.l10n.noStations,
              onRefresh: _refresh,
            );
          }
          final query = _query.trim().toLowerCase();
          final filtered = query.isEmpty
              ? stations
              : stations
                    .where(
                      (station) =>
                          station.name.toLowerCase().contains(query) ||
                          station.location.address.toLowerCase().contains(
                            query,
                          ),
                    )
                    .toList(growable: false);
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 6, 18, 8),
                child: SearchBar(
                  elevation: const WidgetStatePropertyAll(0),
                  leading: const Icon(Icons.search_rounded, size: 21),
                  hintText: context.l10n.searchStations,
                  textStyle: const WidgetStatePropertyAll(
                    TextStyle(fontSize: 13),
                  ),
                  hintStyle: WidgetStatePropertyAll(
                    TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                  side: WidgetStatePropertyAll(
                    BorderSide(
                      color: Theme.of(
                        context,
                      ).colorScheme.outlineVariant.withValues(alpha: 0.65),
                    ),
                  ),
                  onChanged: (value) => setState(() => _query = value),
                ),
              ),
              if (_lastUpdated != null)
                Padding(
                  padding: const EdgeInsetsDirectional.only(
                    start: 22,
                    end: 22,
                    bottom: 8,
                  ),
                  child: Align(
                    alignment: AlignmentDirectional.centerEnd,
                    child: Text(
                      '${context.l10n.lastUpdated} ${DateFormat.Hm().format(_lastUpdated!)}',
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                ),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: _refresh,
                  child: filtered.isEmpty
                      ? ListView(
                          padding: const EdgeInsets.only(top: 80),
                          children: [
                            const Icon(Icons.search_off_rounded, size: 44),
                            const SizedBox(height: 12),
                            Center(child: Text(context.l10n.noSearchResults)),
                          ],
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.fromLTRB(18, 0, 18, 112),
                          itemCount: filtered.length,
                          separatorBuilder: (_, _) =>
                              const SizedBox(height: 12),
                          itemBuilder: (_, index) => _StationCard(
                            station: filtered[index],
                            onTap: () => context.push(
                              AppRoutes.station(filtered[index].id),
                            ),
                          ),
                        ),
                ),
              ),
            ],
          );
        },
      ),
    ),
  );
}

class _StationCard extends StatelessWidget {
  const _StationCard({required this.station, required this.onTap});

  final Station station;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final reason = station.availability.reason;
    final available = reason == StationAvailabilityReason.available;
    final browseOnly =
        reason == StationAvailabilityReason.hardwareFuelingDisabled;
    final colors = Theme.of(context).colorScheme;
    final badgeColor = available || browseOnly
        ? colors.primaryContainer
        : colors.errorContainer;
    final badgeTextColor = available || browseOnly
        ? colors.onPrimaryContainer
        : colors.onErrorContainer;
    final badgeText = available
        ? context.l10n.fuelingAvailable
        : browseOnly
        ? context.l10n.browsePricesAvailable
        : _availabilityMessage(context, reason);

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: BorderSide(color: colors.outlineVariant.withValues(alpha: 0.55)),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: colors.primaryContainer,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(
                  Icons.local_gas_station_rounded,
                  color: colors.onPrimaryContainer,
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      station.name,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      station.location.address,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 9,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: badgeColor,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        badgeText,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 9.5,
                          fontWeight: FontWeight.w700,
                          color: badgeTextColor,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(
                Icons.arrow_forward_ios_rounded,
                size: 16,
                color: colors.outline,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class StationDetailsPage extends ConsumerStatefulWidget {
  const StationDetailsPage({required this.stationId, super.key});

  final String stationId;

  @override
  ConsumerState<StationDetailsPage> createState() => _StationDetailsPageState();
}

class _StationDetailsPageState extends ConsumerState<StationDetailsPage> {
  late Future<_StationDetailsData> _detailsFuture;

  @override
  void initState() {
    super.initState();
    _detailsFuture = _load();
  }

  Future<_StationDetailsData> _load() async {
    final repository = ref.read(stationRepositoryProvider);
    final station = await repository.getStation(widget.stationId);
    final prices = await repository.getFuelPrices(widget.stationId);
    final availability = await repository.getAvailability(widget.stationId);
    return _StationDetailsData(
      station: station,
      prices: prices,
      availability: availability,
      refreshedAt: DateTime.now(),
    );
  }

  Future<void> _refresh() async {
    final next = _load();
    setState(() => _detailsFuture = next);
    await next;
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: Colors.transparent,
    appBar: AppBar(
      title: Text(context.l10n.stationDetails),
      backgroundColor: Colors.transparent,
    ),
    body: BrandedPageBackground(
      child: FutureBuilder<_StationDetailsData>(
        future: _detailsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || !snapshot.hasData) {
            return _RefreshMessage(
              icon: Icons.cloud_off_outlined,
              message: context.l10n.stationsLoadFailed,
              onRefresh: _refresh,
            );
          }
          final data = snapshot.data!;
          final station = data.station;
          final availability = data.availability;
          final languageCode = Localizations.localeOf(context).languageCode;
          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(18, 8, 18, 34),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Row(
                      children: [
                        Container(
                          width: 54,
                          height: 54,
                          decoration: BoxDecoration(
                            color: Theme.of(
                              context,
                            ).colorScheme.primaryContainer,
                            borderRadius: BorderRadius.circular(17),
                          ),
                          child: Icon(
                            Icons.local_gas_station_rounded,
                            color: Theme.of(
                              context,
                            ).colorScheme.onPrimaryContainer,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                station.name,
                                style: Theme.of(context).textTheme.titleLarge
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                              const SizedBox(height: 4),
                              Text(station.location.address),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                _AvailabilityBanner(availability: availability),
                const SizedBox(height: 22),
                Text(
                  context.l10n.fuelPrices,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 10),
                if (data.prices.isEmpty)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Text(context.l10n.noFuelPrices),
                    ),
                  )
                else
                  ...data.prices.map(
                    (price) => Padding(
                      padding: const EdgeInsets.only(bottom: 9),
                      child: _FuelPriceCard(
                        price: price,
                        label: _fuelLabel(context, price.product, languageCode),
                      ),
                    ),
                  ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: availability.appFuelingAvailable
                      ? () => context.push(AppRoutes.scan)
                      : null,
                  icon: const Icon(Icons.qr_code_scanner_rounded),
                  label: Text(context.l10n.startFueling),
                ),
                const SizedBox(height: 10),
                Text(
                  '${context.l10n.lastUpdated} ${DateFormat.Hm().format(data.refreshedAt)}',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    ),
  );
}

class _StationDetailsData {
  const _StationDetailsData({
    required this.station,
    required this.prices,
    required this.availability,
    required this.refreshedAt,
  });

  final Station station;
  final List<FuelPrice> prices;
  final StationAvailability availability;
  final DateTime refreshedAt;
}

class _AvailabilityBanner extends StatelessWidget {
  const _AvailabilityBanner({required this.availability});

  final StationAvailability availability;

  @override
  Widget build(BuildContext context) {
    final available =
        availability.reason == StationAvailabilityReason.available;
    final browseOnly =
        availability.reason ==
        StationAvailabilityReason.hardwareFuelingDisabled;
    final colors = Theme.of(context).colorScheme;
    final color = available || browseOnly ? colors.primary : colors.error;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: color.withValues(alpha: 0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            available
                ? Icons.check_circle_outline_rounded
                : browseOnly
                ? Icons.info_outline_rounded
                : Icons.warning_amber_rounded,
            color: color,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _availabilityMessage(context, availability.reason),
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 4),
                Text(
                  availability.status,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: colors.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FuelPriceCard extends StatelessWidget {
  const _FuelPriceCard({required this.price, required this.label});

  final FuelPrice price;
  final String label;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(13),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(13),
            ),
            child: Icon(
              _fuelIcon(price.product.kind),
              size: 21,
              color: Theme.of(context).colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                Text(
                  price.product.code,
                  style: Theme.of(context).textTheme.labelSmall,
                ),
              ],
            ),
          ),
          Text(
            '${price.unitPrice.toStringAsFixed(2)} ${price.currency}',
            style: const TextStyle(fontWeight: FontWeight.w900),
          ),
        ],
      ),
    ),
  );
}

class _RefreshMessage extends StatelessWidget {
  const _RefreshMessage({
    required this.icon,
    required this.message,
    required this.onRefresh,
  });

  final IconData icon;
  final String message;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 48),
          const SizedBox(height: 12),
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 14),
          FilledButton.tonalIcon(
            onPressed: onRefresh,
            icon: const Icon(Icons.refresh_rounded),
            label: Text(context.l10n.continueLabel),
          ),
        ],
      ),
    ),
  );
}

String _availabilityMessage(
  BuildContext context,
  StationAvailabilityReason reason,
) => switch (reason) {
  StationAvailabilityReason.available => context.l10n.fuelingAvailable,
  StationAvailabilityReason.companySelfServiceDisabled =>
    context.l10n.companySelfServiceDisabledMessage,
  StationAvailabilityReason.stationSelfServiceDisabled =>
    context.l10n.stationSelfServiceDisabledMessage,
  StationAvailabilityReason.stationMaintenance =>
    context.l10n.stationMaintenanceMessage,
  StationAvailabilityReason.hardwareFuelingDisabled =>
    context.l10n.hardwareFuelingDisabledMessage,
  StationAvailabilityReason.edgeOffline => context.l10n.edgeOfflineMessage,
  StationAvailabilityReason.noCompatibleNozzle =>
    context.l10n.noCompatibleNozzleMessage,
  StationAvailabilityReason.fuelPriceUnavailable =>
    context.l10n.fuelPriceUnavailableMessage,
  StationAvailabilityReason.outsideSchedule =>
    context.l10n.outsideScheduleMessage,
  StationAvailabilityReason.unknown => context.l10n.availabilityUnknownMessage,
};

String _fuelLabel(
  BuildContext context,
  FuelProduct product,
  String languageCode,
) => switch (product.kind) {
  FuelKind.gasoline91 => context.l10n.fuelGasoline91,
  FuelKind.gasoline95 => context.l10n.fuelGasoline95,
  FuelKind.diesel => context.l10n.fuelDiesel,
  FuelKind.kerosene => context.l10n.fuelKerosene,
  FuelKind.lpg => context.l10n.fuelLpg,
  FuelKind.other =>
    product.localizedName(languageCode).isEmpty
        ? context.l10n.fuelOther
        : product.localizedName(languageCode),
};

IconData _fuelIcon(FuelKind kind) => switch (kind) {
  FuelKind.gasoline91 => Icons.local_gas_station_rounded,
  FuelKind.gasoline95 => Icons.oil_barrel_rounded,
  FuelKind.diesel => Icons.local_shipping_rounded,
  FuelKind.kerosene => Icons.local_fire_department_rounded,
  FuelKind.lpg => Icons.propane_tank_rounded,
  FuelKind.other => Icons.water_drop_outlined,
};
