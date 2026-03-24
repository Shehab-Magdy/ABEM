import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/audit_cubit.dart';

/// Admin audit log screen with filters, relative timestamps, and pagination.
class AuditScreen extends StatefulWidget {
  const AuditScreen({super.key});

  @override
  State<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends State<AuditScreen> {
  final _scrollController = ScrollController();
  String? _entityType;
  String? _action;
  String? _dateFrom;
  String? _dateTo;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      context.read<AuditCubit>().loadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      key: const ValueKey('tc_s8_mob_audit_log'),
      appBar: AppBar(
        title: const Text('Audit Log'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () => _showFilterSheet(context),
          ),
        ],
      ),
      body: BlocBuilder<AuditCubit, AuditState>(
        builder: (context, state) {
          if (state is AuditLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is AuditError) {
            return _ErrorView(
              message: state.message,
              onRetry: () => context.read<AuditCubit>().loadLogs(),
            );
          }
          if (state is AuditLoaded) {
            if (state.logs.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.history,
                        size: 64, color: colorScheme.onSurfaceVariant),
                    const SizedBox(height: 16),
                    Text(
                      'No audit logs found.',
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              );
            }
            return ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: state.logs.length + (state.hasMore ? 1 : 0),
              itemBuilder: (_, i) {
                if (i >= state.logs.length) {
                  return const Padding(
                    padding: EdgeInsets.all(16),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                return _AuditLogRow(log: state.logs[i]);
              },
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }

  void _showFilterSheet(BuildContext context) {
    String? entityType = _entityType;
    String? action = _action;
    final dateFromCtrl = TextEditingController(text: _dateFrom ?? '');
    final dateToCtrl = TextEditingController(text: _dateTo ?? '');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheetState) => Padding(
          padding: EdgeInsets.fromLTRB(
            24,
            24,
            24,
            24 + MediaQuery.of(ctx).viewInsets.bottom,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Filter Audit Logs',
                style: Theme.of(ctx)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: entityType,
                decoration:
                    const InputDecoration(labelText: 'Entity Type'),
                items: const [
                  DropdownMenuItem(value: null, child: Text('All')),
                  DropdownMenuItem(value: 'user', child: Text('User')),
                  DropdownMenuItem(
                      value: 'building', child: Text('Building')),
                  DropdownMenuItem(
                      value: 'apartment', child: Text('Apartment')),
                  DropdownMenuItem(
                      value: 'payment', child: Text('Payment')),
                  DropdownMenuItem(
                      value: 'expense', child: Text('Expense')),
                  DropdownMenuItem(value: 'asset', child: Text('Asset')),
                ],
                onChanged: (v) =>
                    setSheetState(() => entityType = v),
              ),
              const SizedBox(height: 12),
              TextFormField(
                initialValue: action,
                decoration: const InputDecoration(
                  labelText: 'Action',
                  hintText: 'e.g. create, update, delete',
                ),
                onChanged: (v) => action = v.isEmpty ? null : v,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: dateFromCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Date From',
                        suffixIcon: Icon(Icons.calendar_today, size: 18),
                      ),
                      readOnly: true,
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: ctx,
                          initialDate: DateTime.now()
                              .subtract(const Duration(days: 30)),
                          firstDate: DateTime(2020),
                          lastDate: DateTime.now(),
                        );
                        if (picked != null) {
                          setSheetState(() {
                            dateFromCtrl.text =
                                '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
                          });
                        }
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: dateToCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Date To',
                        suffixIcon: Icon(Icons.calendar_today, size: 18),
                      ),
                      readOnly: true,
                      onTap: () async {
                        final picked = await showDatePicker(
                          context: ctx,
                          initialDate: DateTime.now(),
                          firstDate: DateTime(2020),
                          lastDate: DateTime.now(),
                        );
                        if (picked != null) {
                          setSheetState(() {
                            dateToCtrl.text =
                                '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
                          });
                        }
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        setState(() {
                          _entityType = null;
                          _action = null;
                          _dateFrom = null;
                          _dateTo = null;
                        });
                        context.read<AuditCubit>().loadLogs();
                      },
                      child: const Text('Clear'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: () {
                        Navigator.pop(ctx);
                        setState(() {
                          _entityType = entityType;
                          _action = action;
                          _dateFrom = dateFromCtrl.text.isEmpty
                              ? null
                              : dateFromCtrl.text;
                          _dateTo = dateToCtrl.text.isEmpty
                              ? null
                              : dateToCtrl.text;
                        });
                        context.read<AuditCubit>().loadLogs(
                              entityType: _entityType,
                              action: _action,
                              dateFrom: _dateFrom,
                              dateTo: _dateTo,
                            );
                      },
                      child: const Text('Apply'),
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

class _AuditLogRow extends StatelessWidget {
  final Map<String, dynamic> log;
  const _AuditLogRow({required this.log});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final timestamp = log['created_at'] as String? ?? '';
    final actorName = log['actor_name'] as String? ??
        log['actor_email'] as String? ??
        'System';
    final action = log['action'] as String? ?? '';
    final entityType = log['entity_type'] as String? ?? '';
    final entitySnippet = log['description'] as String? ??
        log['entity_repr'] as String? ??
        '';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: _actionColor(action).withAlpha(30),
              child: Icon(
                _actionIcon(action),
                size: 18,
                color: _actionColor(action),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          actorName,
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                      ),
                      Text(
                        _relativeTime(timestamp),
                        style: TextStyle(
                          fontSize: 12,
                          color: colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: _actionColor(action).withAlpha(30),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          action.toUpperCase(),
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: _actionColor(action),
                          ),
                        ),
                      ),
                      if (entityType.isNotEmpty) ...[
                        const SizedBox(width: 6),
                        Text(
                          entityType,
                          style: TextStyle(
                            fontSize: 12,
                            color: colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ],
                  ),
                  if (entitySnippet.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      entitySnippet,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _actionColor(String action) {
    switch (action.toLowerCase()) {
      case 'create':
        return Colors.green;
      case 'update':
        return Colors.blue;
      case 'delete':
        return Colors.red;
      case 'activate':
        return Colors.teal;
      case 'deactivate':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  IconData _actionIcon(String action) {
    switch (action.toLowerCase()) {
      case 'create':
        return Icons.add_circle_outline;
      case 'update':
        return Icons.edit_outlined;
      case 'delete':
        return Icons.delete_outline;
      case 'activate':
        return Icons.check_circle_outline;
      case 'deactivate':
        return Icons.block;
      default:
        return Icons.info_outline;
    }
  }

  String _relativeTime(String timestamp) {
    if (timestamp.isEmpty) return '';
    try {
      final dt = DateTime.parse(timestamp);
      final now = DateTime.now();
      final diff = now.difference(dt);

      if (diff.inSeconds < 60) return 'just now';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      if (diff.inDays < 7) return '${diff.inDays}d ago';
      if (diff.inDays < 30) return '${(diff.inDays / 7).floor()}w ago';
      return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
    } catch (_) {
      return timestamp;
    }
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
