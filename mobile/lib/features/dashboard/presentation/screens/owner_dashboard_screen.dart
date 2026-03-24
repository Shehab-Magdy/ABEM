import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../bloc/owner_dashboard_cubit.dart';

/// Owner dashboard screen with balance summary, donut chart, recent payments,
/// and claim unit section.
class OwnerDashboardScreen extends StatelessWidget {
  const OwnerDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      key: const ValueKey('tc_s5_mob_owner_dashboard'),
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.date_range_outlined),
            tooltip: 'Date Range',
            onPressed: () => _showDateRangeFilter(context),
          ),
        ],
      ),
      body: BlocBuilder<OwnerDashboardCubit, OwnerDashboardState>(
        builder: (context, state) {
          if (state is OwnerDashboardLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is OwnerDashboardError) {
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
                        context.read<OwnerDashboardCubit>().refresh(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final data = state is OwnerDashboardLoaded
              ? state.data
              : <String, dynamic>{};

          return RefreshIndicator(
            onRefresh: () =>
                context.read<OwnerDashboardCubit>().refresh(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _BalanceSummaryCard(data: data),
                const SizedBox(height: 16),
                _ExpenseBreakdownChart(data: data),
                const SizedBox(height: 16),
                _RecentPaymentsList(data: data),
                const SizedBox(height: 16),
                _ClaimUnitSection(),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showDateRangeFilter(BuildContext context) async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null && context.mounted) {
      final from =
          '${picked.start.year}-${picked.start.month.toString().padLeft(2, '0')}-${picked.start.day.toString().padLeft(2, '0')}';
      final to =
          '${picked.end.year}-${picked.end.month.toString().padLeft(2, '0')}-${picked.end.day.toString().padLeft(2, '0')}';
      context
          .read<OwnerDashboardCubit>()
          .load(dateFrom: from, dateTo: to);
    }
  }
}

// ── Balance Summary ─────────────────────────────────────────────────────────

class _BalanceSummaryCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _BalanceSummaryCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final balance =
        double.tryParse(data['balance']?.toString() ?? '0') ?? 0;

    Color chipColor;
    String chipLabel;
    if (balance < 0) {
      chipColor = AppColors.balanceCredit;
      chipLabel = 'Credit';
    } else if (balance == 0) {
      chipColor = AppColors.balanceSettled;
      chipLabel = 'Settled';
    } else {
      chipColor = AppColors.balanceOutstanding;
      chipLabel = 'Outstanding';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Your Balance',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: chipColor.withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(chipLabel,
                      style: TextStyle(
                          color: chipColor,
                          fontWeight: FontWeight.w600,
                          fontSize: 13)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              formatCurrency(balance.abs()),
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.w800,
                color: chipColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Expense Breakdown Donut ─────────────────────────────────────────────────

class _ExpenseBreakdownChart extends StatelessWidget {
  final Map<String, dynamic> data;
  const _ExpenseBreakdownChart({required this.data});

  static const _chartColors = [
    AppColors.primary,
    AppColors.accent,
    AppColors.purple,
    AppColors.orange,
    AppColors.balanceSettled,
    AppColors.balanceCredit,
    AppColors.neutralMid,
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final breakdown =
        (data['expense_breakdown'] as List?)
                ?.cast<Map<String, dynamic>>() ??
            [];

    if (breakdown.isEmpty) return const SizedBox.shrink();

    final total = breakdown.fold<double>(0, (prev, item) {
      return prev +
          (double.tryParse(item['amount']?.toString() ?? '0') ?? 0);
    });

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Expense Breakdown',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 16),
            SizedBox(
              height: 180,
              child: PieChart(
                PieChartData(
                  centerSpaceRadius: 40,
                  sectionsSpace: 2,
                  sections: List.generate(breakdown.length, (i) {
                    final item = breakdown[i];
                    final amount = double.tryParse(
                            item['amount']?.toString() ?? '0') ??
                        0;
                    final pct = total > 0 ? (amount / total * 100) : 0;
                    return PieChartSectionData(
                      value: amount,
                      title: '${pct.toStringAsFixed(0)}%',
                      titleStyle: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Colors.white),
                      color: _chartColors[i % _chartColors.length],
                      radius: 50,
                    );
                  }),
                ),
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              children: List.generate(breakdown.length, (i) {
                final item = breakdown[i];
                final name = item['category'] as String? ?? 'Other';
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 10,
                      height: 10,
                      decoration: BoxDecoration(
                        color: _chartColors[i % _chartColors.length],
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(name, style: const TextStyle(fontSize: 12)),
                  ],
                );
              }),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Recent Payments ─────────────────────────────────────────────────────────

class _RecentPaymentsList extends StatelessWidget {
  final Map<String, dynamic> data;
  const _RecentPaymentsList({required this.data});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final payments =
        (data['recent_payments'] as List?)
                ?.cast<Map<String, dynamic>>() ??
            [];

    if (payments.isEmpty) return const SizedBox.shrink();

    final last5 = payments.take(5).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Recent Payments',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            ...last5.map((p) {
              final date = p['payment_date'] as String? ?? '';
              final amount =
                  double.tryParse(p['amount']?.toString() ?? '0') ?? 0;
              final method = p['payment_method'] as String? ?? '';
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Icon(Icons.payment_outlined,
                        size: 18,
                        color: theme.colorScheme.onSurfaceVariant),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(date,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13)),
                          Text(method,
                              style: TextStyle(
                                  fontSize: 11,
                                  color: theme
                                      .colorScheme.onSurfaceVariant)),
                        ],
                      ),
                    ),
                    Text(
                      formatCurrency(amount),
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.primary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

// ── Claim Unit Section ────────────────────────────────────────────────────────

class _ClaimUnitSection extends StatefulWidget {
  @override
  State<_ClaimUnitSection> createState() => _ClaimUnitSectionState();
}

class _ClaimUnitSectionState extends State<_ClaimUnitSection> {
  bool _expanded = false;
  final _codeController = TextEditingController();

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Column(
        children: [
          ListTile(
            leading: Icon(Icons.add_home_outlined,
                color: theme.colorScheme.primary),
            title: const Text('Claim a Unit',
                style: TextStyle(fontWeight: FontWeight.w600)),
            subtitle: const Text('Enter an 8-character invite code'),
            trailing: IconButton(
              icon: Icon(
                _expanded
                    ? Icons.keyboard_arrow_up
                    : Icons.keyboard_arrow_down,
              ),
              onPressed: () => setState(() => _expanded = !_expanded),
            ),
            onTap: () => setState(() => _expanded = !_expanded),
          ),
          if (_expanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _codeController,
                      maxLength: 8,
                      textCapitalization: TextCapitalization.characters,
                      decoration: const InputDecoration(
                        hintText: 'ABCD1234',
                        counterText: '',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      style: const TextStyle(
                        letterSpacing: 3,
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  FilledButton(
                    onPressed: _codeController.text.length == 8
                        ? () {
                            // TODO: call claim cubit
                          }
                        : null,
                    child: const Text('Claim'),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
