import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:share_plus/share_plus.dart' show Share;

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../../auth/bloc/auth_bloc.dart';
import '../bloc/apartment_detail_cubit.dart';

/// Apartment detail screen showing balance card, owner info, status,
/// and invite generation.
class ApartmentDetailScreen extends StatelessWidget {
  final String apartmentId;
  const ApartmentDetailScreen({super.key, required this.apartmentId});

  @override
  Widget build(BuildContext context) {
    final isAdmin = context.select<AuthBloc, bool>((bloc) {
      final s = bloc.state;
      return s is AuthAuthenticated && s.isAdmin;
    });

    return Scaffold(
      key: const ValueKey('tc_s2_mob_apartment_detail'),
      appBar: AppBar(title: const Text('Unit Details')),
      body: BlocBuilder<ApartmentDetailCubit, ApartmentDetailState>(
        builder: (context, state) {
          if (state is ApartmentDetailLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is ApartmentDetailError) {
            return Center(child: Text(state.message));
          }

          final apartment = state is ApartmentDetailLoaded
              ? state.apartment
              : state is ApartmentInviteGenerated
                  ? state.apartment
                  : null;
          final balance = state is ApartmentDetailLoaded
              ? state.balance
              : state is ApartmentInviteGenerated
                  ? state.balance
                  : null;

          if (apartment == null) return const SizedBox.shrink();

          return RefreshIndicator(
            onRefresh: () =>
                context.read<ApartmentDetailCubit>().load(apartmentId),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _UnitHeader(apartment: apartment),
                const SizedBox(height: 16),
                _BalanceCard(balance: balance),
                const SizedBox(height: 16),
                _OwnerSection(apartment: apartment),
                if (isAdmin) ...[
                  const SizedBox(height: 16),
                  _StatusSection(
                    apartment: apartment,
                    onStatusChanged: (status) {
                      context
                          .read<ApartmentDetailCubit>()
                          .updateStatus(apartmentId, status);
                    },
                  ),
                  const SizedBox(height: 16),
                  _InviteSection(
                    apartmentId: apartmentId,
                    inviteCode: state is ApartmentInviteGenerated
                        ? state.code
                        : null,
                    expiresAt: state is ApartmentInviteGenerated
                        ? state.expiresAt
                        : null,
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}

class _UnitHeader extends StatelessWidget {
  final Map<String, dynamic> apartment;
  const _UnitHeader({required this.apartment});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final unitNumber = apartment['unit_number'] ?? '?';
    final floor = apartment['floor'] ?? '?';
    final type = apartment['unit_type'] ?? apartment['type'] ?? 'apartment';
    final sizeSqm = apartment['size_sqm'];
    final isStore = type == 'store';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 28,
              backgroundColor: isStore
                  ? AppColors.accentLight
                  : theme.colorScheme.primaryContainer,
              child: Icon(
                isStore ? Icons.store_outlined : Icons.door_front_door_outlined,
                color: isStore
                    ? AppColors.accentDark
                    : theme.colorScheme.onPrimaryContainer,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Unit $unitNumber',
                      style: theme.textTheme.titleLarge
                          ?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 4),
                  Text(
                    'Floor $floor${sizeSqm != null ? ' · $sizeSqm m²' : ''}',
                    style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
                  ),
                ],
              ),
            ),
            Chip(
              label: Text(isStore ? 'Store' : 'Apartment'),
              backgroundColor: isStore
                  ? AppColors.accentLight
                  : theme.colorScheme.primaryContainer,
            ),
          ],
        ),
      ),
    );
  }
}

class _BalanceCard extends StatelessWidget {
  final Map<String, dynamic>? balance;
  const _BalanceCard({this.balance});

  @override
  Widget build(BuildContext context) {
    if (balance == null) return const SizedBox.shrink();
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final currentBalance =
        double.tryParse(balance!['balance']?.toString() ?? '0') ?? 0;
    final totalOwed =
        double.tryParse(balance!['total_owed']?.toString() ?? '0') ?? 0;
    final totalPaid =
        double.tryParse(balance!['total_paid']?.toString() ?? '0') ?? 0;
    final overdueAmount =
        double.tryParse(balance!['overdue_amount']?.toString() ?? '0') ?? 0;
    final upcomingAmount =
        double.tryParse(balance!['upcoming_amount']?.toString() ?? '0') ?? 0;

    Color chipColor;
    String chipLabel;
    if (currentBalance < 0) {
      chipColor = AppColors.balanceCredit;
      chipLabel = 'Credit';
    } else if (currentBalance == 0) {
      chipColor = AppColors.balanceSettled;
      chipLabel = 'Settled';
    } else {
      chipColor = AppColors.balanceOutstanding;
      chipLabel = 'Outstanding';
    }

    return Card(
      key: const ValueKey('tc_s2_mob_balance_card'),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Balance Summary',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
                Chip(
                  label: Text(chipLabel),
                  labelStyle: TextStyle(
                    color: chipColor,
                    fontWeight: FontWeight.w600,
                  ),
                  backgroundColor: chipColor.withOpacity(0.1),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _BalanceStat(
                    label: 'Total Owed',
                    value: formatCurrency(totalOwed),
                    color: AppColors.balanceOutstanding,
                  ),
                ),
                Expanded(
                  child: _BalanceStat(
                    label: 'Total Paid',
                    value: formatCurrency(totalPaid),
                    color: AppColors.balanceSettled,
                  ),
                ),
                Expanded(
                  child: _BalanceStat(
                    label: 'Current',
                    value: formatCurrency(currentBalance.abs()),
                    color: chipColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                color: colorScheme.surfaceVariant,
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Reminder',
                      style: theme.textTheme.labelLarge
                          ?.copyWith(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 6),
                  Text(
                    'Overdue: ${formatCurrency(overdueAmount)} · Upcoming: ${formatCurrency(upcomingAmount)}',
                    style: TextStyle(color: colorScheme.onSurfaceVariant),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BalanceStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _BalanceStat({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: TextStyle(
                fontSize: 16, fontWeight: FontWeight.w700, color: color)),
        const SizedBox(height: 4),
        Text(label,
            style: TextStyle(
                fontSize: 12,
                color: Theme.of(context).colorScheme.onSurfaceVariant)),
      ],
    );
  }
}

class _OwnerSection extends StatelessWidget {
  final Map<String, dynamic> apartment;
  const _OwnerSection({required this.apartment});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final ownerNames =
        (apartment['owner_names'] as List?)?.cast<String>() ?? [];
    final status = apartment['status'] as String? ?? 'vacant';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('Owner(s)',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(width: 8),
                Chip(
                  label: Text(status.toUpperCase()),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (ownerNames.isEmpty)
              Row(
                children: [
                  Icon(Icons.person_off_outlined,
                      color: theme.colorScheme.onSurfaceVariant, size: 20),
                  const SizedBox(width: 8),
                  Text(status == 'vacant' ? 'Vacant — no owner' : 'No owner',
                      style: TextStyle(
                          color: theme.colorScheme.onSurfaceVariant)),
                ],
              )
            else
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: ownerNames.map((name) {
                  final initials = name.isNotEmpty
                      ? name
                          .split(' ')
                          .take(2)
                          .map((w) => w.isNotEmpty ? w[0].toUpperCase() : '')
                          .join()
                      : '?';
                  return Chip(
                    avatar: CircleAvatar(
                      backgroundColor: theme.colorScheme.primary,
                      child: Text(
                        initials,
                        style: TextStyle(
                          color: theme.colorScheme.onPrimary,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    label: Text(name),
                  );
                }).toList(),
              ),
          ],
        ),
      ),
    );
  }
}

class _StatusSection extends StatelessWidget {
  final Map<String, dynamic> apartment;
  final void Function(String status) onStatusChanged;
  const _StatusSection(
      {required this.apartment, required this.onStatusChanged});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final current = apartment['status'] as String? ?? 'vacant';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Status',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'occupied', label: Text('Occupied')),
                ButtonSegment(value: 'vacant', label: Text('Vacant')),
                ButtonSegment(
                    value: 'under_maintenance', label: Text('Maintenance')),
              ],
              selected: {current},
              onSelectionChanged: (set) => onStatusChanged(set.first),
            ),
          ],
        ),
      ),
    );
  }
}

class _InviteSection extends StatelessWidget {
  final String apartmentId;
  final String? inviteCode;
  final String? expiresAt;
  const _InviteSection({
    required this.apartmentId,
    this.inviteCode,
    this.expiresAt,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Invite Owner',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            if (inviteCode != null) ...[
              // Show generated code
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  children: [
                    Text('Registration Code',
                        style: TextStyle(
                            color: colorScheme.onPrimaryContainer,
                            fontSize: 12)),
                    const SizedBox(height: 8),
                    SelectableText(
                      inviteCode!,
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 4,
                        fontFamily: 'monospace',
                        color: colorScheme.onPrimaryContainer,
                      ),
                    ),
                    if (expiresAt != null) ...[
                      const SizedBox(height: 8),
                      Text('Valid for 30 days',
                          style: TextStyle(
                              fontSize: 12,
                              color: colorScheme.onPrimaryContainer
                                  .withAlpha(180))),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.copy, size: 18),
                      label: const Text('Copy'),
                      onPressed: () {
                        Clipboard.setData(ClipboardData(text: inviteCode!));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Code copied!')),
                        );
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton.icon(
                      icon: const Icon(Icons.share, size: 18),
                      label: const Text('Share'),
                      onPressed: () {
                        Share.share(
                          'Your ABEM registration code: $inviteCode\n'
                          'Download the app and enter this code to join.',
                        );
                      },
                    ),
                  ),
                ],
              ),
            ] else ...[
              Text(
                'Generate a registration code to invite an owner to this unit.',
                style: TextStyle(
                    color: colorScheme.onSurfaceVariant, fontSize: 13),
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                key: const ValueKey('tc_s2_mob_generate_invite_btn'),
                icon: const Icon(Icons.person_add_outlined),
                label: const Text('Generate Invite Code'),
                onPressed: () {
                  context
                      .read<ApartmentDetailCubit>()
                      .generateInvite(apartmentId);
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}
