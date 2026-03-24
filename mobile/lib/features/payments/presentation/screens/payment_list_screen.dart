import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../../auth/bloc/auth_bloc.dart';
import '../bloc/payment_list_cubit.dart';

/// Payment list screen with payment cards, admin FAB, and receipt navigation.
class PaymentListScreen extends StatelessWidget {
  const PaymentListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isAdmin = context.select<AuthBloc, bool>((bloc) {
      final s = bloc.state;
      return s is AuthAuthenticated && s.isAdmin;
    });

    return Scaffold(
      key: const ValueKey('tc_s4_mob_payment_list'),
      appBar: AppBar(title: const Text('Payments')),
      floatingActionButton: isAdmin
          ? FloatingActionButton(
              onPressed: () => context.push('/admin/payments/record'),
              child: const Icon(Icons.add),
            )
          : null,
      body: BlocBuilder<PaymentListCubit, PaymentListState>(
        builder: (context, state) {
          if (state is PaymentListLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is PaymentListError) {
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
                        context.read<PaymentListCubit>().refresh(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final payments = state is PaymentListLoaded
              ? state.payments
              : <Map<String, dynamic>>[];

          if (payments.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.payment_outlined,
                      size: 64,
                      color: theme.colorScheme.onSurfaceVariant),
                  const SizedBox(height: 16),
                  Text('No payments found.',
                      style: theme.textTheme.titleMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant)),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => context.read<PaymentListCubit>().refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: payments.length,
              itemBuilder: (ctx, i) {
                final payment = payments[i];
                return _PaymentCard(
                  payment: payment,
                  onTap: () {
                    final id = payment['id']?.toString() ?? '';
                    if (isAdmin) {
                      context.push('/admin/payments/$id/receipt');
                    } else {
                      context.push('/owner/payments/$id/receipt');
                    }
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _PaymentCard extends StatelessWidget {
  final Map<String, dynamic> payment;
  final VoidCallback onTap;
  const _PaymentCard({required this.payment, required this.onTap});

  IconData _methodIcon(String? method) {
    switch (method?.toLowerCase()) {
      case 'cash':
        return Icons.money_outlined;
      case 'bank_transfer':
      case 'bank transfer':
        return Icons.account_balance_outlined;
      case 'mobile_wallet':
      case 'mobile wallet':
        return Icons.phone_android_outlined;
      case 'check':
      case 'cheque':
        return Icons.description_outlined;
      default:
        return Icons.payment_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final date = payment['payment_date'] as String? ?? '';
    final amount =
        double.tryParse(payment['amount']?.toString() ?? '0') ?? 0;
    final method = payment['payment_method'] as String? ?? '';
    final balanceAfter =
        double.tryParse(payment['balance_after']?.toString() ?? '0') ?? 0;

    Color balanceColor;
    if (balanceAfter < 0) {
      balanceColor = AppColors.balanceCredit;
    } else if (balanceAfter == 0) {
      balanceColor = AppColors.balanceSettled;
    } else {
      balanceColor = AppColors.balanceOutstanding;
    }

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
                backgroundColor: theme.colorScheme.tertiaryContainer,
                child: Icon(
                  _methodIcon(method),
                  color: theme.colorScheme.onTertiaryContainer,
                  size: 22,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(date,
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    Text(method,
                        style: TextStyle(
                            fontSize: 12,
                            color: theme.colorScheme.onSurfaceVariant)),
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
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: balanceColor.withAlpha(30),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      'Bal: ${formatCurrency(balanceAfter)}',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: balanceColor,
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
}
