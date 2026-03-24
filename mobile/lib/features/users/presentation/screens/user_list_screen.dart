import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/user_list_cubit.dart';
import 'user_create_screen.dart';
import 'user_detail_screen.dart';

/// Admin user list screen with search, role filter chips, and CRUD navigation.
class UserListScreen extends StatefulWidget {
  const UserListScreen({super.key});

  @override
  State<UserListScreen> createState() => _UserListScreenState();
}

class _UserListScreenState extends State<UserListScreen> {
  String _searchQuery = '';
  String? _selectedRole;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      key: const ValueKey('tc_s1_mob_user_list'),
      appBar: AppBar(
        title: const Text('Users'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Search users...',
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
                setState(() => _searchQuery = query);
                context.read<UserListCubit>().loadUsers(
                      search: query,
                      role: _selectedRole,
                    );
              },
            ),
          ),
        ),
      ),
      body: Column(
        children: [
          // ── Role filter chips ────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Row(
              children: [
                _RoleChip(
                  label: 'All',
                  selected: _selectedRole == null,
                  onTap: () => _onRoleSelected(null),
                ),
                const SizedBox(width: 8),
                _RoleChip(
                  label: 'Admin',
                  selected: _selectedRole == 'admin',
                  onTap: () => _onRoleSelected('admin'),
                ),
                const SizedBox(width: 8),
                _RoleChip(
                  label: 'Owner',
                  selected: _selectedRole == 'owner',
                  onTap: () => _onRoleSelected('owner'),
                ),
              ],
            ),
          ),

          // ── User list ───────────────────────────────────────────────
          Expanded(
            child: BlocBuilder<UserListCubit, UserListState>(
              builder: (context, state) {
                if (state is UserListLoading) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is UserListError) {
                  return _ErrorView(
                    message: state.message,
                    onRetry: () =>
                        context.read<UserListCubit>().loadUsers(),
                  );
                }
                if (state is UserListLoaded) {
                  if (state.users.isEmpty) {
                    return const _EmptyView();
                  }
                  return RefreshIndicator(
                    onRefresh: () => context.read<UserListCubit>().refresh(),
                    child: ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: state.users.length,
                      itemBuilder: (_, i) => _UserCard(
                        user: state.users[i],
                        onTap: () => _navigateToDetail(
                          context,
                          state.users[i]['id']?.toString() ?? '',
                        ),
                      ),
                    ),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        key: const ValueKey('tc_s1_mob_user_create_fab'),
        onPressed: () => _navigateToCreate(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _onRoleSelected(String? role) {
    setState(() => _selectedRole = role);
    context.read<UserListCubit>().loadUsers(
          search: _searchQuery.isNotEmpty ? _searchQuery : null,
          role: role,
        );
  }

  void _navigateToDetail(BuildContext context, String userId) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => UserDetailScreen(userId: userId),
      ),
    );
  }

  void _navigateToCreate(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => const UserCreateScreen(),
      ),
    );
  }
}

class _RoleChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _RoleChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return FilterChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onTap(),
      selectedColor: colorScheme.primaryContainer,
      checkmarkColor: colorScheme.onPrimaryContainer,
    );
  }
}

class _UserCard extends StatelessWidget {
  final Map<String, dynamic> user;
  final VoidCallback onTap;

  const _UserCard({required this.user, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final firstName = user['first_name'] as String? ?? '';
    final lastName = user['last_name'] as String? ?? '';
    final fullName = '$firstName $lastName'.trim();
    final email = user['email'] as String? ?? '';
    final role = user['role'] as String? ?? 'owner';
    final isActive = user['is_active'] as bool? ?? true;

    // Initials fallback
    final initials = [
      if (firstName.isNotEmpty) firstName[0],
      if (lastName.isNotEmpty) lastName[0],
    ].join().toUpperCase();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: colorScheme.primaryContainer,
                child: Text(
                  initials.isNotEmpty ? initials : '?',
                  style: TextStyle(
                    color: colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            fullName.isNotEmpty ? fullName : 'Unnamed',
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 16,
                            ),
                          ),
                        ),
                        // Active dot
                        Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: isActive ? Colors.green : Colors.grey,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      email,
                      style: TextStyle(
                        fontSize: 13,
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: role == 'admin'
                            ? colorScheme.tertiaryContainer
                            : colorScheme.secondaryContainer,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        role.toUpperCase(),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: role == 'admin'
                              ? colorScheme.onTertiaryContainer
                              : colorScheme.onSecondaryContainer,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: colorScheme.onSurfaceVariant),
            ],
          ),
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
  const _EmptyView();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.people_outlined,
              size: 64, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(height: 16),
          Text(
            'No users found.',
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}
