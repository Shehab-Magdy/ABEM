import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../auth/bloc/auth_bloc.dart';
import '../bloc/notification_cubit.dart';

/// Notification center screen with unread badge, filter chips, swipe actions,
/// and admin broadcast/send panels.
class NotificationCenterScreen extends StatefulWidget {
  const NotificationCenterScreen({super.key});

  @override
  State<NotificationCenterScreen> createState() =>
      _NotificationCenterScreenState();
}

class _NotificationCenterScreenState
    extends State<NotificationCenterScreen> {
  final ScrollController _scrollController = ScrollController();
  String _filter = 'All';

  // Admin panels
  bool _showBroadcast = false;
  bool _showSendMessage = false;
  final _broadcastSubjectController = TextEditingController();
  final _broadcastMessageController = TextEditingController();
  final _sendSubjectController = TextEditingController();
  final _sendBodyController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _broadcastSubjectController.dispose();
    _broadcastMessageController.dispose();
    _sendSubjectController.dispose();
    _sendBodyController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      context.read<NotificationCubit>().loadMore();
    }
  }

  List<Map<String, dynamic>> _applyFilter(
    List<Map<String, dynamic>> items,
  ) {
    if (_filter == 'Unread') {
      return items.where((n) => n['is_read'] != true).toList();
    }
    return items;
  }

  Color _typeColor(String? type) {
    switch (type?.toLowerCase()) {
      case 'payment':
        return AppColors.balanceSettled;
      case 'expense':
        return AppColors.accent;
      case 'alert':
      case 'warning':
        return AppColors.danger;
      case 'broadcast':
        return AppColors.purple;
      case 'message':
        return AppColors.balanceCredit;
      default:
        return AppColors.neutralMid;
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
      key: const ValueKey('tc_s6_mob_notification_center'),
      appBar: AppBar(
        title: BlocBuilder<NotificationCubit, NotificationState>(
          builder: (context, state) {
            final unread = state is NotificationLoaded
                ? state.unreadCount
                : 0;
            return Row(
              children: [
                const Text('Notifications'),
                if (unread > 0) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.danger,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      unread.toString(),
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ],
            );
          },
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.done_all),
            tooltip: 'Mark all read',
            onPressed: () =>
                context.read<NotificationCubit>().markAllRead(),
          ),
        ],
      ),
      body: Column(
        children: [
          // ── Filter chips ──
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: ['All', 'Unread'].map((label) {
                final isSelected = _filter == label;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(label),
                    selected: isSelected,
                    onSelected: (_) =>
                        setState(() => _filter = label),
                  ),
                );
              }).toList(),
            ),
          ),

          // ── Admin panels ──
          if (isAdmin) ...[
            _AdminExpandablePanel(
              title: 'Broadcast',
              icon: Icons.campaign_outlined,
              expanded: _showBroadcast,
              onToggle: () =>
                  setState(() => _showBroadcast = !_showBroadcast),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    TextField(
                      controller: _broadcastSubjectController,
                      decoration: const InputDecoration(
                        labelText: 'Subject',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _broadcastMessageController,
                      decoration: const InputDecoration(
                        labelText: 'Message',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      maxLines: 3,
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        icon: const Icon(Icons.send, size: 18),
                        label: const Text('Send Broadcast'),
                        onPressed: () {
                          // TODO: Invoke broadcast via cubit
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Broadcast sent')),
                          );
                          _broadcastSubjectController.clear();
                          _broadcastMessageController.clear();
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
            _AdminExpandablePanel(
              title: 'Send Message',
              icon: Icons.mail_outlined,
              expanded: _showSendMessage,
              onToggle: () => setState(
                  () => _showSendMessage = !_showSendMessage),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    TextField(
                      controller: _sendSubjectController,
                      decoration: const InputDecoration(
                        labelText: 'Subject',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _sendBodyController,
                      decoration: const InputDecoration(
                        labelText: 'Body',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      maxLines: 3,
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        icon: const Icon(Icons.send, size: 18),
                        label: const Text('Send Message'),
                        onPressed: () {
                          // TODO: Invoke sendMessage via cubit
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Message sent')),
                          );
                          _sendSubjectController.clear();
                          _sendBodyController.clear();
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],

          // ── Notification list ──
          Expanded(
            child: BlocBuilder<NotificationCubit, NotificationState>(
              builder: (context, state) {
                if (state is NotificationLoading) {
                  return const Center(
                      child: CircularProgressIndicator());
                }
                if (state is NotificationError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error_outline,
                            size: 48,
                            color: theme.colorScheme.error),
                        const SizedBox(height: 12),
                        Text(state.message,
                            style: TextStyle(
                                color: theme.colorScheme.error)),
                        const SizedBox(height: 12),
                        FilledButton(
                          onPressed: () => context
                              .read<NotificationCubit>()
                              .refresh(),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  );
                }

                final items = state is NotificationLoaded
                    ? _applyFilter(state.items)
                    : <Map<String, dynamic>>[];

                if (items.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.notifications_none_outlined,
                            size: 64,
                            color:
                                theme.colorScheme.onSurfaceVariant),
                        const SizedBox(height: 16),
                        Text('No notifications.',
                            style: theme.textTheme.titleMedium
                                ?.copyWith(
                                    color: theme.colorScheme
                                        .onSurfaceVariant)),
                      ],
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () =>
                      context.read<NotificationCubit>().refresh(),
                  child: ListView.separated(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: items.length,
                    separatorBuilder: (_, __) =>
                        const SizedBox(height: 8),
                    itemBuilder: (ctx, i) {
                      final n = items[i];
                      final isRead = n['is_read'] == true;
                      final id = n['id']?.toString() ?? '';

                      return Dismissible(
                        key: ValueKey('notification_$id'),
                        direction: DismissDirection.endToStart,
                        onDismissed: (_) {
                          if (!isRead) {
                            context
                                .read<NotificationCubit>()
                                .markRead(id);
                          }
                        },
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding:
                              const EdgeInsets.only(right: 20),
                          decoration: BoxDecoration(
                            color: AppColors.balanceSettled
                                .withAlpha(30),
                            borderRadius:
                                BorderRadius.circular(12),
                          ),
                          child: const Icon(Icons.done,
                              color: AppColors.balanceSettled),
                        ),
                        child: _NotificationCard(
                          notification: n,
                          typeColor: _typeColor(
                              n['type'] as String?),
                          onTap: () {
                            if (!isRead) {
                              context
                                  .read<NotificationCubit>()
                                  .markRead(id);
                            }
                          },
                        ),
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

class _NotificationCard extends StatelessWidget {
  final Map<String, dynamic> notification;
  final Color typeColor;
  final VoidCallback onTap;
  const _NotificationCard({
    required this.notification,
    required this.typeColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isRead = notification['is_read'] == true;
    final title = notification['title'] as String? ?? '';
    final body = notification['message'] as String? ??
        notification['body'] as String? ??
        '';
    final type = notification['type'] as String? ?? '';
    final sender = notification['sender_name'] as String? ?? '';
    final timestamp = notification['created_at'] as String? ??
        notification['timestamp'] as String? ??
        '';

    return Card(
      color: isRead
          ? null
          : theme.colorScheme.primaryContainer.withAlpha(40),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Blue unread dot
              if (!isRead)
                Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.only(top: 6, right: 8),
                  decoration: const BoxDecoration(
                    color: AppColors.balanceCredit,
                    shape: BoxShape.circle,
                  ),
                )
              else
                const SizedBox(width: 16),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        if (type.isNotEmpty)
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            margin: const EdgeInsets.only(right: 8),
                            decoration: BoxDecoration(
                              color: typeColor.withAlpha(30),
                              borderRadius:
                                  BorderRadius.circular(4),
                            ),
                            child: Text(
                              type,
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: typeColor,
                              ),
                            ),
                          ),
                        Expanded(
                          child: Text(title,
                              style: TextStyle(
                                fontWeight: isRead
                                    ? FontWeight.normal
                                    : FontWeight.w600,
                                fontSize: 14,
                              )),
                        ),
                      ],
                    ),
                    if (body.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(body,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                              fontSize: 13,
                              color: theme
                                  .colorScheme.onSurfaceVariant)),
                    ],
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        if (sender.isNotEmpty) ...[
                          Icon(Icons.person_outline,
                              size: 12,
                              color: theme
                                  .colorScheme.onSurfaceVariant),
                          const SizedBox(width: 2),
                          Text(sender,
                              style: TextStyle(
                                  fontSize: 11,
                                  color: theme.colorScheme
                                      .onSurfaceVariant)),
                          const SizedBox(width: 12),
                        ],
                        Icon(Icons.access_time,
                            size: 12,
                            color: theme
                                .colorScheme.onSurfaceVariant),
                        const SizedBox(width: 2),
                        Text(timestamp,
                            style: TextStyle(
                                fontSize: 11,
                                color: theme.colorScheme
                                    .onSurfaceVariant)),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AdminExpandablePanel extends StatelessWidget {
  final String title;
  final IconData icon;
  final bool expanded;
  final VoidCallback onToggle;
  final Widget child;

  const _AdminExpandablePanel({
    required this.title,
    required this.icon,
    required this.expanded,
    required this.onToggle,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Column(
        children: [
          ListTile(
            leading: Icon(icon, size: 20),
            title: Text(title,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            trailing: Icon(expanded
                ? Icons.keyboard_arrow_up
                : Icons.keyboard_arrow_down),
            dense: true,
            onTap: onToggle,
          ),
          if (expanded) child,
        ],
      ),
    );
  }
}
