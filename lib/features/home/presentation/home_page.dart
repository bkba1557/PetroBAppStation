import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:nnexoris_customer/app/router/app_routes.dart';
import 'package:nnexoris_customer/core/providers.dart';
import 'package:nnexoris_customer/features/home/domain/dashboard.dart';
import 'package:nnexoris_customer/shared/widgets/branded_page_background.dart';
import 'package:nnexoris_customer/shared/widgets/branded_wallet_card.dart';

class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});
  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  String period = '30d';
  DateTimeRange? customRange;
  late Future<(DashboardData, AnalyticsData)> data;
  @override
  void initState() {
    super.initState();
    data = load();
  }

  Future<(DashboardData, AnalyticsData)> load() async {
    final repo = ref.read(dashboardRepositoryProvider);
    return (
      await repo.dashboard(),
      await repo.analytics(
        period,
        from: customRange?.start,
        to: customRange?.end.add(const Duration(days: 1)),
      ),
    );
  }

  void reload([String? next]) => setState(() {
    if (next != null) period = next;
    data = load();
  });
  Future<void> chooseCustom() async {
    final now = DateTime.now();
    final range = await showDateRangePicker(
      context: context,
      firstDate: DateTime(now.year - 1, now.month, now.day),
      lastDate: now,
      initialDateRange: customRange,
    );
    if (range == null) return;
    setState(() {
      customRange = range;
      period = 'custom';
      data = load();
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: BrandedPageBackground(
      child: SafeArea(
        child: FutureBuilder<(DashboardData, AnalyticsData)>(
          future: data,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const _DashboardSkeleton();
            }
            if (snap.hasError || !snap.hasData) {
              return _LoadFailure(onRetry: reload);
            }
            return RefreshIndicator(
              onRefresh: () async {
                reload();
                await data;
              },
              child: _DashboardBody(
                dashboard: snap.data!.$1,
                analytics: snap.data!.$2,
                period: period,
                onPeriod: reload,
                onCustom: chooseCustom,
              ),
            );
          },
        ),
      ),
    ),
  );
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({
    required this.dashboard,
    required this.analytics,
    required this.period,
    required this.onPeriod,
    required this.onCustom,
  });
  final DashboardData dashboard;
  final AnalyticsData analytics;
  final String period;
  final ValueChanged<String> onPeriod;
  final VoidCallback onCustom;
  String money(Object? v) => '${(v as num? ?? 0).toStringAsFixed(2)} SAR';
  @override
  Widget build(BuildContext context) {
    final name = dashboard.customer['name'] as String? ?? '';
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'صباح الخير'
        : hour < 18
        ? 'مساء الخير'
        : 'مساء النور';
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      padding: const EdgeInsets.fromLTRB(18, 10, 18, 112),
      children: [
        _WelcomeHeader(
          name: name.isEmpty ? 'عميل PetroB' : name,
          greeting: greeting,
          initial: name.isEmpty ? 'P' : name.characters.first,
        ),
        const SizedBox(height: 20),
        BrandedWalletCard(
          available: money(dashboard.wallet['available']),
          reserved: money(dashboard.wallet['held']),
          updatedLabel:
              'آخر تحديث ${_shortDate(dashboard.wallet['updatedAt'])}',
          onTopUp: () => context.push(AppRoutes.walletTopUp),
        ),
        const SizedBox(height: 24),
        _FuelingAction(onTap: () => context.push(AppRoutes.scan)),
        const SizedBox(height: 26),
        const _SectionTitle(
          'خدماتك السريعة',
          subtitle: 'كل ما تحتاجه على بُعد خطوة',
        ),
        const SizedBox(height: 14),
        _QuickActions(
          actions: [
            _QuickActionData(
              icon: Icons.near_me_rounded,
              label: 'المحطات',
              caption: 'الأقرب إليك',
              color: const Color(0xFF16A085),
              onTap: () => context.go(AppRoutes.stations),
            ),
            _QuickActionData(
              icon: Icons.directions_car_filled_rounded,
              label: 'مركباتي',
              caption: 'إدارة المركبات',
              color: const Color(0xFF3B82F6),
              onTap: () => context.push(AppRoutes.vehicles),
            ),
            _QuickActionData(
              icon: Icons.receipt_long_rounded,
              label: 'العمليات',
              caption: 'السجل الكامل',
              color: const Color(0xFFF59E0B),
              onTap: () => context.push(AppRoutes.transactions),
            ),
            _QuickActionData(
              icon: Icons.add_card_rounded,
              label: 'شحن الرصيد',
              caption: 'إضافة رصيد',
              color: const Color(0xFF8B5CF6),
              onTap: () => context.push(AppRoutes.walletTopUp),
            ),
          ],
        ),
        const SizedBox(height: 28),
        const _SectionTitle(
          'ملخص نشاطك',
          subtitle: 'نظرة سريعة على آخر 30 يومًا',
        ),
        const SizedBox(height: 14),
        GridView.count(
          crossAxisCount: MediaQuery.sizeOf(context).width > 600 ? 4 : 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          childAspectRatio: MediaQuery.sizeOf(context).width < 370 ? 1.35 : 1.5,
          children: [
            _Metric(
              'التعبئات',
              '${dashboard.summary['totalFuelings']}',
              Icons.ev_station_outlined,
              const Color(0xFF16A085),
            ),
            _Metric(
              'اللترات',
              (dashboard.summary['totalLiters'] as num).toStringAsFixed(3),
              Icons.water_drop_outlined,
              const Color(0xFF3B82F6),
            ),
            _Metric(
              'الإنفاق',
              money(dashboard.summary['totalSpent']),
              Icons.payments_outlined,
              const Color(0xFFF59E0B),
            ),
            _Metric(
              'متوسط العملية',
              money(dashboard.summary['averageTransaction']),
              Icons.analytics_outlined,
              const Color(0xFF8B5CF6),
            ),
            _Metric(
              'المحطات',
              '${dashboard.summary['stationsUsed']}',
              Icons.location_on_outlined,
              const Color(0xFFEF6262),
            ),
            _Metric(
              'المركبات',
              '${dashboard.summary['vehiclesUsed']}',
              Icons.directions_car_outlined,
              const Color(0xFF0EA5E9),
            ),
          ],
        ),
        const SizedBox(height: 24),
        Row(
          children: [
            const Expanded(child: _SectionTitle('تحليلاتك')),
            DropdownButton<String>(
              value: period,
              underline: const SizedBox(),
              onChanged: (v) {
                if (v == 'custom') {
                  onCustom();
                } else if (v != null) {
                  onPeriod(v);
                }
              },
              items:
                  const {
                        '7d': '7 أيام',
                        '30d': '30 يوم',
                        '3m': '3 أشهر',
                        '6m': '6 أشهر',
                        '1y': 'سنة',
                        'custom': 'فترة مخصصة',
                      }.entries
                      .map(
                        (e) => DropdownMenuItem(
                          value: e.key,
                          child: Text(e.value),
                        ),
                      )
                      .toList(),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('الإنفاق عبر الوقت'),
                const SizedBox(height: 20),
                SizedBox(
                  height: 180,
                  child: analytics.timeSeries.isEmpty
                      ? const _Empty('لا توجد عمليات في هذه الفترة')
                      : CustomPaint(
                          painter: _LineChart(
                            analytics.timeSeries
                                .map((e) => (e['spent'] as num).toDouble())
                                .toList(),
                          ),
                          child: const SizedBox.expand(),
                        ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _SeriesCard(
                title: 'اللترات عبر الوقت',
                values: analytics.timeSeries
                    .map((e) => (e['liters'] as num).toDouble())
                    .toList(),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _SeriesCard(
                title: 'عدد التعبئات',
                values: analytics.timeSeries
                    .map((e) => (e['fuelings'] as num).toDouble())
                    .toList(),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _AverageCard(
                'متوسط سعر اللتر',
                money(analytics.averages['unitPrice']),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _AverageCard(
                'متوسط التعبئة',
                money(analytics.averages['fuelingAmount']),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('توزيع أنواع الوقود'),
                const SizedBox(height: 12),
                if (analytics.fuels.isEmpty)
                  const _Empty('لا توجد بيانات')
                else
                  ...analytics.fuels.map(
                    (e) => _Bar(
                      label: '${e['fuelCode']}',
                      value: (e['liters'] as num).toDouble(),
                      max: analytics.fuels
                          .map((x) => (x['liters'] as num).toDouble())
                          .fold<double>(0.0, (a, b) => math.max(a, b)),
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        _Ranking(
          title: 'المحطات الأكثر استخدامًا',
          items: analytics.stations,
          label: 'name',
        ),
        const SizedBox(height: 12),
        _Ranking(
          title: 'المركبات الأكثر استخدامًا',
          items: analytics.vehicles,
          label: 'name',
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('حالات جلسات التعبئة'),
                const SizedBox(height: 10),
                if (analytics.statuses.isEmpty)
                  const _Empty('لا توجد جلسات')
                else
                  ...analytics.statuses.map(
                    (e) => ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: Text('${e['status']}'),
                      trailing: Text('${e['count']}'),
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        _SeriesCard(
          title: 'سجل شحن المحفظة',
          values: analytics.topUps
              .map((e) => (e['amount'] as num).toDouble())
              .toList(),
        ),
      ],
    );
  }

  static String _shortDate(Object? value) {
    if (value is! String) return '—';
    return DateFormat(
      'd MMM، HH:mm',
      'ar',
    ).format(DateTime.parse(value).toLocal());
  }
}

class _WelcomeHeader extends StatelessWidget {
  const _WelcomeHeader({
    required this.name,
    required this.greeting,
    required this.initial,
  });

  final String name;
  final String greeting;
  final String initial;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    return Row(
      children: [
        Container(
          width: 50,
          height: 50,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF25D7A2), Color(0xFF087F6E)],
            ),
            borderRadius: BorderRadius.circular(17),
            border: Border.all(color: Colors.white.withValues(alpha: .18)),
            boxShadow: const [
              BoxShadow(
                color: Color(0x3320C997),
                blurRadius: 18,
                offset: Offset(0, 7),
              ),
            ],
          ),
          child: Text(
            initial,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const SizedBox(width: 13),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                greeting,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                  letterSpacing: -.2,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Material(
          color: isDark
              ? const Color(0xFF102936)
              : Colors.white.withValues(alpha: .9),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(15),
            side: BorderSide(
              color: theme.colorScheme.outlineVariant.withValues(alpha: .7),
            ),
          ),
          child: IconButton(
            onPressed: () {},
            tooltip: 'الإشعارات',
            icon: Badge(
              smallSize: 7,
              backgroundColor: const Color(0xFFFFB547),
              child: Icon(
                Icons.notifications_none_rounded,
                color: theme.colorScheme.onSurface,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _FuelingAction extends StatelessWidget {
  const _FuelingAction({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
    color: Colors.transparent,
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(24),
      child: Ink(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: AlignmentDirectional.topStart,
            end: AlignmentDirectional.bottomEnd,
            colors: [Color(0xFF143E4B), Color(0xFF0A7668)],
          ),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withValues(alpha: .1)),
          boxShadow: const [
            BoxShadow(
              color: Color(0x2915C795),
              blurRadius: 22,
              offset: Offset(0, 10),
            ),
          ],
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            PositionedDirectional(
              end: -18,
              child: Icon(
                Icons.local_gas_station_rounded,
                color: Colors.white.withValues(alpha: .055),
                size: 112,
              ),
            ),
            Row(
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: .13),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: .14),
                    ),
                  ),
                  child: const Icon(
                    Icons.qr_code_scanner_rounded,
                    size: 28,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'جاهز للتعبئة؟',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'امسح رمز المحطة وابدأ فورًا',
                        style: TextStyle(
                          color: Color(0xFFC8EDE5),
                          fontSize: 11.5,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(
                    Icons.arrow_back_rounded,
                    color: Color(0xFF087F6E),
                    size: 21,
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

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text, {this.subtitle});
  final String text;
  final String? subtitle;

  @override
  Widget build(BuildContext c) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        children: [
          Container(
            width: 5,
            height: 21,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Color(0xFF25D7A2), Color(0xFF087F6E)],
              ),
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: Theme.of(c).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w900,
                letterSpacing: -.2,
              ),
            ),
          ),
        ],
      ),
      if (subtitle != null) ...[
        const SizedBox(height: 4),
        Padding(
          padding: const EdgeInsetsDirectional.only(start: 15),
          child: Text(
            subtitle!,
            style: Theme.of(c).textTheme.bodySmall?.copyWith(
              color: Theme.of(c).colorScheme.onSurfaceVariant,
            ),
          ),
        ),
      ],
    ],
  );
}

class _QuickActionData {
  const _QuickActionData({
    required this.icon,
    required this.label,
    required this.caption,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final String caption;
  final Color color;
  final VoidCallback onTap;
}

class _QuickActions extends StatelessWidget {
  const _QuickActions({required this.actions});

  final List<_QuickActionData> actions;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final columns = constraints.maxWidth >= 620 ? 4 : 2;
      return GridView.builder(
        itemCount: actions.length,
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: columns,
          mainAxisSpacing: 11,
          crossAxisSpacing: 11,
          childAspectRatio: constraints.maxWidth < 350 ? 1.05 : 1.25,
        ),
        itemBuilder: (_, index) => _QuickAction(action: actions[index]),
      );
    },
  );
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({required this.action});

  final _QuickActionData action;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    return Material(
      color: isDark
          ? const Color(0xFF0E222E).withValues(alpha: .96)
          : Colors.white.withValues(alpha: .94),
      borderRadius: BorderRadius.circular(21),
      child: InkWell(
        onTap: action.onTap,
        borderRadius: BorderRadius.circular(21),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(21),
            border: Border.all(
              color: theme.colorScheme.outlineVariant.withValues(alpha: .62),
            ),
            boxShadow: isDark
                ? null
                : const [
                    BoxShadow(
                      color: Color(0x0D0B5146),
                      blurRadius: 18,
                      offset: Offset(0, 7),
                    ),
                  ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      color: action.color.withValues(alpha: isDark ? .18 : .11),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Icon(action.icon, size: 21, color: action.color),
                  ),
                  const Spacer(),
                  Icon(
                    Icons.arrow_outward_rounded,
                    size: 17,
                    color: theme.colorScheme.onSurfaceVariant.withValues(
                      alpha: .55,
                    ),
                  ),
                ],
              ),
              const Spacer(),
              Text(
                action.label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                action.caption,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value, this.icon, this.color);
  final String label, value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext c) {
    final theme = Theme.of(c);
    final isDark = theme.brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: isDark
            ? const Color(0xFF0E222E).withValues(alpha: .96)
            : Colors.white.withValues(alpha: .94),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: theme.colorScheme.outlineVariant.withValues(alpha: .58),
        ),
        boxShadow: isDark
            ? null
            : const [
                BoxShadow(
                  color: Color(0x0A0B5146),
                  blurRadius: 16,
                  offset: Offset(0, 6),
                ),
              ],
      ),
      child: Row(
        children: [
          Container(
            width: 39,
            height: 39,
            decoration: BoxDecoration(
              color: color.withValues(alpha: isDark ? .18 : .11),
              borderRadius: BorderRadius.circular(13),
            ),
            child: Icon(icon, size: 19, color: color),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                    letterSpacing: -.2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
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

class _AverageCard extends StatelessWidget {
  const _AverageCard(this.label, this.value);
  final String label, value;
  @override
  Widget build(BuildContext c) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(c).textTheme.bodySmall),
          const SizedBox(height: 6),
          Text(
            value,
            style: Theme.of(
              c,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
        ],
      ),
    ),
  );
}

class _SeriesCard extends StatelessWidget {
  const _SeriesCard({required this.title, required this.values});
  final String title;
  final List<double> values;
  @override
  Widget build(BuildContext c) => Card(
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title),
          const SizedBox(height: 12),
          SizedBox(
            height: 110,
            child: values.isEmpty
                ? const _Empty('لا توجد بيانات')
                : CustomPaint(
                    painter: _LineChart(values),
                    child: const SizedBox.expand(),
                  ),
          ),
        ],
      ),
    ),
  );
}

class _Empty extends StatelessWidget {
  const _Empty(this.text);
  final String text;
  @override
  Widget build(BuildContext c) => Center(
    child: Padding(padding: const EdgeInsets.all(24), child: Text(text)),
  );
}

class _Bar extends StatelessWidget {
  const _Bar({required this.label, required this.value, required this.max});
  final String label;
  final double value, max;
  @override
  Widget build(BuildContext c) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Row(
      children: [
        SizedBox(width: 92, child: Text(label)),
        Expanded(
          child: LinearProgressIndicator(
            value: max == 0 ? 0 : value / max,
            minHeight: 9,
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        const SizedBox(width: 10),
        Text(value.toStringAsFixed(1)),
      ],
    ),
  );
}

class _Ranking extends StatelessWidget {
  const _Ranking({
    required this.title,
    required this.items,
    required this.label,
  });
  final String title, label;
  final List<Map<String, dynamic>> items;
  @override
  Widget build(BuildContext c) => Card(
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title),
          const SizedBox(height: 10),
          if (items.isEmpty)
            const _Empty('لا توجد بيانات')
          else
            ...items.asMap().entries.map(
              (e) => ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(radius: 15, child: Text('${e.key + 1}')),
                title: Text('${e.value[label]}'),
                trailing: Text('${e.value['fuelings']} تعبئة'),
              ),
            ),
        ],
      ),
    ),
  );
}

class _LineChart extends CustomPainter {
  _LineChart(this.values);
  final List<double> values;
  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final max = values.fold<double>(0.0, (a, b) => math.max(a, b));
    final p = Paint()
      ..color = const Color(0xFF25D7A2)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final fill = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [const Color(0x6625D7A2), Colors.transparent],
      ).createShader(Offset.zero & size);
    final path = Path();
    for (var i = 0; i < values.length; i++) {
      final x = size.width * i / (values.length - 1);
      final y =
          size.height -
          (max == 0 ? 0 : values[i] / max) * (size.height - 12) -
          6;
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    final area = Path.from(path)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(area, fill);
    canvas.drawPath(path, p);
  }

  @override
  bool shouldRepaint(covariant _LineChart old) => old.values != values;
}

class _DashboardSkeleton extends StatelessWidget {
  const _DashboardSkeleton();

  @override
  Widget build(BuildContext c) => TweenAnimationBuilder<double>(
    tween: Tween(begin: .35, end: .8),
    duration: const Duration(milliseconds: 900),
    builder: (_, v, child) => Opacity(opacity: v, child: child),
    child: ListView(
      padding: const EdgeInsets.all(20),
      children: List.generate(
        7,
        (i) => Container(
          height: i == 1 ? 180 : 90,
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            color: const Color(0xFF102531),
            borderRadius: BorderRadius.circular(22),
          ),
        ),
      ),
    ),
  );
}

class _LoadFailure extends StatelessWidget {
  const _LoadFailure({required this.onRetry});
  final VoidCallback onRetry;
  @override
  Widget build(BuildContext c) => Center(
    child: Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.cloud_off_outlined, size: 54),
          const SizedBox(height: 14),
          const Text('تعذر تحميل بياناتك الآمنة'),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('إعادة المحاولة'),
          ),
        ],
      ),
    ),
  );
}
