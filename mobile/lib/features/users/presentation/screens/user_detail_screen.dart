import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/datasources/user_remote_data_source.dart';
import '../../data/repositories/user_repository.dart';
import '../bloc/user_detail_cubit.dart';

/// User detail screen with edit form and admin action tiles.
class UserDetailScreen extends StatelessWidget {
  final String userId;
  const UserDetailScreen({super.key, required this.userId});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) {
        final cubit = UserDetailCubit(
          UserRepository(
            context.read<UserRemoteDataSource>(),
          ),
        );
        cubit.load(userId);
        return cubit;
      },
      child: _UserDetailView(userId: userId),
    );
  }
}

class _UserDetailView extends StatelessWidget {
  final String userId;
  const _UserDetailView({required this.userId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const ValueKey('tc_s1_mob_user_detail'),
      appBar: AppBar(title: const Text('User Details')),
      body: BlocConsumer<UserDetailCubit, UserDetailState>(
        listener: (context, state) {
          if (state is UserDetailActionSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message)),
            );
          }
          if (state is UserDetailError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is UserDetailLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is UserDetailError) {
            return Center(child: Text(state.message));
          }

          final user = state is UserDetailLoaded ? state.user : null;
          if (user == null) return const SizedBox.shrink();

          return RefreshIndicator(
            onRefresh: () =>
                context.read<UserDetailCubit>().load(userId),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _UserEditSection(userId: userId, user: user),
                const SizedBox(height: 16),
                _ActionTiles(userId: userId, user: user),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _UserEditSection extends StatefulWidget {
  final String userId;
  final Map<String, dynamic> user;
  const _UserEditSection({required this.userId, required this.user});

  @override
  State<_UserEditSection> createState() => _UserEditSectionState();
}

class _UserEditSectionState extends State<_UserEditSection> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _firstNameCtrl;
  late TextEditingController _lastNameCtrl;
  late TextEditingController _phoneCtrl;
  late String _selectedRole;

  @override
  void initState() {
    super.initState();
    _firstNameCtrl = TextEditingController(
      text: widget.user['first_name'] as String? ?? '',
    );
    _lastNameCtrl = TextEditingController(
      text: widget.user['last_name'] as String? ?? '',
    );
    _phoneCtrl = TextEditingController(
      text: widget.user['phone'] as String? ?? '',
    );
    _selectedRole = widget.user['role'] as String? ?? 'owner';
  }

  @override
  void didUpdateWidget(covariant _UserEditSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.user != oldWidget.user) {
      _firstNameCtrl.text = widget.user['first_name'] as String? ?? '';
      _lastNameCtrl.text = widget.user['last_name'] as String? ?? '';
      _phoneCtrl.text = widget.user['phone'] as String? ?? '';
      _selectedRole = widget.user['role'] as String? ?? 'owner';
    }
  }

  @override
  void dispose() {
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Edit User',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _firstNameCtrl,
                      decoration:
                          const InputDecoration(labelText: 'First Name'),
                      validator: (v) =>
                          (v == null || v.trim().isEmpty) ? 'Required' : null,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _lastNameCtrl,
                      decoration:
                          const InputDecoration(labelText: 'Last Name'),
                      validator: (v) =>
                          (v == null || v.trim().isEmpty) ? 'Required' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _phoneCtrl,
                decoration: const InputDecoration(labelText: 'Phone'),
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 12),
              Text('Role', style: theme.textTheme.bodySmall),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'admin', label: Text('Admin')),
                  ButtonSegment(value: 'owner', label: Text('Owner')),
                ],
                selected: {_selectedRole},
                onSelectionChanged: (set) {
                  setState(() => _selectedRole = set.first);
                },
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _save,
                  child: const Text('Save Changes'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    context.read<UserDetailCubit>().updateUser(widget.userId, {
      'first_name': _firstNameCtrl.text.trim(),
      'last_name': _lastNameCtrl.text.trim(),
      'phone': _phoneCtrl.text.trim(),
      'role': _selectedRole,
    });
  }
}

class _ActionTiles extends StatelessWidget {
  final String userId;
  final Map<String, dynamic> user;
  const _ActionTiles({required this.userId, required this.user});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final isActive = user['is_active'] as bool? ?? true;
    final isMessagingBlocked = user['is_messaging_blocked'] as bool? ?? false;
    final isIndividualBlocked =
        user['is_individual_messaging_blocked'] as bool? ?? false;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Actions',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),

            // ── Activate / Deactivate ─────────────────────────────────
            ListTile(
              leading: Icon(
                isActive ? Icons.block : Icons.check_circle_outline,
                color: isActive ? colorScheme.error : Colors.green,
              ),
              title: Text(isActive ? 'Deactivate User' : 'Activate User'),
              subtitle: Text(
                isActive
                    ? 'User will not be able to login'
                    : 'Re-enable user access',
              ),
              onTap: () => _confirmToggleActive(context, isActive),
            ),
            const Divider(height: 1),

            // ── Reset Password ────────────────────────────────────────
            ListTile(
              leading: Icon(Icons.lock_reset, color: colorScheme.primary),
              title: const Text('Reset Password'),
              subtitle: const Text('Set a new password for this user'),
              onTap: () => _showResetPasswordSheet(context),
            ),
            const Divider(height: 1),

            // ── Messaging Restrictions ────────────────────────────────
            ListTile(
              leading:
                  Icon(Icons.message_outlined, color: colorScheme.primary),
              title: const Text('Messaging Restrictions'),
              subtitle: const Text('Control broadcast and individual messaging'),
              onTap: () => _showMessagingSheet(
                context,
                isMessagingBlocked,
                isIndividualBlocked,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmToggleActive(BuildContext context, bool isActive) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isActive ? 'Deactivate User' : 'Activate User'),
        content: Text(
          isActive
              ? 'Are you sure you want to deactivate this user? They will not be able to login.'
              : 'Are you sure you want to activate this user? They will regain access.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: isActive
                ? FilledButton.styleFrom(
                    backgroundColor: Theme.of(ctx).colorScheme.error,
                  )
                : null,
            onPressed: () {
              Navigator.pop(ctx);
              if (isActive) {
                context.read<UserDetailCubit>().deactivate(userId);
              } else {
                context.read<UserDetailCubit>().activate(userId);
              }
            },
            child: Text(isActive ? 'Deactivate' : 'Activate'),
          ),
        ],
      ),
    );
  }

  void _showResetPasswordSheet(BuildContext context) {
    final pwCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.fromLTRB(
          24,
          24,
          24,
          24 + MediaQuery.of(ctx).viewInsets.bottom,
        ),
        child: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Reset Password',
                style: Theme.of(ctx)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: pwCtrl,
                obscureText: true,
                decoration:
                    const InputDecoration(labelText: 'New Password'),
                validator: (v) {
                  if (v == null || v.length < 8) {
                    return 'At least 8 characters';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    if (!formKey.currentState!.validate()) return;
                    Navigator.pop(ctx);
                    context
                        .read<UserDetailCubit>()
                        .resetPassword(userId, pwCtrl.text);
                  },
                  child: const Text('Reset Password'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showMessagingSheet(
    BuildContext context,
    bool blocked,
    bool individualBlocked,
  ) {
    bool broadcastBlocked = blocked;
    bool individualMsgBlocked = individualBlocked;

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
                'Messaging Restrictions',
                style: Theme.of(ctx)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 16),
              SwitchListTile(
                title: const Text('Block Broadcast Messages'),
                subtitle:
                    const Text('Prevent user from receiving broadcasts'),
                value: broadcastBlocked,
                onChanged: (v) {
                  setSheetState(() => broadcastBlocked = v);
                },
              ),
              SwitchListTile(
                title: const Text('Block Individual Messages'),
                subtitle:
                    const Text('Prevent user from sending individual messages'),
                value: individualMsgBlocked,
                onChanged: (v) {
                  setSheetState(() => individualMsgBlocked = v);
                },
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    Navigator.pop(ctx);
                    context.read<UserDetailCubit>().setMessagingBlock(
                          userId,
                          blocked: broadcastBlocked,
                          individualBlocked: individualMsgBlocked,
                        );
                  },
                  child: const Text('Save'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
