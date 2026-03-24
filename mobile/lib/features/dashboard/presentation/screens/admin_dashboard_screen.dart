import 'dart:math';

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../bloc/admin_dashboard_cubit.dart';

/// Admin dashboard screen with summary cards, bar chart, and outstanding table.
class AdminDashboardScreen extends StatelessWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      key: const ValueKey('tc_s5_mob_admin_dashboard'),
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list_outlined),
            tooltip: 'Filter',
            onPressed: () => _showFilterSheet(context),
          ),
        ],
      ),
      body: BlocBuilder<AdminDashboardCubit, AdminDashboardState>(
        builder: (context, state) {
          if (state is AdminDashboardLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is AdminDashboardError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline,
                      size: 48, color: theme.colorScheme.error),
                  const SizedBox(height: 12),
                  Text(state.message,
                      style: TextStyle(color: theme.colorScheme.error)),
                  const SizedBox(height: 12),
                  FilledButton(
                    onPressed: () =>
                        context.read<AdminDashboardCubit>().refresh(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final data = state is AdminDashboardLoaded
              ? state.data
              : <String, dynamic>{};

          return RefreshIndicator(
            onRefresh: () =>
                context.read<AdminDashboardCubit>().refresh(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // ── Summary cards ──
                _SummaryCardsRow(data: data),
                const SizedBox(height: 16),

                // ── Payment coverage ──
                _PaymentCoverageCard(data: data),
                const SizedBox(height: 16),

                // ── Monthly bar chart ──
                _MonthlyBarChart(data: data),
                const SizedBox(height: 16),

                // ── Outstanding balances ──
                _OutstandingBalancesTable(data: data),
                const SizedBox(height: 16),

                // ── Banner ad placeholder ──
                Container(
                  height: 60,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  alignment: Alignment.center,
                  child: Text('Ad Placeholder',
                      style: TextStyle(
                          color: theme.colorScheme.onSurfaceVariant,
                          fontSize: 12)),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showFilterSheet(BuildContext context) {
    final theme = Theme.of(context);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Filter Dashboard',
                style: theme.textTheme.titleLarge
                    ?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            // Building selector placeholder
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(
                labelText: 'Building',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: '', child: Text('All Buildings')),
              ],
              value: '',
              onChanged: (_) {},
            ),
            const SizedBox(height: 16),
            // Date range placeholder
            Row(
              children: [
                Expanded(
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: 'From',
                      border: OutlineInputBorder(),
                      suffixIcon: Icon(Icons.calendar_today_outlined, size: 18),
                    ),
                    child: const Text(''),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: 'To',
                      border: OutlineInputBorder(),
                      suffixIcon: Icon(Icons.calendar_today_outlined, size: 18),
                    ),
                    child: const Text(''),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  Navigator.of(ctx).pop();
                  context.read<AdminDashboardCubit>().refresh();
                },
                child: const Text('Apply'),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

// ── Summary Cards ─────────────────────────────────────────────────────────────

class _SummaryCardsRow extends StatelessWidget {
  final Map<String, dynamic> data;
  const _SummaryCardsRow({required this.data});

  @override
  Widget build(BuildContext context) {
    final totalIncome =
        double.tryParse(data['total_income']?.toString() ?? '0') ?? 0;
    final totalExpenses =
        double.tryParse(data['total_expenses']?.toString() ?? '0') ?? 0;
    final overdueCount =
        int.tryParse(data['overdue_count']?.toString() ?? '0') ?? 0;
    final buildingCount =
        int.tryParse(data['building_count']?.toString() ?? '0') ?? 0;

    return SizedBox(
      height: 110,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          _SummaryCard(
            title: 'Total Income',
            value: formatCurrency(totalIncome),
            icon: Icons.trending_up_outlined,
            color: AppColors.balanceSettled,
          ),
          _SummaryCard(
            title: 'Total Expenses',
            value: formatCurrency(totalExpenses),
            icon: Icons.trending_down_outlined,
            color: AppColors.balanceOutstanding,
          ),
          _SummaryCard(
            title: 'Overdue',
            value: overdueCount.toString(),
            icon: Icons.warning_amber_outlined,
            color: overdueCount > 0 ? AppColors.danger : AppColors.neutralMid,
          ),
          _SummaryCard(
            title: 'Buildings',
            value: buildingCount.toString(),
            icon: Icons.apartment_outlined,
            color: AppColors.primary,
          ),
        ],
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;
  const _SummaryCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: 150,
      margin: const EdgeInsets.only(right: 12),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: color, size: 24),
              const Spacer(),
              Text(value,
                  style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700, color: color)),
              const SizedBox(height: 2),
              Text(title,
                  style: TextStyle(
                      fontSize: 11,
                      color: theme.colorScheme.onSurfaceVariant)),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Payment Coverage ──────────────────────────────────────────────────────────

class _PaymentCoverageCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _PaymentCoverageCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final coverage =
        double.tryParse(data['payment_coverage']?.toString() ?? '0') ?? 0;
    final pct = (coverage / 100).clamp(0.0, 1.0);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Payment Coverage',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
                Text('${coverage.toStringAsFixed(1)}%',
                    style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: theme.colorScheme.primary)),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: pct,
                minHeight: 10,
                backgroundColor: theme.colorScheme.surfaceContainerHighest,
                color: theme.colorScheme.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Monthly Bar Chart ─────────────────────────────────────────────────────────

class _MonthlyBarChart extends StatelessWidget {
  final Map<String, dynamic> data;
  const _MonthlyBarChart({required this.data});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final monthlyData =
        (data['monthly'] as List?)?.cast<Map<String, dynamic>>() ?? [];

    if (monthlyData.isEmpty) return const SizedBox.shrink();

    final maxVal = monthlyData.fold<double>(0, (prev, m) {
      final income =
          double.tryParse(m['income']?.toString() ?? '0') ?? 0;
      final expenses =
          double.tryParse(m['expenses']?.toString() ?? '0') ?? 0;
      return max(prev, max(income, expenses));
    });

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Monthly Overview',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Row(
              children: [
                _LegendDot(
                    color: AppColors.balanceSettled, label: 'Income'),
                const SizedBox(width: 16),
                _LegendDot(
                    color: AppColors.balanceOutstanding,
                    label: 'Expenses'),
              ],
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  maxY: maxVal * 1.2,
                  barTouchData: BarTouchData(enabled: true),
                  gridData: const FlGridData(show: false),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    leftTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          final idx = value.toInt();
                          if (idx < 0 || idx >= monthlyData.length) {
                            return const SizedBox.shrink();
                          }
                          final label =
                              monthlyData[idx]['month']?.toString() ?? '';
                          return SideTitleWidget(
                            meta: meta,
                            child: Text(label,
                                style: const TextStyle(fontSize: 10)),
                          );
                        },
                      ),
                    ),
                  ),
                  barGroups: List.generate(monthlyData.length, (i) {
                    final m = monthlyData[i];
                    final income = double.tryParse(
                            m['income']?.toString() ?? '0') ??
                        0;
                    final expenses = double.tryParse(
                            m['expenses']?.toString() ?? '0') ??
                        0;
                    return BarChartGroupData(
                      x: i,
                      barRods: [
                        BarChartRodData(
                          toY: income,
                          color: AppColors.balanceSettled,
                          width: 8,
                          borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(4)),
                        ),
                        BarChartRodData(
                          toY: expenses,
                          color: AppColors.balanceOutstanding,
                          width: 8,
                          borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(4)),
                        ),
                      ],
                    );
                  }),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}

// ── Outstanding Balances ──────────────────────────────────────────────────────

class _OutstandingBalancesTable extends StatefulWidget {
  final Map<String, dynamic> data;
  const _OutstandingBalancesTable({required this.data});

  @override
  State<_OutstandingBalancesTable> createState() =>
      _OutstandingBalancesTableState();
}

class _OutstandingBalancesTableState
    extends State<_OutstandingBalancesTable> {
  bool _sortAscending = true;
  int _sortColumnIndex = 0;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final outstanding =
        (widget.data['outstanding_balances'] as List?)
                ?.cast<Map<String, dynamic>>() ??
            [];

    if (outstanding.isEmpty) return const SizedBox.shrink();

    final sorted = List<Map<String, dynamic>>.from(outstanding);
    if (_sortColumnIndex == 0) {
      sorted.sort((a, b) {
        final aVal = a['unit_number']?.toString() ?? '';
        final bVal = b['unit_number']?.toString() ?? '';
        return _sortAscending
            ? aVal.compareTo(bVal)
            : bVal.compareTo(aVal);
      });
    } else {
      sorted.sort((a, b) {
        final aVal =
            double.tryParse(a['balance']?.toString() ?? '0') ?? 0;
        final bVal =
            double.tryParse(b['balance']?.toString() ?? '0') ?? 0;
        return _sortAscending
            ? aVal.compareTo(bVal)
            : bVal.compareTo(aVal);
      });
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Outstanding Balances',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                sortColumnIndex: _sortColumnIndex,
                sortAscending: _sortAscending,
                columns: [
                  DataColumn(
                    label: const Text('Unit'),
                    onSort: (i, asc) => setState(() {
                      _sortColumnIndex = i;
                      _sortAscending = asc;
                    }),
                  ),
                  DataColumn(
                    label: const Text('Owner'),
                    onSort: (_, __) {},
                  ),
                  DataColumn(
                    numeric: true,
                    label: const Text('Balance'),
                    onSort: (i, asc) => setState(() {
                      _sortColumnIndex = i;
                      _sortAscending = asc;
                    }),
                  ),
                ],
                rows: sorted.map((item) {
                  final balance = double.tryParse(
                          item['balance']?.toString() ?? '0') ??
                      0;
                  return DataRow(cells: [
                    DataCell(Text(
                        'Unit ${item['unit_number'] ?? '?'}')),
                    DataCell(
                        Text(item['owner_name'] as String? ?? '-')),
                    DataCell(Text(
                      formatCurrency(balance),
                      style: TextStyle(
                        color: AppColors.balanceOutstanding,
                        fontWeight: FontWeight.w600,
                      ),
                    )),
                  ]);
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
