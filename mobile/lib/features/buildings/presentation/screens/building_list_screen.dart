import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/routes.dart';
import '../../../auth/bloc/auth_bloc.dart';
import '../bloc/building_form_cubit.dart';
import '../bloc/building_list_cubit.dart';
import '../widgets/building_form_sheet.dart';

/// Admin building list screen with search, pull-to-refresh, and CRUD actions.
class BuildingListScreen extends StatelessWidget {
  const BuildingListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final authState = context.watch<AuthBloc>().state;
    final isAdmin =
        authState is AuthAuthenticated && authState.isAdmin;

    return Scaffold(
      key: const ValueKey('tc_s2_mob_buildings_list'),
      appBar: AppBar(
        title: const Text('Buildings'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: TextField(
              key: const ValueKey('tc_s2_mob_search_field'),
              decoration: InputDecoration(
                hintText: 'Search buildings…',
                prefixIcon: const Icon(Icons.search, size: 20),
                isDense: true,
                filled: true,
                fillColor: colorScheme.surfaceContainerHighest,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 8),
              ),
              onChanged: (query) {
                context.read<BuildingListCubit>().loadBuildings(search: query);
              },
            ),
          ),
        ),
      ),
      body: BlocBuilder<BuildingListCubit, BuildingListState>(
        builder: (context, state) {
          if (state is BuildingListLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is BuildingListError) {
            return _ErrorView(
              message: state.message,
              onRetry: () =>
                  context.read<BuildingListCubit>().loadBuildings(),
            );
          }
          if (state is BuildingListLoaded) {
            if (state.buildings.isEmpty) {
              return _EmptyView(isAdmin: isAdmin);
            }
            return RefreshIndicator(
              onRefresh: () => context.read<BuildingListCubit>().refresh(),
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: state.buildings.length,
                itemBuilder: (_, i) => _BuildingCard(
                  building: state.buildings[i],
                  isAdmin: isAdmin,
                  onDelete: () {
                    final id = state.buildings[i]['id'] as String;
                    _confirmDelete(context, state.buildings[i], id);
                  },
                  onToggleActive: () {
                    final id = state.buildings[i]['id'] as String;
                    final active =
                        state.buildings[i]['is_active'] as bool? ?? true;
                    context
                        .read<BuildingListCubit>()
                        .toggleActive(id, isCurrentlyActive: active);
                  },
                  onEdit: () => _openFormSheet(
                    context,
                    building: state.buildings[i],
                  ),
                  onViewDetail: () {
                    final id = state.buildings[i]['id']?.toString();
                    if (id != null) {
                      context.push(Routes.adminBuildingDetail(id));
                    }
                  },
                ),
              ),
            );
          }
          return const SizedBox.shrink();
        },
      ),
      floatingActionButton: isAdmin
          ? FloatingActionButton.extended(
              key: const ValueKey('tc_s2_mob_add_building_fab'),
              onPressed: () => _openFormSheet(context),
              icon: const Icon(Icons.add),
              label: const Text('Add Building'),
            )
          : null,
    );
  }

  Future<void> _openFormSheet(BuildContext context,
      {Map<String, dynamic>? building}) async {
    final formCubit = context.read<BuildingFormCubit>()..reset();
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (_) => BlocProvider.value(
        value: formCubit,
        child: BuildingFormSheet(initialBuilding: building),
      ),
    );

    if (result != null) {
      if (!context.mounted) return;
      final snackText =
          building == null ? 'Building created' : 'Building updated';
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(snackText)));
      context.read<BuildingListCubit>().loadBuildings();
    }
  }

  void _confirmDelete(
    BuildContext context,
    Map<String, dynamic> building,
    String id,
  ) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Building'),
        content: Text(
            'Delete "${building['name']}"? This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(ctx).colorScheme.error,
            ),
            onPressed: () {
              Navigator.pop(ctx);
              context.read<BuildingListCubit>().deleteBuilding(id);
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

}

class _BuildingCard extends StatelessWidget {
  final Map<String, dynamic> building;
  final bool isAdmin;
  final VoidCallback onDelete;
  final VoidCallback onToggleActive;
  final VoidCallback onEdit;
  final VoidCallback onViewDetail;

  const _BuildingCard({
    required this.building,
    required this.isAdmin,
    required this.onDelete,
    required this.onToggleActive,
    required this.onEdit,
    required this.onViewDetail,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final name = building['name'] as String? ?? '';
    final city = building['city'] as String? ?? '';
    final country = building['country'] as String? ?? '';
    final floors = building['num_floors'] ?? 0;
    final apts = building['num_apartments'] ?? 0;
    final stores = building['num_stores'] ?? 0;
    final isActive = building['is_active'] as bool? ?? true;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        key: ValueKey('tc_s2_mob_building_card_${building['id']}'),
        borderRadius: BorderRadius.circular(16),
        onTap: onViewDetail,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: colorScheme.primaryContainer,
                child: Icon(Icons.apartment,
                    color: colorScheme.onPrimaryContainer),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(name,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600, fontSize: 16)),
                        ),
                        if (!isActive)
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: colorScheme.errorContainer,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text('Inactive',
                                style: TextStyle(
                                    fontSize: 11,
                                    color: colorScheme.onErrorContainer)),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      [city, country]
                          .where((s) => s.isNotEmpty)
                          .join(', '),
                      style: TextStyle(
                          fontSize: 13, color: colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: [
                        _InfoChip(
                            icon: Icons.layers, label: '$floors floors'),
                        _InfoChip(
                            icon: Icons.door_front_door_outlined,
                            label: '$apts apts'),
                        if ((stores as int) > 0)
                          _InfoChip(
                              icon: Icons.store_outlined,
                              label: '$stores stores'),
                      ],
                    ),
                  ],
                ),
              ),
              if (isAdmin)
                PopupMenuButton<String>(
                  onSelected: (action) {
                    switch (action) {
                      case 'toggle':
                        onToggleActive();
                        break;
                      case 'edit':
                        onEdit();
                        break;
                      case 'delete':
                        onDelete();
                        break;
                    }
                  },
                  itemBuilder: (_) => [
                    PopupMenuItem(
                      value: 'toggle',
                      child: Text(isActive ? 'Deactivate' : 'Activate'),
                    ),
                    const PopupMenuItem(
                      value: 'edit',
                      child: Text('Edit'),
                    ),
                    PopupMenuItem(
                      value: 'delete',
                      child: Text('Delete',
                          style: TextStyle(color: colorScheme.error)),
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

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _InfoChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.onSurfaceVariant;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 3),
        Text(label, style: TextStyle(fontSize: 12, color: color)),
      ],
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 48, color: colorScheme.error),
          const SizedBox(height: 12),
          Text(message, style: TextStyle(color: colorScheme.error)),
          const SizedBox(height: 12),
          FilledButton(onPressed: onRetry, child: const Text('Retry')),
        ],
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  final bool isAdmin;
  const _EmptyView({required this.isAdmin});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.apartment_outlined,
              size: 64, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(height: 16),
          Text('No buildings yet.',
              style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant)),
          if (isAdmin) ...[
            const SizedBox(height: 12),
            Text('Tap the + button to add your first building.',
                style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
          ],
        ],
      ),
    );
  }
}
