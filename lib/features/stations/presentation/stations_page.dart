import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:intl/intl.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/localization/localization_extension.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/stations/domain/models/station.dart';
import 'package:nnexoris_customer/features/stations/domain/repositories/station_repository.dart';
import 'package:nnexoris_customer/shared/widgets/branded_app_bar_background.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';

class StationsPage extends ConsumerStatefulWidget {
  const StationsPage({super.key});

  @override
  ConsumerState<StationsPage> createState() => _StationsPageState();
}

class _StationsPageState extends ConsumerState<StationsPage>
    with WidgetsBindingObserver {
  late Future<List<Station>> _stationsFuture;
  DateTime? _lastUpdated;
  String _query = '';
  GeoPosition? _origin;
  Map<String, StationRouteMetrics> _routes = const {};
  bool _locationUnavailable = false;
  String? _selectedCompanyId;
  bool _sortNearest = false;
  bool _waitingForLocationSettings = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _stationsFuture = _loadStations();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && _waitingForLocationSettings) {
      _waitingForLocationSettings = false;
      _refresh();
    }
  }

  Future<List<Station>> _loadStations() async {
    final repository = ref.read(stationRepositoryProvider);
    GeoPosition? origin;
    try {
      origin = await ref.read(locationServiceProvider).currentLocation();
    } on Object {
      origin = null;
    }
    final stations = await repository.getStations(
      StationQuery(latitude: origin?.latitude, longitude: origin?.longitude),
    );
    Map<String, StationRouteMetrics> routes = const {};
    if (origin != null) {
      try {
        routes = await repository.getRouteMetrics(
          origin,
          stations.map((station) => station.id).toList(growable: false),
        );
      } on Object {
        routes = const {};
      }
    }
    _origin = origin;
    _routes = routes;
    _locationUnavailable = origin == null;
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
    backgroundColor: Theme.of(context).brightness == Brightness.dark
        ? const Color(0xFF071823)
        : const Color(0xFFF8FCFB),
    appBar: AppBar(
      toolbarHeight: 64,
      foregroundColor: Theme.of(context).colorScheme.primary,
      title: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.local_gas_station_rounded, size: 20),
          ),
          const SizedBox(width: 12),
          Text(
            context.l10n.stations,
            style: const TextStyle(fontWeight: FontWeight.w900),
          ),
        ],
      ),
      backgroundColor: Theme.of(context).brightness == Brightness.dark
          ? const Color(0xFF071823)
          : const Color(0xFFF8FCFB),
      flexibleSpace: const BrandedAppBarBackground(),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
      ),
      elevation: 0,
      scrolledUnderElevation: 0,
      surfaceTintColor: Colors.transparent,
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
          final languageCode = Localizations.localeOf(context).languageCode;
          final companies = <String, String>{
            for (final station in stations)
              if (station.companyId.isNotEmpty)
                station.companyId: station.localizedCompanyName(languageCode),
          };
          final query = _query.trim().toLowerCase();
          final filtered = stations.where((station) {
            final company = station.localizedCompanyName(languageCode);
            final matchesCompany =
                _selectedCompanyId == null ||
                station.companyId == _selectedCompanyId;
            final matchesQuery =
                query.isEmpty ||
                station.name.toLowerCase().contains(query) ||
                station.location.address.toLowerCase().contains(query) ||
                company.toLowerCase().contains(query);
            return matchesCompany && matchesQuery;
          }).toList();
          if (_sortNearest) {
            filtered.sort(
              (a, b) => (_routes[a.id]?.distanceMeters ?? double.infinity)
                  .compareTo(_routes[b.id]?.distanceMeters ?? double.infinity),
            );
          }
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 14, 18, 10),
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF073F37).withValues(alpha: 0.10),
                        blurRadius: 18,
                        offset: const Offset(0, 7),
                      ),
                    ],
                  ),
                  child: SearchBar(
                    elevation: const WidgetStatePropertyAll(0),
                    backgroundColor: WidgetStatePropertyAll(
                      Theme.of(context).brightness == Brightness.dark
                          ? const Color(0xFF0E2B2A)
                          : const Color(0xFFEAF8F3),
                    ),
                    shape: WidgetStatePropertyAll(
                      RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                        side: BorderSide(
                          color: Theme.of(
                            context,
                          ).colorScheme.primary.withValues(alpha: 0.22),
                        ),
                      ),
                    ),
                    leading: Container(
                      margin: const EdgeInsetsDirectional.only(start: 5),
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.primaryContainer,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.search_rounded,
                        size: 20,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ),
                    hintText: context.l10n.stationSearchHint,
                    textStyle: const WidgetStatePropertyAll(
                      TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                    ),
                    hintStyle: WidgetStatePropertyAll(
                      TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                    onChanged: (value) => setState(() => _query = value),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 0, 18, 10),
                child: _StationFilters(
                  companies: companies,
                  selectedCompanyId: _selectedCompanyId,
                  nearestSelected: _sortNearest,
                  onAll: () => setState(() {
                    _selectedCompanyId = null;
                    _sortNearest = false;
                  }),
                  onNearest: _routes.isEmpty
                      ? null
                      : () => setState(() {
                          _selectedCompanyId = null;
                          _sortNearest = true;
                        }),
                  onCompany: (companyId) => setState(() {
                    _selectedCompanyId = companyId;
                    _sortNearest = false;
                  }),
                ),
              ),
              if (_locationUnavailable)
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 0, 18, 10),
                  child: _LocationNotice(
                    message: context.l10n.locationPermissionMessage,
                    onActivate: _requestLocationAccess,
                  ),
                ),
              if (filtered.any(_hasCoordinates)) ...[
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 2, 18, 10),
                  child: Row(
                    children: [
                      Icon(
                        Icons.map_rounded,
                        size: 19,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 7),
                      Text(
                        context.l10n.stationsMap,
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
                  child: _StationsMap(
                    stations: filtered,
                    origin: _origin,
                    onStationTap: (station) =>
                        context.push(AppRoutes.station(station.id)),
                  ),
                ),
                if (_routes.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 0, 18, 8),
                    child: Align(
                      alignment: AlignmentDirectional.centerEnd,
                      child: Text(
                        context.l10n.poweredByGoogle,
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                  ),
              ],
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
                            route: _routes[filtered[index].id],
                            onTap: () => context.push(
                              AppRoutes.station(filtered[index].id),
                            ),
                            onNavigate: () => _navigate(filtered[index]),
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

  Future<void> _navigate(Station station) async {
    final opened = await ref
        .read(stationNavigationServiceProvider)
        .navigateTo(station);
    if (!opened && mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(context.l10n.routeUnavailable)));
    }
  }

  Future<void> _requestLocationAccess() async {
    final service = ref.read(locationServiceProvider);
    final status = await service.accessStatus();
    switch (status) {
      case LocationAccessStatus.granted:
        await _refresh();
      case LocationAccessStatus.denied:
        final next = await service.requestAccess();
        if (next == LocationAccessStatus.granted) await _refresh();
      case LocationAccessStatus.deniedForever:
        _waitingForLocationSettings = true;
        await service.openAppSettings();
      case LocationAccessStatus.serviceDisabled:
        _waitingForLocationSettings = true;
        await service.openLocationSettings();
    }
  }
}

class _StationCard extends StatelessWidget {
  const _StationCard({
    required this.station,
    required this.route,
    required this.onTap,
    required this.onNavigate,
  });

  final Station station;
  final StationRouteMetrics? route;
  final VoidCallback onTap;
  final VoidCallback onNavigate;

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

    final languageCode = Localizations.localeOf(context).languageCode;
    return Card(
      elevation: 0,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: BorderSide(color: colors.outlineVariant.withValues(alpha: 0.55)),
      ),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(11),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [colors.primary, colors.tertiary],
                      ),
                      borderRadius: BorderRadius.circular(13),
                    ),
                    child: Icon(
                      Icons.local_gas_station_rounded,
                      size: 21,
                      color: colors.onPrimary,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          station.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          station.location.address,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.labelSmall
                              ?.copyWith(color: colors.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  _StatusDot(active: available || browseOnly),
                ],
              ),
              const SizedBox(height: 9),
              Row(
                children: [
                  Expanded(
                    child: _RouteStat(
                      icon: Icons.route_rounded,
                      text: route == null
                          ? '—'
                          : context.l10n.distanceKm(
                              (route!.distanceMeters / 1000).toStringAsFixed(1),
                            ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: _RouteStat(
                      icon: Icons.schedule_rounded,
                      text: route == null
                          ? '—'
                          : context.l10n.arrivalMinutes(
                              (route!.durationSeconds / 60).ceil(),
                            ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                context.l10n.availableFuel,
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: colors.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 4),
              Wrap(
                spacing: 5,
                runSpacing: 5,
                children: station.fuelPrices.isEmpty
                    ? [Text(context.l10n.noFuelPrices)]
                    : station.fuelPrices
                          .map(
                            (price) => _FuelChip(
                              icon: _fuelIcon(price.product.kind),
                              color: _fuelColor(price.product.kind),
                              label: _fuelLabel(
                                context,
                                price.product,
                                languageCode,
                              ),
                            ),
                          )
                          .toList(growable: false),
              ),
              const SizedBox(height: 9),
              Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 5,
                      ),
                      decoration: BoxDecoration(
                        color: badgeColor,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        badgeText,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w800,
                          color: badgeTextColor,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 7),
                  FilledButton.tonalIcon(
                    onPressed: _hasCoordinates(station) ? onNavigate : null,
                    icon: const Icon(Icons.navigation_rounded, size: 15),
                    label: Text(context.l10n.navigateToStation),
                    style: FilledButton.styleFrom(
                      visualDensity: VisualDensity.compact,
                      textStyle: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StationsMap extends StatelessWidget {
  const _StationsMap({
    required this.stations,
    required this.origin,
    required this.onStationTap,
  });

  final List<Station> stations;
  final GeoPosition? origin;
  final ValueChanged<Station> onStationTap;

  @override
  Widget build(BuildContext context) {
    final mappedStations = stations.where(_hasCoordinates).toList();
    final target = origin == null
        ? LatLng(
            mappedStations.first.location.latitude,
            mappedStations.first.location.longitude,
          )
        : LatLng(origin!.latitude, origin!.longitude);
    final colors = Theme.of(context).colorScheme;
    return Container(
      height: 218,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        border: Border.all(
          color: colors.outlineVariant.withValues(alpha: 0.65),
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: GoogleMap(
        initialCameraPosition: CameraPosition(target: target, zoom: 11.5),
        myLocationEnabled: origin != null,
        myLocationButtonEnabled: origin != null,
        zoomControlsEnabled: false,
        compassEnabled: false,
        mapToolbarEnabled: false,
        markers: {
          for (final station in mappedStations)
            Marker(
              markerId: MarkerId(station.id),
              position: LatLng(
                station.location.latitude,
                station.location.longitude,
              ),
              infoWindow: InfoWindow(
                title: station.name,
                snippet: station.location.address,
                onTap: () => onStationTap(station),
              ),
            ),
        },
      ),
    );
  }
}

class _StationFilters extends StatelessWidget {
  const _StationFilters({
    required this.companies,
    required this.selectedCompanyId,
    required this.nearestSelected,
    required this.onAll,
    required this.onNearest,
    required this.onCompany,
  });

  final Map<String, String> companies;
  final String? selectedCompanyId;
  final bool nearestSelected;
  final VoidCallback onAll;
  final VoidCallback? onNearest;
  final ValueChanged<String?> onCompany;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final companyName = companies[selectedCompanyId];
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          ChoiceChip(
            selected: selectedCompanyId == null && !nearestSelected,
            avatar: const Icon(Icons.apps_rounded, size: 17),
            label: Text(context.l10n.filterAll),
            onSelected: (_) => onAll(),
          ),
          const SizedBox(width: 7),
          ChoiceChip(
            selected: nearestSelected,
            avatar: const Icon(Icons.near_me_rounded, size: 17),
            label: Text(context.l10n.filterNearest),
            onSelected: onNearest == null ? null : (_) => onNearest!(),
          ),
          if (companies.isNotEmpty) ...[
            const SizedBox(width: 7),
            PopupMenuButton<String>(
              initialValue: selectedCompanyId,
              onSelected: onCompany,
              itemBuilder: (_) => companies.entries
                  .map(
                    (entry) => PopupMenuItem(
                      value: entry.key,
                      child: Row(
                        children: [
                          Icon(
                            Icons.business_rounded,
                            size: 18,
                            color: colors.primary,
                          ),
                          const SizedBox(width: 8),
                          Text(entry.value),
                        ],
                      ),
                    ),
                  )
                  .toList(growable: false),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: selectedCompanyId == null
                      ? colors.surfaceContainerHighest.withValues(alpha: 0.65)
                      : colors.primaryContainer,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: colors.outlineVariant.withValues(alpha: 0.55),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.business_rounded,
                      size: 17,
                      color: colors.primary,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      companyName ?? context.l10n.filterCompanies,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Icon(Icons.keyboard_arrow_down_rounded, size: 18),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _LocationNotice extends StatelessWidget {
  const _LocationNotice({required this.message, required this.onActivate});

  final String message;
  final VoidCallback onActivate;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: colors.secondaryContainer.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(15),
      ),
      child: Row(
        children: [
          Icon(Icons.location_off_rounded, size: 19, color: colors.secondary),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.labelMedium,
            ),
          ),
          const SizedBox(width: 8),
          FilledButton.tonal(
            onPressed: onActivate,
            style: FilledButton.styleFrom(
              visualDensity: VisualDensity.compact,
              padding: const EdgeInsets.symmetric(horizontal: 10),
            ),
            child: Text(context.l10n.enableLocation),
          ),
        ],
      ),
    );
  }
}

class _RouteStat extends StatelessWidget {
  const _RouteStat({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest.withValues(alpha: 0.58),
        borderRadius: BorderRadius.circular(11),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 15, color: colors.primary),
          const SizedBox(width: 5),
          Flexible(
            child: Text(
              text,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FuelChip extends StatelessWidget {
  const _FuelChip({
    required this.icon,
    required this.color,
    required this.label,
  });

  final IconData icon;
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 3),
          Text(
            label,
            style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }
}

class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.active});

  final bool active;

  @override
  Widget build(BuildContext context) => Container(
    width: 11,
    height: 11,
    decoration: BoxDecoration(
      color: active
          ? const Color(0xFF20B486)
          : Theme.of(context).colorScheme.error,
      shape: BoxShape.circle,
      boxShadow: [
        BoxShadow(
          color:
              (active
                      ? const Color(0xFF20B486)
                      : Theme.of(context).colorScheme.error)
                  .withValues(alpha: 0.3),
          blurRadius: 7,
          spreadRadius: 2,
        ),
      ],
    ),
  );
}

bool _hasCoordinates(Station station) =>
    station.location.latitude.abs() > 0.000001 ||
    station.location.longitude.abs() > 0.000001;

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
    GeoPosition? origin;
    StationRouteMetrics? route;
    try {
      origin = await ref.read(locationServiceProvider).currentLocation();
      if (origin != null) {
        route = (await repository.getRouteMetrics(origin, [
          station.id,
        ]))[station.id];
      }
    } on Object {
      origin = null;
      route = null;
    }
    return _StationDetailsData(
      station: station,
      prices: prices,
      availability: availability,
      origin: origin,
      route: route,
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
    backgroundColor: Theme.of(context).brightness == Brightness.dark
        ? const Color(0xFF071823)
        : const Color(0xFFF8FCFB),
    appBar: AppBar(
      toolbarHeight: 60,
      foregroundColor: Theme.of(context).colorScheme.primary,
      title: Text(
        context.l10n.stationDetails,
        style: const TextStyle(fontWeight: FontWeight.w900),
      ),
      backgroundColor: Theme.of(context).brightness == Brightness.dark
          ? const Color(0xFF071823)
          : const Color(0xFFF8FCFB),
      flexibleSpace: const BrandedAppBarBackground(),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(18)),
      ),
      elevation: 0,
      scrolledUnderElevation: 0,
      surfaceTintColor: Colors.transparent,
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
                if (_hasCoordinates(station)) ...[
                  _StationsMap(
                    stations: [station],
                    origin: data.origin,
                    onStationTap: (_) {},
                  ),
                  const SizedBox(height: 12),
                ],
                Row(
                  children: [
                    Expanded(
                      child: _RouteStat(
                        icon: Icons.route_rounded,
                        text: data.route == null
                            ? '—'
                            : context.l10n.distanceKm(
                                (data.route!.distanceMeters / 1000)
                                    .toStringAsFixed(1),
                              ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _RouteStat(
                        icon: Icons.schedule_rounded,
                        text: data.route == null
                            ? '—'
                            : context.l10n.arrivalMinutes(
                                (data.route!.durationSeconds / 60).ceil(),
                              ),
                      ),
                    ),
                  ],
                ),
                if (data.route != null) ...[
                  const SizedBox(height: 5),
                  Text(
                    context.l10n.poweredByGoogle,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _hasCoordinates(station)
                      ? () => _navigate(station)
                      : null,
                  icon: const Icon(Icons.navigation_rounded),
                  label: Text(context.l10n.navigateToStation),
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

  Future<void> _navigate(Station station) async {
    final opened = await ref
        .read(stationNavigationServiceProvider)
        .navigateTo(station);
    if (!opened && mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(context.l10n.routeUnavailable)));
    }
  }
}

class _StationDetailsData {
  const _StationDetailsData({
    required this.station,
    required this.prices,
    required this.availability,
    required this.origin,
    required this.route,
    required this.refreshedAt,
  });

  final Station station;
  final List<FuelPrice> prices;
  final StationAvailability availability;
  final GeoPosition? origin;
  final StationRouteMetrics? route;
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
  Widget build(BuildContext context) {
    final fuelColor = _fuelColor(price.product.kind);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: fuelColor.withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(13),
                border: Border.all(color: fuelColor.withValues(alpha: 0.28)),
              ),
              child: Icon(
                _fuelIcon(price.product.kind),
                size: 21,
                color: fuelColor,
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
  FuelKind.gasoline98 => context.l10n.fuelGasoline98,
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
  FuelKind.gasoline98 => Icons.local_gas_station_rounded,
  FuelKind.diesel => Icons.local_shipping_rounded,
  FuelKind.kerosene => Icons.local_fire_department_rounded,
  FuelKind.lpg => Icons.propane_tank_rounded,
  FuelKind.other => Icons.water_drop_outlined,
};

Color _fuelColor(FuelKind kind) => switch (kind) {
  FuelKind.gasoline91 => const Color(0xFF16A34A),
  FuelKind.gasoline95 => const Color(0xFFDC2626),
  FuelKind.gasoline98 => const Color(0xFF2563EB),
  FuelKind.diesel => const Color(0xFFF4C430),
  FuelKind.kerosene => const Color(0xFFF97316),
  FuelKind.lpg => const Color(0xFF8B5CF6),
  FuelKind.other => const Color(0xFF0F766E),
};
