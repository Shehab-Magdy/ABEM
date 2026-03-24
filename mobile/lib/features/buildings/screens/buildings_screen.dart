import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:dio/dio.dart';

import '../../../core/api/buildings_api.dart';
import '../../../injection.dart';
import '../../auth/bloc/auth_bloc.dart';

class BuildingsScreen extends StatefulWidget {
  const BuildingsScreen({super.key});

  @override
  State<BuildingsScreen> createState() => _BuildingsScreenState();
}

class _BuildingsScreenState extends State<BuildingsScreen> {
  List<Map<String, dynamic>> _buildings = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadBuildings();
  }

  BuildingsApi get _api => BuildingsApi(dio: getIt<Dio>());

  Future<void> _loadBuildings() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final buildings = await _api.fetchBuildings();
      setState(() => _buildings = buildings);
    } catch (e) {
      setState(() => _error = 'Failed to load buildings.');
    } finally {
      setState(() => _loading = false);
    }
  }

  bool get _isAdmin {
    final authState = context.read<AuthBloc>().state;
    if (authState is AuthAuthenticated) {
      return authState.user['role'] == 'admin';
    }
    return false;
  }

  Future<void> _showCreateDialog() async {
    final nameCtrl = TextEditingController();
    final addressCtrl = TextEditingController();
    final cityCtrl = TextEditingController();
    final countryCtrl = TextEditingController();
    final floorsCtrl = TextEditingController(text: '1');
    final formKey = GlobalKey<FormState>();
    String? dialogError;

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('New Building'),
          content: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (dialogError != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(dialogError!,
                          style: TextStyle(
                              color: Theme.of(ctx).colorScheme.error)),
                    ),
                  TextFormField(
                    controller: nameCtrl,
                    decoration: const InputDecoration(labelText: 'Name *'),
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Required' : null,
                  ),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: addressCtrl,
                    decoration: const InputDecoration(labelText: 'Address *'),
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Required' : null,
                  ),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: cityCtrl,
                    decoration: const InputDecoration(labelText: 'City *'),
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Required' : null,
                  ),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: countryCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Country'),
                  ),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: floorsCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Floors *'),
                    keyboardType: TextInputType.number,
                    validator: (v) {
                      final n = int.tryParse(v ?? '');
                      if (n == null || n < 1) return 'Must be >= 1';
                      return null;
                    },
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                if (!formKey.currentState!.validate()) return;
                try {
                  await _api.createBuilding({
                    'name': nameCtrl.text,
                    'address': addressCtrl.text,
                    'city': cityCtrl.text,
                    'country': countryCtrl.text,
                    'num_floors': int.parse(floorsCtrl.text),
                  });
                  if (ctx.mounted) Navigator.pop(ctx);
                  _loadBuildings();
                } catch (e) {
                  setDialogState(() => dialogError = 'Failed to create building.');
                }
              },
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmDelete(Map<String, dynamic> building) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete Building'),
        content:
            Text('Delete "${building['name']}"? This cannot be undone.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          FilledButton(
            style: FilledButton.styleFrom(
                backgroundColor: Theme.of(ctx).colorScheme.error),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      try {
        await _api.deleteBuilding(building['id'] as String);
        _loadBuildings();
      } catch (_) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to delete building.')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isAdmin = _isAdmin;

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _loadBuildings,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error_outline,
                            size: 48,
                            color: theme.colorScheme.error),
                        const SizedBox(height: 12),
                        Text(_error!,
                            style: TextStyle(
                                color: theme.colorScheme.error)),
                        const SizedBox(height: 12),
                        FilledButton(
                          onPressed: _loadBuildings,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : _buildings.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.apartment_outlined,
                                size: 64,
                                color:
                                    theme.colorScheme.onSurfaceVariant),
                            const SizedBox(height: 16),
                            Text('No buildings yet.',
                                style: theme.textTheme.titleMedium?.copyWith(
                                    color: theme
                                        .colorScheme.onSurfaceVariant)),
                            if (isAdmin) ...[
                              const SizedBox(height: 12),
                              FilledButton.icon(
                                onPressed: _showCreateDialog,
                                icon: const Icon(Icons.add),
                                label: const Text('Add Building'),
                              ),
                            ],
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _buildings.length,
                        itemBuilder: (ctx, i) {
                          final b = _buildings[i];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: theme.colorScheme.primaryContainer,
                                child: Icon(Icons.apartment,
                                    color: theme.colorScheme.onPrimaryContainer),
                              ),
                              title: Text(b['name'] as String? ?? '',
                                  style: const TextStyle(fontWeight: FontWeight.w600)),
                              subtitle: Text(
                                '${b['city'] ?? ''}${b['country'] != null && (b['country'] as String).isNotEmpty ? ', ${b['country']}' : ''}\n'
                                '${b['num_floors'] ?? 0} floor(s)',
                              ),
                              isThreeLine: false,
                              trailing: isAdmin
                                  ? IconButton(
                                      icon: Icon(Icons.delete_outline,
                                          color: theme.colorScheme.error),
                                      onPressed: () => _confirmDelete(b),
                                    )
                                  : null,
                            ),
                          );
                        },
                      ),
      ),
      floatingActionButton: isAdmin
          ? FloatingActionButton(
              onPressed: _showCreateDialog,
              child: const Icon(Icons.add),
            )
          : null,
    );
  }
}
