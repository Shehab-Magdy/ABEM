import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../../auth/bloc/auth_bloc.dart';
import '../bloc/expense_list_cubit.dart';

/// Expense list screen with filter chips, pagination, and admin FAB.
class ExpenseListScreen extends StatefulWidget {
  const ExpenseListScreen({super.key});

  @override
  State<ExpenseListScreen> createState() => _ExpenseListScreenState();
}

class _ExpenseListScreenState extends State<ExpenseListScreen> {
  final ScrollController _scrollController = ScrollController();
  String _selectedFilter = 'All';

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<ExpenseListCubit>().loadExpenses();
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      context.read<ExpenseListCubit>().loadMore();
    }
  }

  List<Map<String, dynamic>> _applyFilter(
    List<Map<String, dynamic>> expenses,
  ) {
    switch (_selectedFilter) {
      case 'Recurring':
        return expenses.where((e) => e['is_recurring'] == true).toList();
      case 'Pending':
        return expenses
            .where((e) => (e['status'] as String? ?? '').toLowerCase() == 'pending')
            .toList();
      case 'Paid':
        return expenses
            .where((e) => (e['status'] as String? ?? '').toLowerCase() == 'paid')
            .toList();
      case 'Overdue':
        return expenses
            .where((e) => (e['status'] as String? ?? '').toLowerCase() == 'overdue')
            .toList();
      default:
        return expenses;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isAdmin = context.select<AuthBloc, bool>((bloc) {
      final s = bloc.state;
      return s is AuthAuthenticated && s.isAdmin;
    });

    return Scaffold(
      key: const ValueKey('tc_s3_mob_expense_list'),
      appBar: AppBar(title: const Text('Expenses')),
      floatingActionButton: isAdmin
          ? FloatingActionButton.extended(
              key: const ValueKey('tc_s3_mob_add_expense_fab'),
              icon: const Icon(Icons.add),
              label: const Text('New Expense'),
              onPressed: () async {
                final created = await context.push<bool>(Routes.adminExpenseCreate);
                if (created == true && mounted) {
                  context.read<ExpenseListCubit>().refresh();
                }
              },
            )
          : null,
      body: Column(
        children: [
          // ── Filter chips ──
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: ['All', 'Recurring', 'Pending', 'Paid', 'Overdue']
                  .map((label) {
                final isSelected = _selectedFilter == label;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(label),
                    selected: isSelected,
                    onSelected: (_) => setState(() => _selectedFilter = label),
                  ),
                );
              }).toList(),
            ),
          ),

          // ── List ──
          Expanded(
            child: BlocBuilder<ExpenseListCubit, ExpenseListState>(
              builder: (context, state) {
                if (state is ExpenseListLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is ExpenseListError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error_outline,
                            size: 48, color: theme.colorScheme.error),
                        const SizedBox(height: 12),
                        Text(state.message,
                            style:
                                TextStyle(color: theme.colorScheme.error)),
                        const SizedBox(height: 12),
                        FilledButton(
                          onPressed: () =>
                              context.read<ExpenseListCubit>().refresh(),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  );
                }

                final expenses = state is ExpenseListLoaded
                    ? _applyFilter(state.expenses)
                    : <Map<String, dynamic>>[];
                final hasMore = state is ExpenseListLoaded && state.hasMore;

                if (expenses.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.receipt_long_outlined,
                            size: 64,
                            color: theme.colorScheme.onSurfaceVariant),
                        const SizedBox(height: 16),
                        Text('No expenses found.',
                            style: theme.textTheme.titleMedium?.copyWith(
                                color:
                                    theme.colorScheme.onSurfaceVariant)),
                      ],
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () =>
                      context.read<ExpenseListCubit>().refresh(),
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: expenses.length + (hasMore ? 1 : 0),
                    itemBuilder: (ctx, i) {
                      if (i >= expenses.length) {
                        return const Padding(
                          padding: EdgeInsets.symmetric(vertical: 16),
                          child: Center(child: CircularProgressIndicator()),
                        );
                      }
                      final expense = expenses[i];
                      return _ExpenseCard(
                        key: ValueKey('tc_s3_mob_expense_card_${expense['id']}'),
                        expense: expense,
                        isAdmin: isAdmin,
                        onTap: () async {
                          final id = expense['id']?.toString();
                          if (id == null) return;
                          final route =
                              isAdmin ? Routes.adminExpenseDetail(id) : Routes.ownerExpenseDetail(id);
                          final deleted = await context.push<bool>(route);
                          if (deleted == true && mounted) {
                            context.read<ExpenseListCubit>().refresh();
                          }
                        },
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ExpenseCard extends StatelessWidget {
  final Map<String, dynamic> expense;
  final bool isAdmin;
  final VoidCallback onTap;
  const _ExpenseCard({super.key, required this.expense, required this.isAdmin, required this.onTap});

  IconData _categoryIcon(String? category) {
    switch (category?.toLowerCase()) {
      case 'maintenance':
        return Icons.build_outlined;
      case 'utilities':
        return Icons.bolt_outlined;
      case 'cleaning':
        return Icons.cleaning_services_outlined;
      case 'security':
        return Icons.security_outlined;
      case 'elevator':
        return Icons.elevator_outlined;
      default:
        return Icons.receipt_long_outlined;
    }
  }

  Color _categoryColor(String? category) {
    switch (category?.toLowerCase()) {
      case 'maintenance':
        return AppColors.orange;
      case 'utilities':
        return AppColors.accent;
      case 'cleaning':
        return AppColors.primaryLight;
      case 'security':
        return AppColors.purple;
      case 'elevator':
        return AppColors.neutralMid;
      default:
        return AppColors.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final title = expense['title'] as String? ?? '';
    final amount =
        double.tryParse(expense['amount']?.toString() ?? '0') ?? 0;
    final date = expense['expense_date'] as String? ?? '';
    final categoryName =
        expense['category_name'] as String? ?? expense['category'] as String?;
    final status = expense['status'] as String? ?? '';
    final isRecurring = expense['is_recurring'] == true;
    final splitType = expense['split_type'] as String? ?? '';
    final iconColor = _categoryColor(categoryName);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: iconColor.withAlpha(30),
                child: Icon(
                  _categoryIcon(categoryName),
                  color: iconColor,
                  size: 22,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 8,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text(date,
                            style: TextStyle(
                                fontSize: 12,
                                color:
                                    theme.colorScheme.onSurfaceVariant)),
                        if (isRecurring)
                          Chip(
                            label: const Text('Recurring'),
                            visualDensity: VisualDensity.compact,
                            backgroundColor:
                                theme.colorScheme.surfaceContainerHighest,
                          ),
                        if (splitType.isNotEmpty)
                          Chip(
                            label: Text(_splitLabels[splitType] ?? splitType),
                            visualDensity: VisualDensity.compact,
                            backgroundColor:
                                theme.colorScheme.surfaceContainerHighest,
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    formatCurrency(amount),
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  if (status.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: _statusColor(status, theme)
                            .withAlpha(30),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        status.toUpperCase(),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: _statusColor(status, theme),
                        ),
                      ),
                    ),
                  if (!isAdmin && expense['my_share_amount'] != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(
                        'Your share: ${formatCurrency(double.tryParse(expense['my_share_amount'].toString()) ?? 0)}',
                        style: TextStyle(
                          fontSize: 11,
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
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

  Color _statusColor(String status, ThemeData theme) {
    switch (status.toLowerCase()) {
      case 'approved':
      case 'active':
      case 'paid':
        return AppColors.balanceSettled;
      case 'pending':
      case 'draft':
        return AppColors.accent;
      case 'overdue':
        return AppColors.balanceOutstanding;
      case 'rejected':
        return AppColors.danger;
      default:
        return theme.colorScheme.outline;
    }
  }
}

const Map<String, String> _splitLabels = {
  'equal_all': 'Equal · All Units',
  'equal_apartments': 'Equal · Apartments',
  'equal_stores': 'Equal · Stores',
  'custom': 'Custom Split',
};
