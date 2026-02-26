import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/notifications_api.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<Map<String, dynamic>> _notifications = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  NotificationsApi get _api =>
      NotificationsApi(apiClient: context.read<ApiClient>());

  Future<void> _loadNotifications() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final notifications = await _api.fetchNotifications();
      setState(() => _notifications = notifications);
    } catch (e) {
      setState(() => _error = 'Failed to load notifications.');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _markAllRead() async {
    try {
      await _api.markAllRead();
      _loadNotifications();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to mark all as read.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasUnread = _notifications.any((n) => n['is_read'] != true);

    return Scaffold(
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline,
                          size: 48, color: theme.colorScheme.error),
                      const SizedBox(height: 12),
                      Text(_error!,
                          style:
                              TextStyle(color: theme.colorScheme.error)),
                      const SizedBox(height: 12),
                      FilledButton(
                          onPressed: _loadNotifications,
                          child: const Text('Retry')),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadNotifications,
                  child: Column(
                    children: [
                      if (hasUnread)
                        Padding(
                          padding: const EdgeInsets.all(12),
                          child: SizedBox(
                            width: double.infinity,
                            child: OutlinedButton.icon(
                              onPressed: _markAllRead,
                              icon: const Icon(Icons.done_all, size: 18),
                              label: const Text('Mark all as read'),
                            ),
                          ),
                        ),
                      Expanded(
                        child: _notifications.isEmpty
                            ? Center(
                                child: Column(
                                  mainAxisAlignment:
                                      MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.notifications_none_outlined,
                                        size: 64,
                                        color: theme
                                            .colorScheme.onSurfaceVariant),
                                    const SizedBox(height: 16),
                                    Text('No notifications.',
                                        style: theme.textTheme.titleMedium
                                            ?.copyWith(
                                                color: theme.colorScheme
                                                    .onSurfaceVariant)),
                                  ],
                                ),
                              )
                            : ListView.separated(
                                padding: const EdgeInsets.all(16),
                                itemCount: _notifications.length,
                                separatorBuilder: (_, __) =>
                                    const SizedBox(height: 8),
                                itemBuilder: (ctx, i) {
                                  final n = _notifications[i];
                                  final isRead = n['is_read'] == true;
                                  return Card(
                                    color: isRead
                                        ? null
                                        : theme.colorScheme.primaryContainer
                                            .withOpacity(0.3),
                                    child: ListTile(
                                      leading: CircleAvatar(
                                        backgroundColor: isRead
                                            ? theme.colorScheme
                                                .surfaceContainerHighest
                                            : theme.colorScheme
                                                .primaryContainer,
                                        child: Icon(
                                          isRead
                                              ? Icons.notifications_none
                                              : Icons.notifications_active,
                                          color: isRead
                                              ? theme.colorScheme
                                                  .onSurfaceVariant
                                              : theme.colorScheme
                                                  .onPrimaryContainer,
                                        ),
                                      ),
                                      title: Text(
                                        n['title'] as String? ?? '',
                                        style: TextStyle(
                                          fontWeight: isRead
                                              ? FontWeight.normal
                                              : FontWeight.w600,
                                        ),
                                      ),
                                      subtitle: Text(
                                          n['message'] as String? ?? ''),
                                      trailing: !isRead
                                          ? IconButton(
                                              icon:
                                                  const Icon(Icons.done, size: 18),
                                              tooltip: 'Mark as read',
                                              onPressed: () async {
                                                try {
                                                  await _api.markRead(
                                                      n['id'] as String);
                                                  _loadNotifications();
                                                } catch (_) {}
                                              },
                                            )
                                          : null,
                                    ),
                                  );
                                },
                              ),
                      ),
                    ],
                  ),
                ),
    );
  }
}
