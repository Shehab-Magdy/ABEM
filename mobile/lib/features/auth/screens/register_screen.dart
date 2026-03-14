import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/apartments_api.dart';
import '../../../core/api/buildings_api.dart';
import '../../../core/theme/app_theme.dart';
import '../bloc/auth_bloc.dart';
import '../repositories/auth_repository.dart';

// ── Error extraction helper ───────────────────────────────────────────────────

String _extractError(DioException e) {
  final data = e.response?.data;
  if (data is Map) {
    // Handle backend envelope: {"status":"error","code":400,"errors":{...}}
    final errObj = (data['errors'] is Map ? data['errors'] : data) as Map;
    final values = errObj.values.expand((v) => v is List ? v : [v]).toList();
    return values.map((v) => v.toString()).join(' ');
  }
  return data?.toString() ?? 'An error occurred.';
}

// ── Step indicator ────────────────────────────────────────────────────────────

class _StepIndicator extends StatelessWidget {
  final int currentStep;
  final List<String> labels;

  const _StepIndicator({required this.currentStep, required this.labels});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      children: List.generate(labels.length * 2 - 1, (i) {
        if (i.isOdd) {
          final filled = i ~/ 2 < currentStep;
          return Expanded(
            child: Container(
              height: 2,
              color: filled ? scheme.primary : scheme.outlineVariant,
            ),
          );
        }
        final step = i ~/ 2;
        final done = step < currentStep;
        final active = step == currentStep;
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor:
                  done || active ? scheme.primary : scheme.outlineVariant,
              child: done
                  ? const Icon(Icons.check, size: 16, color: Colors.white)
                  : Text(
                      '${step + 1}',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: active ? Colors.white : scheme.onSurfaceVariant,
                      ),
                    ),
            ),
            const SizedBox(height: 4),
            Text(
              labels[step],
              style: TextStyle(
                fontSize: 11,
                color: active ? scheme.primary : scheme.onSurfaceVariant,
                fontWeight: active ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        );
      }),
    );
  }
}

// ── Main screen ───────────────────────────────────────────────────────────────

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  int _step = 0;
  String _role = 'owner';

  void _nextStep() => setState(() => _step++);

  // Admin: Account(0) → Buildings(1) → Unit(2) → Done(3)
  // Owner: Account(0) → Unit(1) → Done(2)
  List<String> get _stepLabels => _role == 'admin'
      ? ['Account', 'Buildings', 'Your Unit', 'Done']
      : ['Account', 'Your Unit', 'Done'];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Scaffold(
      backgroundColor: scheme.surfaceContainerLowest,
      appBar: AppBar(
        title: const Text('Create Account'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: _step == 0
            ? IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () => context.go('/login'),
              )
            : null,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(Icons.apartment_rounded, size: 48, color: scheme.primary),
                  const SizedBox(height: 8),
                  Text(
                    'ABEM',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: scheme.primary,
                    ),
                  ),
                  const SizedBox(height: 24),
                  _StepIndicator(currentStep: _step, labels: _stepLabels),
                  const SizedBox(height: 28),
                  Card(
                    elevation: 2,
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: AnimatedSwitcher(
                        duration: const Duration(milliseconds: 250),
                        child: _buildStep(context),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStep(BuildContext context) {
    if (_step == 0) {
      return _AccountStep(
        key: const ValueKey('account'),
        onDone: (role) => setState(() { _role = role; _step = 1; }),
      );
    }
    // Admin: Buildings(1) → Unit(2) → Done(3)
    if (_role == 'admin') {
      if (_step == 1) {
        return _AdminBuildingsStep(
          key: const ValueKey('admin-buildings'),
          onDone: _nextStep,
          onSkip: _nextStep,
        );
      }
      if (_step == 2) {
        return _ClaimUnitStep(
          key: const ValueKey('admin-unit'),
          isAdmin: true,
          onDone: _nextStep,
          onSkip: _nextStep,
        );
      }
      return _DoneStep(
        key: const ValueKey('done-admin'),
        role: _role,
        onFinish: () => context.go('/home'),
      );
    }
    // Owner: Unit(1) → Done(2)
    if (_step == 1) {
      return _ClaimUnitStep(
        key: const ValueKey('owner-unit'),
        isAdmin: false,
        onDone: _nextStep,
        onSkip: _nextStep,
      );
    }
    return _DoneStep(
      key: const ValueKey('done-owner'),
      role: _role,
      onFinish: () => context.go('/home'),
    );
  }
}

// ── Step 1: Account ───────────────────────────────────────────────────────────

class _AccountStep extends StatefulWidget {
  final void Function(String role) onDone;
  const _AccountStep({super.key, required this.onDone});

  @override
  State<_AccountStep> createState() => _AccountStepState();
}

class _AccountStepState extends State<_AccountStep> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  String? _error;
  String _role = 'owner';

  @override
  void dispose() {
    _firstNameCtrl.dispose(); _lastNameCtrl.dispose();
    _emailCtrl.dispose(); _phoneCtrl.dispose();
    _passwordCtrl.dispose(); _confirmCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_formKey.currentState?.validate() != true) return;
    setState(() { _loading = true; _error = null; });
    try {
      final repo = context.read<AuthRepository>();
      await repo.selfRegister({
        'first_name': _firstNameCtrl.text.trim(),
        'last_name': _lastNameCtrl.text.trim(),
        'email': _emailCtrl.text.trim(),
        'phone': _phoneCtrl.text.trim(),
        'role': _role,
        'password': _passwordCtrl.text,
        'confirm_password': _confirmCtrl.text,
      });
      if (mounted) {
        context.read<AuthBloc>().add(AuthCheckRequested());
        widget.onDone(_role);
      }
    } on DioException catch (e) {
      setState(() => _error = _extractError(e));
    } catch (_) {
      setState(() => _error = 'Registration failed. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Account Details',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 20),
          if (_error != null) ...[_ErrorCard(message: _error!), const SizedBox(height: 16)],

          Row(children: [
            Expanded(child: TextFormField(
              controller: _firstNameCtrl, textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'First name *'),
              validator: (v) => (v == null || v.isEmpty) ? 'Required.' : null,
            )),
            const SizedBox(width: 12),
            Expanded(child: TextFormField(
              controller: _lastNameCtrl, textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Last name *'),
              validator: (v) => (v == null || v.isEmpty) ? 'Required.' : null,
            )),
          ]),
          const SizedBox(height: 16),
          TextFormField(
            controller: _emailCtrl, keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next, autocorrect: false,
            decoration: const InputDecoration(labelText: 'Email *', prefixIcon: Icon(Icons.email_outlined)),
            validator: (v) {
              if (v == null || v.isEmpty) return 'Required.';
              if (!RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(v)) return 'Invalid email.';
              return null;
            },
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _phoneCtrl, keyboardType: TextInputType.phone,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(labelText: 'Phone (optional)', prefixIcon: Icon(Icons.phone_outlined)),
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordCtrl, obscureText: _obscure, textInputAction: TextInputAction.next,
            decoration: InputDecoration(
              labelText: 'Password *', prefixIcon: const Icon(Icons.lock_outline),
              helperText: 'Min 8 chars, 1 uppercase, 1 digit, 1 special char.', helperMaxLines: 2,
              suffixIcon: IconButton(
                icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                onPressed: () => setState(() => _obscure = !_obscure),
              ),
            ),
            validator: (v) => (v == null || v.isEmpty) ? 'Required.' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _confirmCtrl, obscureText: _obscure,
            textInputAction: TextInputAction.done,
            onFieldSubmitted: (_) => _submit(),
            decoration: const InputDecoration(
              labelText: 'Confirm password *', prefixIcon: Icon(Icons.lock_outline)),
            validator: (v) {
              if (v == null || v.isEmpty) return 'Required.';
              if (v != _passwordCtrl.text) return 'Passwords do not match.';
              return null;
            },
          ),
          const SizedBox(height: 20),
          Text('I am a…',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          _RoleSelector(value: _role, onChanged: (v) => setState(() => _role = v)),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _loading ? null : _submit,
            style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
            child: _loading
                ? const SizedBox(height: 20, width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Continue', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
          ),
          const SizedBox(height: 16),
          GestureDetector(
            onTap: () => context.go('/login'),
            child: Text('Already have an account? Sign in',
              textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).colorScheme.primary, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

// ── Role selector ─────────────────────────────────────────────────────────────

class _RoleSelector extends StatelessWidget {
  final String value;
  final ValueChanged<String> onChanged;
  const _RoleSelector({required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      _RoleCard(selected: value == 'owner', icon: Icons.person_outlined,
          label: 'Owner', subtitle: 'Apartment / tenant', onTap: () => onChanged('owner')),
      const SizedBox(width: 12),
      _RoleCard(selected: value == 'admin', icon: Icons.admin_panel_settings_outlined,
          label: 'Admin', subtitle: 'Building manager', onTap: () => onChanged('admin')),
    ]);
  }
}

class _RoleCard extends StatelessWidget {
  final bool selected;
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;
  const _RoleCard({required this.selected, required this.icon,
      required this.label, required this.subtitle, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            border: Border.all(
              color: selected ? scheme.primary : scheme.outlineVariant,
              width: selected ? 2 : 1,
            ),
            borderRadius: BorderRadius.circular(12),
            color: selected ? scheme.primary.withAlpha(20) : Colors.transparent,
          ),
          child: Column(children: [
            Icon(icon, color: selected ? scheme.primary : scheme.onSurfaceVariant, size: 28),
            const SizedBox(height: 6),
            Text(label, style: TextStyle(
                fontWeight: FontWeight.w600,
                color: selected ? scheme.primary : scheme.onSurface)),
            Text(subtitle, textAlign: TextAlign.center,
                style: TextStyle(fontSize: 11, color: scheme.onSurfaceVariant)),
          ]),
        ),
      ),
    );
  }
}

// ── Step 2 Admin: Add buildings ───────────────────────────────────────────────

class _AdminBuildingsStep extends StatefulWidget {
  final VoidCallback onDone;
  final VoidCallback onSkip;
  const _AdminBuildingsStep({super.key, required this.onDone, required this.onSkip});

  @override
  State<_AdminBuildingsStep> createState() => _AdminBuildingsStepState();
}

class _AdminBuildingsStepState extends State<_AdminBuildingsStep> {
  final List<Map<String, TextEditingController>> _buildings = [];
  bool _submitting = false;
  String? _error;

  @override
  void initState() { super.initState(); _addBuilding(); }

  void _addBuilding() {
    setState(() {
      _buildings.add({
        'name': TextEditingController(),
        'address': TextEditingController(),
        'city': TextEditingController(),
        'country': TextEditingController(),
        'num_floors': TextEditingController(text: '1'),
        'num_apartments': TextEditingController(text: '0'),
        'num_stores': TextEditingController(text: '0'),
      });
    });
  }

  void _removeBuilding(int idx) {
    if (_buildings.length <= 1) return;
    for (final ctrl in _buildings[idx].values) ctrl.dispose();
    setState(() => _buildings.removeAt(idx));
  }

  @override
  void dispose() {
    for (final b in _buildings) for (final c in b.values) c.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final hasAny = _buildings.any((b) => b['name']!.text.trim().isNotEmpty);
    if (!hasAny) { widget.onSkip(); return; }
    setState(() { _submitting = true; _error = null; });
    try {
      final api = BuildingsApi(apiClient: context.read<ApiClient>());
      for (final b in _buildings) {
        final name = b['name']!.text.trim();
        if (name.isEmpty) continue;
        await api.createBuilding({
          'name': name,
          'address': b['address']!.text.trim(),
          'city': b['city']!.text.trim(),
          'country': b['country']!.text.trim(),
          'num_floors': int.tryParse(b['num_floors']!.text) ?? 1,
          'num_apartments': int.tryParse(b['num_apartments']!.text) ?? 0,
          'num_stores': int.tryParse(b['num_stores']!.text) ?? 0,
        });
      }
      widget.onDone();
    } on DioException catch (e) {
      setState(() => _error = _extractError(e));
    } catch (_) {
      setState(() => _error = 'Could not save buildings. Try again.');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Your Buildings',
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Text('Add the buildings you manage. You can add more later from the dashboard.',
            style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const SizedBox(height: 16),
        if (_error != null) ...[_ErrorCard(message: _error!), const SizedBox(height: 12)],
        ..._buildings.asMap().entries.map((e) => _BuildingCard(
          index: e.key, controllers: e.value,
          canRemove: _buildings.length > 1, onRemove: () => _removeBuilding(e.key),
        )),
        TextButton.icon(
          onPressed: _addBuilding,
          icon: const Icon(Icons.add, size: 18),
          label: const Text('Add another building'),
        ),
        const SizedBox(height: 20),
        Row(children: [
          Expanded(child: OutlinedButton(
            onPressed: _submitting ? null : widget.onSkip,
            child: const Text('Skip for now'),
          )),
          const SizedBox(width: 12),
          Expanded(child: FilledButton(
            onPressed: _submitting ? null : _submit,
            child: _submitting
                ? const SizedBox(height: 20, width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Save & Continue'),
          )),
        ]),
      ],
    );
  }
}

class _BuildingCard extends StatelessWidget {
  final int index;
  final Map<String, TextEditingController> controllers;
  final bool canRemove;
  final VoidCallback onRemove;

  const _BuildingCard({required this.index, required this.controllers,
      required this.canRemove, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        border: Border.all(color: scheme.outlineVariant),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text('Building ${index + 1}', style: const TextStyle(fontWeight: FontWeight.w600)),
          if (canRemove) IconButton(
            icon: const Icon(Icons.close, size: 18), color: scheme.error,
            constraints: const BoxConstraints(), padding: EdgeInsets.zero,
            onPressed: onRemove,
          ),
        ]),
        const SizedBox(height: 10),
        TextFormField(controller: controllers['name'], textInputAction: TextInputAction.next,
            decoration: const InputDecoration(labelText: 'Name *', isDense: true)),
        const SizedBox(height: 10),
        TextFormField(controller: controllers['address'], textInputAction: TextInputAction.next,
            decoration: const InputDecoration(labelText: 'Address *', isDense: true)),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(child: TextFormField(controller: controllers['city'],
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'City *', isDense: true))),
          const SizedBox(width: 10),
          Expanded(child: TextFormField(controller: controllers['country'],
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Country', isDense: true))),
        ]),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(child: TextFormField(
            controller: controllers['num_floors'], keyboardType: TextInputType.number,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(labelText: 'Floors', isDense: true),
          )),
          const SizedBox(width: 8),
          Expanded(child: TextFormField(
            controller: controllers['num_apartments'], keyboardType: TextInputType.number,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(
              labelText: '# Apts', isDense: true,
              helperText: 'A1,A2…', helperStyle: TextStyle(fontSize: 10),
            ),
          )),
          const SizedBox(width: 8),
          Expanded(child: TextFormField(
            controller: controllers['num_stores'], keyboardType: TextInputType.number,
            textInputAction: TextInputAction.done,
            decoration: const InputDecoration(
              labelText: '# Stores', isDense: true,
              helperText: 'S1,S2…', helperStyle: TextStyle(fontSize: 10),
            ),
          )),
        ]),
      ]),
    );
  }
}

// ── Shared: Claim a unit (admin or owner) ─────────────────────────────────────

class _ClaimUnitStep extends StatefulWidget {
  final bool isAdmin;
  final VoidCallback onDone;
  final VoidCallback onSkip;
  const _ClaimUnitStep({super.key, required this.isAdmin,
      required this.onDone, required this.onSkip});

  @override
  State<_ClaimUnitStep> createState() => _ClaimUnitStepState();
}

class _ClaimUnitStepState extends State<_ClaimUnitStep> {
  List<Map<String, dynamic>> _buildings = [];
  List<Map<String, dynamic>> _apartments = [];
  String? _selectedBuildingId;
  String? _selectedApartmentId;
  String _typeFilter = 'all'; // 'all' | 'apartment' | 'store'
  bool _loadingBuildings = true;
  bool _loadingApts = false;
  bool _claiming = false;
  String? _error;

  late ApartmentsApi _api;

  @override
  void initState() {
    super.initState();
    _api = ApartmentsApi(apiClient: context.read<ApiClient>());
    _loadBuildings();
  }

  Future<void> _loadBuildings() async {
    try {
      final data = await _api.buildingDirectory();
      if (mounted) setState(() => _buildings = data);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not load buildings.');
    } finally {
      if (mounted) setState(() => _loadingBuildings = false);
    }
  }

  Future<void> _onBuildingSelected(String? id) async {
    if (id == null) return;
    setState(() {
      _selectedBuildingId = id;
      _selectedApartmentId = null;
      _apartments = [];
      _typeFilter = 'all';
      _loadingApts = true;
    });
    try {
      final data = await _api.availableApartments(id);
      if (mounted) setState(() => _apartments = data);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not load units.');
    } finally {
      if (mounted) setState(() => _loadingApts = false);
    }
  }

  Future<void> _claim() async {
    if (_selectedApartmentId == null) return;
    setState(() { _claiming = true; _error = null; });
    try {
      await _api.claimApartment(_selectedApartmentId!);
      widget.onDone();
    } on DioException catch (e) {
      final data = e.response?.data;
      setState(() => _error = (data is Map ? data['detail'] : null) ?? 'Could not claim unit.');
    } catch (_) {
      setState(() => _error = 'An unexpected error occurred.');
    } finally {
      if (mounted) setState(() => _claiming = false);
    }
  }

  List<Map<String, dynamic>> get _filtered => _typeFilter == 'all'
      ? _apartments
      : _apartments.where((a) => a['unit_type'] == _typeFilter).toList();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Your Unit',
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Text(
          widget.isAdmin
              ? 'If you also own a unit in one of your buildings, select it here. You can skip.'
              : 'Select your building and the unit you own.',
          style: theme.textTheme.bodySmall?.copyWith(color: scheme.onSurfaceVariant),
        ),
        const SizedBox(height: 16),

        if (_error != null) ...[
          _ErrorCard(message: _error!, onClose: () => setState(() => _error = null)),
          const SizedBox(height: 12),
        ],

        if (_loadingBuildings)
          const Center(child: CircularProgressIndicator())
        else if (_buildings.isEmpty)
          _InfoCard(
            message: widget.isAdmin
                ? 'No buildings yet. Go back and add your building first, or skip.'
                : 'No buildings registered yet. Ask your manager to add the building first.',
          )
        else ...[
          DropdownButtonFormField<String>(
            value: _selectedBuildingId,
            decoration: const InputDecoration(labelText: 'Select building'),
            items: _buildings.map((b) => DropdownMenuItem<String>(
              value: b['id'].toString(),
              child: Text('${b['name']} — ${b['city']}', overflow: TextOverflow.ellipsis),
            )).toList(),
            onChanged: _onBuildingSelected,
          ),

          if (_selectedBuildingId != null) ...[
            const SizedBox(height: 16),
            if (_loadingApts)
              const Center(child: CircularProgressIndicator())
            else if (_apartments.isEmpty)
              _InfoCard(message: 'No available units in this building.')
            else ...[
              // Filter chips
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(children: [
                  FilterChip(label: const Text('All'), selected: _typeFilter == 'all',
                      visualDensity: VisualDensity.compact,
                      onSelected: (_) => setState(() { _typeFilter = 'all'; _selectedApartmentId = null; })),
                  const SizedBox(width: 8),
                  FilterChip(label: const Text('Apartments'), selected: _typeFilter == 'apartment',
                      visualDensity: VisualDensity.compact,
                      onSelected: (_) => setState(() { _typeFilter = 'apartment'; _selectedApartmentId = null; })),
                  const SizedBox(width: 8),
                  FilterChip(label: const Text('Stores'), selected: _typeFilter == 'store',
                      visualDensity: VisualDensity.compact,
                      onSelected: (_) => setState(() { _typeFilter = 'store'; _selectedApartmentId = null; })),
                ]),
              ),
              const SizedBox(height: 12),
              if (_filtered.isEmpty)
                _InfoCard(message: 'No ${_typeFilter == "all" ? "" : _typeFilter} units available.')
              else
                DropdownButtonFormField<String>(
                  value: _selectedApartmentId,
                  decoration: const InputDecoration(labelText: 'Select your unit number'),
                  items: _filtered.map((a) {
                    final isStore = a['unit_type'] == 'store';
                    return DropdownMenuItem<String>(
                      value: a['id'].toString(),
                      child: Row(children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isStore
                                ? AppColors.accentLight.withAlpha(40)
                                : scheme.primary.withAlpha(30),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            isStore ? 'Store' : 'Apt',
                            style: TextStyle(
                              fontSize: 11, fontWeight: FontWeight.w600,
                              color: isStore ? AppColors.accentDark : scheme.primary,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Flexible(child: Text(
                          'Unit ${a['unit_number']} — Floor ${a['floor']}'
                          '${a['size_sqm'] != null ? ' — ${a['size_sqm']} m²' : ''}',
                          overflow: TextOverflow.ellipsis,
                        )),
                      ]),
                    );
                  }).toList(),
                  onChanged: (v) => setState(() => _selectedApartmentId = v),
                ),
            ],
          ],
        ],

        const SizedBox(height: 24),
        Row(children: [
          Expanded(child: OutlinedButton(
            onPressed: _claiming ? null : widget.onSkip,
            child: const Text('Skip for now'),
          )),
          const SizedBox(width: 12),
          Expanded(child: FilledButton(
            onPressed: (_selectedApartmentId == null || _claiming) ? null : _claim,
            child: _claiming
                ? const SizedBox(height: 20, width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Claim Unit'),
          )),
        ]),
      ],
    );
  }
}

// ── Done step ─────────────────────────────────────────────────────────────────

class _DoneStep extends StatelessWidget {
  final String role;
  final VoidCallback onFinish;
  const _DoneStep({super.key, required this.role, required this.onFinish});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 16),
        Icon(Icons.check_circle_rounded, size: 64, color: theme.colorScheme.primary),
        const SizedBox(height: 16),
        Text('Account Created!',
          textAlign: TextAlign.center,
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700, color: theme.colorScheme.primary)),
        const SizedBox(height: 12),
        Text(
          role == 'admin'
              ? 'Your buildings have been set up. Manage apartments, expenses, and payments from your dashboard.'
              : 'Your account is ready. Head to the dashboard to view your expenses and payments.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
        ),
        const SizedBox(height: 28),
        FilledButton(
          onPressed: onFinish,
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          child: const Text('Go to Dashboard',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
        ),
      ],
    );
  }
}

// ── Shared widgets ────────────────────────────────────────────────────────────

class _ErrorCard extends StatelessWidget {
  final String message;
  final VoidCallback? onClose;
  const _ErrorCard({required this.message, this.onClose});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.errorContainer, borderRadius: BorderRadius.circular(8)),
      child: Row(children: [
        Icon(Icons.error_outline, color: scheme.onErrorContainer, size: 20),
        const SizedBox(width: 10),
        Expanded(child: Text(message,
            style: TextStyle(color: scheme.onErrorContainer, fontSize: 13))),
        if (onClose != null) IconButton(
          icon: Icon(Icons.close, size: 18, color: scheme.onErrorContainer),
          constraints: const BoxConstraints(), padding: EdgeInsets.zero,
          onPressed: onClose,
        ),
      ]),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final String message;
  const _InfoCard({required this.message});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.secondaryContainer, borderRadius: BorderRadius.circular(8)),
      child: Row(children: [
        Icon(Icons.info_outline, color: scheme.onSecondaryContainer, size: 20),
        const SizedBox(width: 10),
        Expanded(child: Text(message,
            style: TextStyle(color: scheme.onSecondaryContainer, fontSize: 13))),
      ]),
    );
  }
}
