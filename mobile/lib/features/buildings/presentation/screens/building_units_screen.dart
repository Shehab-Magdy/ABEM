import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/routes.dart';
import '../bloc/building_units_cubit.dart';

class BuildingUnitsScreen extends StatefulWidget {
  final String buildingId;
  final String? buildingName;
  const BuildingUnitsScreen({super.key, required this.buildingId, this.buildingName});

  @override
  State<BuildingUnitsScreen> createState() => _BuildingUnitsScreenState();
}

class _BuildingUnitsScreenState extends State<BuildingUnitsScreen> {
  String _filter = 'all';
  String _search = '';

  @override
  Widget build(BuildContext context) {
    final title = widget.buildingName ?? 'Units';

    return Scaffold(
      key: ValueKey('tc_s2_mob_building_units_${widget.buildingId}'),
      appBar: AppBar(
        title: Text('$title · Units'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<BuildingUnitsCubit>().refresh(),
          ),
        ],
      ),
      body: Column(
        children: [
          _Filters(
            selected: _filter,
            onChanged: (value) => setState(() => _filter = value),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: TextField(
              key: const ValueKey('tc_s2_mob_units_search_field'),
              decoration: InputDecoration(
                hintText: 'Search units, owners…',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: Theme.of(context).colorScheme.surfaceVariant,
              ),
              onChanged: (value) => setState(() => _search = value.trim()),
            ),
          ),
          Expanded(
            child: BlocBuilder<BuildingUnitsCubit, BuildingUnitsState>(
              builder: (context, state) {
                if (state is BuildingUnitsLoading ||
                    state is BuildingUnitsInitial) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is BuildingUnitsError) {
                  return _UnitsErrorView(
                    message: state.message,
                    onRetry: () =>
                        context.read<BuildingUnitsCubit>().load(widget.buildingId),
                  );
                }

                final units = switch (state) {
                  BuildingUnitsLoaded(:final units) => units,
                  BuildingUnitsRefreshing(:final units) => units,
                  _ => const <Map<String, dynamic>>[],
                };

                final filtered = units.where(_applyFilters).toList();

                if (filtered.isEmpty) {
                  return _UnitsEmptyView(filter: _filter, search: _search);
                }

                return RefreshIndicator(
                  onRefresh: () => context.read<BuildingUnitsCubit>().refresh(),
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: filtered.length,
                    itemBuilder: (_, index) => _UnitCard(
                      unit: filtered[index],
                      onTap: () {
                        final id = filtered[index]['id']?.toString();
                        if (id != null) {
                          context.push(Routes.adminApartmentDetail(id));
                        }
                      },
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  bool _applyFilters(Map<String, dynamic> unit) {
    final status = (unit['status'] ?? 'unknown').toString().toLowerCase();
    final matchesFilter = switch (_filter) {
      'occupied' => status == 'occupied',
      'vacant' => status == 'vacant',
      _ => true,
    };

    if (!matchesFilter) return false;
    if (_search.isEmpty) return true;

    final ownerNames = (unit['owner_names'] as List?)?.cast<String>() ?? [];
    final haystack = [
      unit['unit_number']?.toString() ?? '',
      unit['floor']?.toString() ?? '',
      ...ownerNames,
    ].join(' ').toLowerCase();

    return haystack.contains(_search.toLowerCase());
  }
}

class _Filters extends StatelessWidget {
  final String selected;
  final ValueChanged<String> onChanged;
  const _Filters({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'all', label: Text('All')),
          ButtonSegment(value: 'occupied', label: Text('Occupied')),
          ButtonSegment(value: 'vacant', label: Text('Vacant')),
        ],
        selected: {selected},
        onSelectionChanged: (set) => onChanged(set.first),
      ),
    );
  }
}

class _UnitCard extends StatelessWidget {
  final Map<String, dynamic> unit;
  final VoidCallback onTap;
  const _UnitCard({required this.unit, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final status = (unit['status'] ?? 'unknown').toString();
    final isOccupied = status == 'occupied';
    final owners = (unit['owner_names'] as List?)?.cast<String>() ?? [];

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        key: ValueKey('tc_s2_mob_unit_card_${unit['id']}'),
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor:
              isOccupied ? colorScheme.primaryContainer : colorScheme.surfaceVariant,
          child: Icon(
            isOccupied ? Icons.home_work_outlined : Icons.vacant_bed_outlined,
            color: isOccupied
                ? colorScheme.onPrimaryContainer
                : colorScheme.onSurfaceVariant,
          ),
        ),
        title: Text('Unit ${unit['unit_number'] ?? '—'}'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Floor ${unit['floor'] ?? '—'} · ${status.toUpperCase()}'),
            if (owners.isNotEmpty)
              Text(
                owners.join(', '),
                style: TextStyle(color: colorScheme.onSurfaceVariant),
              ),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}

class _UnitsEmptyView extends StatelessWidget {
  final String filter;
  final String search;
  const _UnitsEmptyView({required this.filter, required this.search});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final message = search.isNotEmpty
        ? 'No units match "$search"'
        : switch (filter) {
            'occupied' => 'No occupied units yet',
            'vacant' => 'No vacant units yet',
            _ => 'No units found for this building',
          };

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.door_front_door_outlined,
              size: 56, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(height: 12),
          Text(
            message,
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _UnitsErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _UnitsErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline,
              size: 56, color: theme.colorScheme.error),
          const SizedBox(height: 12),
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 12),
          FilledButton(onPressed: onRetry, child: const Text('Retry')),
        ],
      ),
    );
  }
}
