import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';

import '../../auth/bloc/auth_bloc.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _firstNameCtrl;
  late TextEditingController _lastNameCtrl;
  late TextEditingController _phoneCtrl;

  bool _saving = false;
  bool _uploadingPicture = false;

  @override
  void initState() {
    super.initState();
    final user = _currentUser;
    _firstNameCtrl =
        TextEditingController(text: user?['first_name'] as String? ?? '');
    _lastNameCtrl =
        TextEditingController(text: user?['last_name'] as String? ?? '');
    _phoneCtrl =
        TextEditingController(text: user?['phone'] as String? ?? '');
  }

  @override
  void dispose() {
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  Map<String, dynamic>? get _currentUser {
    final state = context.read<AuthBloc>().state;
    return state is AuthAuthenticated ? state.user : null;
  }

  Future<void> _pickAndUpload() async {
    final picker = ImagePicker();
    final picked =
        await picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (picked == null || !mounted) return;

    setState(() => _uploadingPicture = true);
    context
        .read<AuthBloc>()
        .add(AuthProfilePictureUpdateRequested(picked));
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    context.read<AuthBloc>().add(AuthProfileUpdateRequested({
          'first_name': _firstNameCtrl.text.trim(),
          'last_name': _lastNameCtrl.text.trim(),
          'phone': _phoneCtrl.text.trim(),
        }));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return BlocConsumer<AuthBloc, AuthState>(
      listener: (context, state) {
        setState(() {
          _saving = false;
          _uploadingPicture = false;
        });
        if (state is AuthAuthenticated) {
          // Re-sync controllers with updated user data.
          _firstNameCtrl.text = state.user['first_name'] as String? ?? '';
          _lastNameCtrl.text = state.user['last_name'] as String? ?? '';
          _phoneCtrl.text = state.user['phone'] as String? ?? '';
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Profile updated')),
          );
        } else if (state is AuthError) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(state.message),
              backgroundColor: theme.colorScheme.error,
            ),
          );
        }
      },
      builder: (context, state) {
        final user =
            state is AuthAuthenticated ? state.user : _currentUser;
        final pictureUrl = user?['profile_picture'] as String?;
        final initials =
            ((user?['first_name'] as String? ?? '?')[0]).toUpperCase();

        return Scaffold(
          appBar: AppBar(
            title: const Text('My Profile'),
            centerTitle: false,
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // ── Avatar with upload overlay ──────────────────────────────
                Stack(
                  alignment: Alignment.bottomRight,
                  children: [
                    CircleAvatar(
                      radius: 54,
                      backgroundColor: theme.colorScheme.primaryContainer,
                      backgroundImage: pictureUrl != null && pictureUrl.isNotEmpty
                          ? CachedNetworkImageProvider(pictureUrl)
                          : null,
                      child: (pictureUrl == null || pictureUrl.isEmpty)
                          ? Text(
                              initials,
                              style: TextStyle(
                                fontSize: 36,
                                color: theme.colorScheme.onPrimaryContainer,
                              ),
                            )
                          : null,
                    ),
                    if (_uploadingPicture)
                      Positioned.fill(
                        child: CircleAvatar(
                          radius: 54,
                          backgroundColor: Colors.black38,
                          child: const CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        ),
                      ),
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: Material(
                        shape: const CircleBorder(),
                        color: theme.colorScheme.primary,
                        child: InkWell(
                          customBorder: const CircleBorder(),
                          onTap: _uploadingPicture ? null : _pickAndUpload,
                          child: Padding(
                            padding: const EdgeInsets.all(8),
                            child: Icon(
                              Icons.camera_alt,
                              size: 18,
                              color: theme.colorScheme.onPrimary,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 8),
                Text(
                  user?['email'] as String? ?? '',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                if (user?['role'] != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Chip(
                      label: Text(
                        (user!['role'] as String).toUpperCase(),
                        style: const TextStyle(fontSize: 11),
                      ),
                      padding: EdgeInsets.zero,
                    ),
                  ),

                const SizedBox(height: 32),

                // ── Profile form ────────────────────────────────────────────
                Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: _firstNameCtrl,
                              decoration:
                                  const InputDecoration(labelText: 'First name'),
                              validator: (v) =>
                                  (v == null || v.trim().isEmpty)
                                      ? 'Required'
                                      : null,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: TextFormField(
                              controller: _lastNameCtrl,
                              decoration:
                                  const InputDecoration(labelText: 'Last name'),
                              validator: (v) =>
                                  (v == null || v.trim().isEmpty)
                                      ? 'Required'
                                      : null,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _phoneCtrl,
                        decoration:
                            const InputDecoration(labelText: 'Phone (optional)'),
                        keyboardType: TextInputType.phone,
                      ),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton(
                          onPressed: _saving ? null : _saveProfile,
                          child: _saving
                              ? const SizedBox(
                                  height: 18,
                                  width: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text('Save changes'),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
