import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/routes.dart';
import '../bloc/building_detail_cubit.dart';
import '../bloc/building_form_cubit.dart';
import '../widgets/building_form_sheet.dart';

class BuildingDetailScreen extends StatelessWidget {
  final String buildingId;
  const BuildingDetailScreen({super.key, required this.buildingId});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return BlocConsumer<BuildingDetailCubit, BuildingDetailState>(
      listener: (context, state) {
        if (state is BuildingDetailError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.message)),
          );
        }
      },
      builder: (context, state) {
        final buildingName = state is BuildingDetailLoaded
            ? state.building['name']?.toString()
            : 'Building';

        return Scaffold(
          key: ValueKey('tc_s2_mob_building_detail_$buildingId'),
          appBar: AppBar(
            title: Text(buildingName ?? 'Building'),
            actions: [
              IconButton(
                tooltip: 'Edit Building',
                icon: const Icon(Icons.edit_outlined),
                onPressed: state is BuildingDetailLoaded
                    ? () => _openFormSheet(context, state.building)
                    : null,
              ),
              PopupMenuButton<String>(
                onSelected: (action) async {
                  if (action == 'toggle') {
                    final message =
                        await context.read<BuildingDetailCubit>().toggleActive();
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(
                            message ?? 'Status updated successfully',
                          ),
                          backgroundColor:
                              message == null ? null : colorScheme.error,
                        ),
                      );
                    }
                  } else if (action == 'refresh') {
                    await context.read<BuildingDetailCubit>().refresh();
                  }
                },
                itemBuilder: (_) => [
                  PopupMenuItem(
                    value: 'toggle',
                    child: Text(
                      state is BuildingDetailLoaded &&
                              (state.building['is_active'] as bool? ?? true)
                          ? 'Deactivate'
                          : 'Activate',
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'refresh',
                    child: Text('Refresh'),
                  ),
                ],
              ),
            ],
          ),
          body: _buildBody(context, state),
        );
      },
    );
  }

  Widget _buildBody(BuildContext context, BuildingDetailState state) {
    if (state is BuildingDetailLoading || state is BuildingDetailInitial) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state is BuildingDetailError) {
      return _ErrorView(
        message: state.message,
        onRetry: () =>
            context.read<BuildingDetailCubit>().load(buildingId),
      );
    }

    if (state is! BuildingDetailLoaded) {
      return const SizedBox.shrink();
    }

    final building = state.building;
    final occupancyRate = _parseDouble(building['occupancy_rate']) ??
        _computeOccupancyRate(building);
    final occupancyPercent = (occupancyRate * 100).clamp(0, 100).toStringAsFixed(0);

    return RefreshIndicator(
      onRefresh: () => context.read<BuildingDetailCubit>().refresh(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _SummaryCard(building: building),
          const SizedBox(height: 16),
          _StatsGrid(building: building, occupancyPercent: occupancyPercent),
          const SizedBox(height: 16),
          _ActionSection(
            building: building,
            buildingId: buildingId,
          ),
          const SizedBox(height: 24),
          _DetailsCard(building: building),
          const SizedBox(height: 16),
          _NotesCard(building: building),
        ],
      ),
    );
  }

  double _computeOccupancyRate(Map<String, dynamic> building) {
    final total = (building['num_apartments'] as num?)?.toDouble() ?? 0;
    if (total <= 0) return 0;
    final occupied =
        (building['num_occupied_apartments'] as num?)?.toDouble() ?? total;
    return (occupied / total).clamp(0, 1);
  }

  double? _parseDouble(dynamic value) {
    if (value == null) return null;
    return double.tryParse(value.toString());
  }

  Future<void> _openFormSheet(
    BuildContext context,
    Map<String, dynamic> building,
  ) async {
    final formCubit = context.read<BuildingFormCubit>()..reset();
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (_) => BlocProvider.value(
        value: formCubit,
        child: BuildingFormSheet(initialBuilding: building),
      ),
    );

    if (result != null && context.mounted) {
      final messenger = ScaffoldMessenger.of(context);
      messenger.showSnackBar(
        const SnackBar(content: Text('Building updated successfully')),
      );
      context.read<BuildingDetailCubit>().refresh();
    }
  }
}

class _SummaryCard extends StatelessWidget {
  final Map<String, dynamic> building;
  const _SummaryCard({required this.building});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isActive = building['is_active'] as bool? ?? true;

    return Card(
      key: const ValueKey('tc_s2_mob_building_summary_card'),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: colorScheme.primaryContainer,
                  child: Icon(Icons.apartment,
                      color: colorScheme.onPrimaryContainer),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        building['name']?.toString() ?? 'Building',
                        style: theme.textTheme.titleLarge
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        building['address']?.toString() ?? 'No address provided',
                        style: TextStyle(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                Chip(
                  label: Text(isActive ? 'Active' : 'Inactive'),
                  backgroundColor: isActive
                      ? colorScheme.primaryContainer
                      : colorScheme.errorContainer,
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(Icons.location_city,
                    size: 18, color: colorScheme.onSurfaceVariant),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${building['city'] ?? 'Unknown'}, ${building['country'] ?? '—'}',
                    style: TextStyle(color: colorScheme.onSurfaceVariant),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  final Map<String, dynamic> building;
  final String occupancyPercent;
  const _StatsGrid({required this.building, required this.occupancyPercent});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    List<_StatItem> stats = [
      _StatItem(
        label: 'Floors',
        value: (building['num_floors'] ?? '0').toString(),
        icon: Icons.layers_outlined,
      ),
      _StatItem(
        label: 'Apartments',
        value: (building['num_apartments'] ?? '0').toString(),
        icon: Icons.door_front_door_outlined,
      ),
      _StatItem(
        label: 'Stores',
        value: (building['num_stores'] ?? '0').toString(),
        icon: Icons.store_outlined,
      ),
      _StatItem(
        label: 'Occupancy',
        value: '$occupancyPercent%',
        icon: Icons.analytics_outlined,
      ),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        child: Wrap(
          alignment: WrapAlignment.spaceAround,
          children: stats
              .map(
                (stat) => SizedBox(
                  width: MediaQuery.of(context).size.width / 2 - 32,
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: colorScheme.surfaceVariant,
                      child: Icon(stat.icon,
                          color: colorScheme.onSurfaceVariant, size: 20),
                    ),
                    title: Text(stat.value,
                        style: const TextStyle(
                            fontWeight: FontWeight.w700, fontSize: 18)),
                    subtitle: Text(stat.label),
                  ),
                ),
              )
              .toList(),
        ),
      ),
    );
  }
}

class _StatItem {
  final String label;
  final String value;
  final IconData icon;
  _StatItem({required this.label, required this.value, required this.icon});
}

class _ActionSection extends StatelessWidget {
  final Map<String, dynamic> building;
  final String buildingId;
  const _ActionSection({required this.building, required this.buildingId});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Actions',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            OutlinedButton.icon(
              key: const ValueKey('tc_s2_mob_manage_units_btn'),
              onPressed: () {
                context.push(
                  Routes.adminBuildingUnits(buildingId),
                  extra: {
                    'buildingName': building['name']?.toString(),
                  },
                );
              },
              icon: const Icon(Icons.apartment_outlined),
              label: const Text('Manage Units'),
            ),
            OutlinedButton.icon(
              onPressed: () {
                context.push(Routes.adminAssets);
              },
              icon: const Icon(Icons.inventory_2_outlined),
              label: const Text('View Assets'),
            ),
            OutlinedButton.icon(
              onPressed: () {
                context.push(Routes.adminExpenses);
              },
              icon: const Icon(Icons.receipt_long_outlined),
              label: const Text('View Expenses'),
            ),
          ],
        ),
      ],
    );
  }
}

class _DetailsCard extends StatelessWidget {
  final Map<String, dynamic> building;
  const _DetailsCard({required this.building});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rows = <MapEntry<String, String?>>[
      MapEntry('Address', building['address']?.toString()),
      MapEntry('City', building['city']?.toString()),
      MapEntry('Country', building['country']?.toString()),
      MapEntry('Created At', building['created_at']?.toString()),
      MapEntry('Last Updated', building['updated_at']?.toString()),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Details',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            ...rows.map((row) => ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text(row.key,
                      style: TextStyle(
                          color: theme.colorScheme.onSurfaceVariant)),
                  subtitle: Text(row.value ?? '—'),
                )),
          ],
        ),
      ),
    );
  }
}

class _NotesCard extends StatelessWidget {
  final Map<String, dynamic> building;
  const _NotesCard({required this.building});

  @override
  Widget build(BuildContext context) {
    final notes = building['description']?.toString();
    if (notes == null || notes.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Icon(Icons.note_alt_outlined,
                  color: Theme.of(context).colorScheme.onSurfaceVariant),
              const SizedBox(width: 12),
              const Expanded(
                child: Text('No internal notes yet.'),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Notes',
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            Text(notes),
          ],
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline,
              size: 48, color: Theme.of(context).colorScheme.error),
          const SizedBox(height: 12),
          Text(message),
          const SizedBox(height: 12),
          FilledButton(onPressed: onRetry, child: const Text('Retry')),
        ],
      ),
    );
  }
}
