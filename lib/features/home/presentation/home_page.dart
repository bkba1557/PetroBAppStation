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
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 108),
      children: [
        Row(
          children: [
            Container(
              width: 46,
              height: 46,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF19B98E), Color(0xFF087F6E)],
                ),
                borderRadius: BorderRadius.circular(15),
                boxShadow: const [
                  BoxShadow(color: Color(0x3320C997), blurRadius: 16),
                ],
              ),
              child: Text(
                name.isEmpty ? 'N' : name.characters.first,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(greeting, style: Theme.of(context).textTheme.bodySmall),
                  Text(
                    name.isEmpty ? 'عميل PetroB' : name,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
            IconButton.filledTonal(
              onPressed: () {},
              tooltip: 'الإشعارات',
              icon: const Badge(child: Icon(Icons.notifications_none_rounded)),
            ),
          ],
        ),
        const SizedBox(height: 18),
        BrandedWalletCard(
          available: money(dashboard.wallet['available']),
          reserved: money(dashboard.wallet['held']),
          updatedLabel:
              'آخر تحديث ${_shortDate(dashboard.wallet['updatedAt'])}',
          onTopUp: () => context.push(AppRoutes.walletTopUp),
        ),
        const SizedBox(height: 22),
        const _SectionTitle('اختصارات سريعة'),
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            _Quick(
              Icons.local_gas_station,
              'ابدأ التعبئة',
              () => context.push(AppRoutes.scan),
            ),
            _Quick(
              Icons.qr_code_scanner,
              'مسح QR',
              () => context.push(AppRoutes.scan),
            ),
            _Quick(
              Icons.near_me_outlined,
              'المحطات القريبة',
              () => context.go(AppRoutes.stations),
            ),
            _Quick(
              Icons.directions_car_outlined,
              'إضافة مركبة',
              () => context.push(AppRoutes.vehicles),
            ),
            _Quick(
              Icons.receipt_long_outlined,
              'سجل العمليات',
              () => context.push(AppRoutes.transactions),
            ),
          ],
        ),
        const SizedBox(height: 22),
        const _SectionTitle('ملخص آخر 30 يومًا'),
        const SizedBox(height: 12),
        GridView.count(
          crossAxisCount: MediaQuery.sizeOf(context).width > 600 ? 4 : 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          childAspectRatio: 1.70,
          children: [
            _Metric(
              'التعبئات',
              '${dashboard.summary['totalFuelings']}',
              Icons.ev_station_outlined,
            ),
            _Metric(
              'اللترات',
              (dashboard.summary['totalLiters'] as num).toStringAsFixed(3),
              Icons.water_drop_outlined,
            ),
            _Metric(
              'الإنفاق',
              money(dashboard.summary['totalSpent']),
              Icons.payments_outlined,
            ),
            _Metric(
              'متوسط العملية',
              money(dashboard.summary['averageTransaction']),
              Icons.analytics_outlined,
            ),
            _Metric(
              'المحطات',
              '${dashboard.summary['stationsUsed']}',
              Icons.location_on_outlined,
            ),
            _Metric(
              'المركبات',
              '${dashboard.summary['vehiclesUsed']}',
              Icons.directions_car_outlined,
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

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;
  @override
  Widget build(BuildContext c) => Row(
    children: [
      Container(
        width: 4,
        height: 18,
        decoration: BoxDecoration(
          color: Theme.of(c).colorScheme.primary,
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      const SizedBox(width: 9),
      Text(
        text,
        style: Theme.of(
          c,
        ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
      ),
    ],
  );
}

class _Quick extends StatelessWidget {
  const _Quick(this.icon, this.label, this.tap);
  final IconData icon;
  final String label;
  final VoidCallback tap;
  @override
  Widget build(BuildContext c) => SizedBox(
    width: (MediaQuery.sizeOf(c).width - 46) / 2,
    child: Material(
      color: Theme.of(c).colorScheme.surface.withValues(alpha: 0.92),
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        onTap: tap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(11),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: Theme.of(
                c,
              ).colorScheme.outlineVariant.withValues(alpha: 0.55),
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: Theme.of(c).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Icon(
                  icon,
                  size: 18,
                  color: Theme.of(c).colorScheme.onPrimaryContainer,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  label,
                  maxLines: 2,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value, this.icon);
  final String label, value;
  final IconData icon;
  @override
  Widget build(BuildContext c) => Card(
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(17),
      side: BorderSide(
        color: Theme.of(c).colorScheme.outlineVariant.withValues(alpha: 0.55),
      ),
    ),
    child: Padding(
      padding: const EdgeInsets.all(10),
      child: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: Theme.of(c).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(11),
            ),
            child: Icon(
              icon,
              size: 18,
              color: Theme.of(c).colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(
                    c,
                  ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w800),
                ),
                Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(c).textTheme.labelSmall,
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
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
