import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../../auth/bloc/auth_bloc.dart';
import '../bloc/expense_detail_cubit.dart';

/// Expense detail screen showing header, per-unit breakdown, and admin actions.
class ExpenseDetailScreen extends StatelessWidget {
  final String expenseId;
  const ExpenseDetailScreen({
    super.key,
    required this.expenseId,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isAdmin = context.select<AuthBloc, bool>((bloc) {
      final s = bloc.state;
      return s is AuthAuthenticated && s.isAdmin;
    });

    return BlocConsumer<ExpenseDetailCubit, ExpenseDetailState>(
      listener: (context, state) {
        if (state is ExpenseDetailError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.message)),
          );
        } else if (state is ExpenseDetailDeleted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Expense deleted')), 
          );
          context.pop(true);
        }
      },
      builder: (context, state) {
        final isLoading =
            state is ExpenseDetailLoading || state is ExpenseDetailInitial;
        final expense = state is ExpenseDetailLoaded ? state.expense : null;
        final title = expense?['title'] as String? ?? '';
        final amount = double.tryParse(expense?['amount']?.toString() ?? '0') ?? 0;
        final splitType = expense?['split_type'] as String? ?? '';
        final categoryName =
            expense?['category_name'] as String? ?? expense?['category'] as String? ?? '';
        final date = expense?['expense_date'] as String? ?? '';
        final description = expense?['description'] as String? ?? '';
        final shares =
            (expense?['shares'] as List?)?.cast<Map<String, dynamic>>() ?? [];

        return Scaffold(
          key: const ValueKey('tc_s3_mob_expense_detail'),
          appBar: AppBar(
            title: const Text('Expense Details'),
            actions: isAdmin && expense != null
                ? [
                    IconButton(
                      icon: const Icon(Icons.edit_outlined),
                      tooltip: 'Edit',
                      onPressed: () {
                        // TODO: hook to edit flow
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.upload_file_outlined),
                      tooltip: 'Upload Bill',
                      onPressed: () {
                        // TODO: File picker + upload
                      },
                    ),
                    IconButton(
                      icon: Icon(Icons.delete_outline,
                          color: theme.colorScheme.error),
                      tooltip: 'Delete',
                      onPressed: () => _confirmDelete(context),
                    ),
                  ]
                : null,
          ),
          body: isLoading
              ? const Center(child: CircularProgressIndicator())
              : expense == null
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.error_outline,
                              size: 48, color: theme.colorScheme.error),
                          const SizedBox(height: 12),
                          Text('Expense not found',
                              style: TextStyle(color: theme.colorScheme.error)),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: () =>
                          context.read<ExpenseDetailCubit>().refresh(),
                      child: ListView(
                        padding: const EdgeInsets.all(16),
                        children: [
                          // ── Header card ──
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(title,
                                      style: theme.textTheme.headlineSmall
                                          ?.copyWith(fontWeight: FontWeight.w700)),
                                  const SizedBox(height: 12),
                                  Text(
                                    formatCurrency(amount),
                                    style: theme.textTheme.headlineMedium?.copyWith(
                                      fontWeight: FontWeight.w800,
                                      color: theme.colorScheme.primary,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 8,
                                    children: [
                                      if (splitType.isNotEmpty)
                                        Chip(
                                          label: Text(splitType),
                                          backgroundColor:
                                              theme.colorScheme.secondaryContainer,
                                        ),
                                      if (categoryName.isNotEmpty)
                                        Chip(
                                          avatar: Icon(Icons.category_outlined,
                                              size: 16,
                                              color: theme.colorScheme
                                                  .onTertiaryContainer),
                                          label: Text(categoryName),
                                          backgroundColor:
                                              theme.colorScheme.tertiaryContainer,
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      Icon(Icons.calendar_today_outlined,
                                          size: 16,
                                          color: theme.colorScheme.onSurfaceVariant),
                                      const SizedBox(width: 6),
                                      Text(date,
                                          style: TextStyle(
                                              color: theme.colorScheme.onSurfaceVariant)),
                                    ],
                                  ),
                                  if (description.isNotEmpty) ...[
                                    const SizedBox(height: 12),
                                    Text(description,
                                        style: TextStyle(
                                            color: theme.colorScheme.onSurfaceVariant)),
                                  ],
                                ],
                              ),
                            ),
                          ),

                          // ── Per-unit breakdown ──
                          if (shares.isNotEmpty) ...[
                            const SizedBox(height: 16),
                            Card(
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Per-Unit Breakdown',
                                        style: theme.textTheme.titleMedium
                                            ?.copyWith(fontWeight: FontWeight.w600)),
                                    const SizedBox(height: 12),
                                    Table(
                                      columnWidths: const {
                                        0: FlexColumnWidth(2),
                                        1: FlexColumnWidth(1),
                                      },
                                      border: TableBorder(
                                        horizontalInside: BorderSide(
                                          color: theme.dividerColor,
                                          width: 0.5,
                                        ),
                                      ),
                                      children: [
                                        TableRow(
                                          decoration: BoxDecoration(
                                            color:
                                                theme.colorScheme.surfaceContainerHighest,
                                          ),
                                          children: [
                                            Padding(
                                              padding: const EdgeInsets.all(10),
                                              child: Text('Unit',
                                                  style: TextStyle(
                                                      fontWeight: FontWeight.w600,
                                                      color: theme.colorScheme
                                                          .onSurfaceVariant)),
                                            ),
                                            Padding(
                                              padding: const EdgeInsets.all(10),
                                              child: Text('Share Amount',
                                                  textAlign: TextAlign.end,
                                                  style: TextStyle(
                                                      fontWeight: FontWeight.w600,
                                                      color: theme.colorScheme
                                                          .onSurfaceVariant)),
                                            ),
                                          ],
                                        ),
                                        ...shares.map((share) {
                                          final unitNumber =
                                              share['unit_number']?.toString() ?? '?';
                                          final shareAmount = double.tryParse(
                                                  share['share_amount']?.toString() ??
                                                      '0') ??
                                              0;
                                          return TableRow(children: [
                                            Padding(
                                              padding: const EdgeInsets.all(10),
                                              child: Text('Unit $unitNumber'),
                                            ),
                                            Padding(
                                              padding: const EdgeInsets.all(10),
                                              child: Text(
                                                formatCurrency(shareAmount),
                                                textAlign: TextAlign.end,
                                                style: const TextStyle(
                                                    fontWeight: FontWeight.w600),
                                              ),
                                            ),
                                          ]);
                                        }),
                                      ],
                                    ),
                                    const SizedBox(height: 12),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Row(
                                          children: [
                                            Text('Shares Total',
                                                style: theme.textTheme.titleSmall
                                                    ?.copyWith(
                                                        fontWeight: FontWeight.w700)),
                                            const SizedBox(width: 4),
                                            Tooltip(
                                              message:
                                                  'Individual shares are rounded up to the nearest 5 EGP. '
                                                  'The sum of shares may exceed the total expense amount.',
                                              child: Icon(Icons.info_outline,
                                                  size: 16,
                                                  color: theme.colorScheme
                                                      .onSurfaceVariant),
                                            ),
                                          ],
                                        ),
                                        Text(
                                          formatCurrency(_sharesTotal(shares)),
                                          style: theme.textTheme.titleSmall?.copyWith(
                                            fontWeight: FontWeight.w700,
                                            color: theme.colorScheme.primary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
        );
      },
    );
  }

  double _sharesTotal(List<Map<String, dynamic>> shares) {
    double total = 0;
    for (final share in shares) {
      total +=
          double.tryParse(share['share_amount']?.toString() ?? '0') ?? 0;
    }
    return total;
  }

  void _confirmDelete(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Expense'),
        content:
            const Text('Are you sure you want to delete this expense?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.danger,
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              context.read<ExpenseDetailCubit>().delete(expenseId);
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}
