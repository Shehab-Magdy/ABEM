import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/building_form_cubit.dart';

class BuildingFormSheet extends StatefulWidget {
  final Map<String, dynamic>? initialBuilding;
  const BuildingFormSheet({super.key, this.initialBuilding});

  bool get isEdit => initialBuilding != null;

  @override
  State<BuildingFormSheet> createState() => _BuildingFormSheetState();
}

class _BuildingFormSheetState extends State<BuildingFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameCtrl;
  late final TextEditingController _addressCtrl;
  late final TextEditingController _cityCtrl;
  late final TextEditingController _countryCtrl;
  late final TextEditingController _floorsCtrl;
  late final TextEditingController _apartmentsCtrl;
  late final TextEditingController _storesCtrl;
  late final TextEditingController _descriptionCtrl;

  @override
  void initState() {
    super.initState();
    final initial = widget.initialBuilding ?? const <String, dynamic>{};
    _nameCtrl = TextEditingController(text: initial['name']?.toString() ?? '');
    _addressCtrl = TextEditingController(text: initial['address']?.toString() ?? '');
    _cityCtrl = TextEditingController(text: initial['city']?.toString() ?? '');
    _countryCtrl = TextEditingController(text: initial['country']?.toString() ?? '');
    _floorsCtrl = TextEditingController(
      text: (initial['num_floors'] ?? '1').toString(),
    );
    _apartmentsCtrl = TextEditingController(
      text: (initial['num_apartments'] ?? '0').toString(),
    );
    _storesCtrl = TextEditingController(
      text: (initial['num_stores'] ?? '0').toString(),
    );
    _descriptionCtrl = TextEditingController(text: initial['description']?.toString() ?? '');
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _addressCtrl.dispose();
    _cityCtrl.dispose();
    _countryCtrl.dispose();
    _floorsCtrl.dispose();
    _apartmentsCtrl.dispose();
    _storesCtrl.dispose();
    _descriptionCtrl.dispose();
    super.dispose();
  }

  Map<String, dynamic> _payload() => {
        'name': _nameCtrl.text.trim(),
        'address': _addressCtrl.text.trim(),
        'city': _cityCtrl.text.trim(),
        'country': _countryCtrl.text.trim(),
        'num_floors': int.tryParse(_floorsCtrl.text.trim()) ?? 1,
        'num_apartments': int.tryParse(_apartmentsCtrl.text.trim()) ?? 0,
        'num_stores': int.tryParse(_storesCtrl.text.trim()) ?? 0,
        'description': _descriptionCtrl.text.trim(),
      };

  String? _fieldError(BuildingFormState state, String field) {
    if (state is! BuildingFormError) return null;
    final fieldErrors = state.fieldErrors;
    final error = fieldErrors?[field];
    if (error is List && error.isNotEmpty) return error.first.toString();
    if (error is String) return error;
    return null;
  }

  void _submit(BuildContext context) {
    if (!_formKey.currentState!.validate()) return;
    final payload = _payload();
    final cubit = context.read<BuildingFormCubit>();
    if (widget.isEdit) {
      final id = widget.initialBuilding?['id']?.toString();
      if (id == null) return;
      cubit.updateBuilding(id, payload);
    } else {
      cubit.createBuilding(payload);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final media = MediaQuery.of(context);

    return BlocConsumer<BuildingFormCubit, BuildingFormState>(
      listener: (context, state) {
        if (state is BuildingFormSuccess) {
          Navigator.of(context).pop(state.building);
        }
      },
      builder: (context, state) {
        final isSubmitting = state is BuildingFormSubmitting;
        final generalError = state is BuildingFormError ? state.message : null;

        return AnimatedPadding(
          duration: const Duration(milliseconds: 200),
          padding: EdgeInsets.only(bottom: media.viewInsets.bottom),
          child: SafeArea(
            top: false,
            child: Material(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
              clipBehavior: Clip.antiAlias,
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: media.size.height * 0.85,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 40,
                      height: 4,
                      margin: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.outlineVariant,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                        child: Form(
                          key: _formKey,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.isEdit ? 'Edit Building' : 'New Building',
                                style: theme.textTheme.titleLarge
                                    ?.copyWith(fontWeight: FontWeight.w700),
                              ),
                              const SizedBox(height: 20),
                              if (generalError != null)
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 12),
                                  child: Text(
                                    generalError,
                                    style: TextStyle(color: theme.colorScheme.error),
                                  ),
                                ),
                              TextFormField(
                                key: const ValueKey('tc_s2_mob_building_name_field'),
                                controller: _nameCtrl,
                                decoration: InputDecoration(
                                  labelText: 'Name *',
                                  errorText: _fieldError(state, 'name'),
                                ),
                                validator: (value) =>
                                    (value == null || value.trim().isEmpty)
                                        ? 'Required'
                                        : null,
                              ),
                              const SizedBox(height: 12),
                              TextFormField(
                                key: const ValueKey('tc_s2_mob_building_address_field'),
                                controller: _addressCtrl,
                                decoration: InputDecoration(
                                  labelText: 'Address *',
                                  errorText: _fieldError(state, 'address'),
                                ),
                                validator: (value) =>
                                    (value == null || value.trim().isEmpty)
                                        ? 'Required'
                                        : null,
                              ),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      key: const ValueKey('tc_s2_mob_building_city_field'),
                                      controller: _cityCtrl,
                                      decoration: InputDecoration(
                                        labelText: 'City *',
                                        errorText: _fieldError(state, 'city'),
                                      ),
                                      validator: (value) =>
                                          (value == null || value.trim().isEmpty)
                                              ? 'Required'
                                              : null,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: TextFormField(
                                      key: const ValueKey('tc_s2_mob_building_country_field'),
                                      controller: _countryCtrl,
                                      decoration: InputDecoration(
                                        labelText: 'Country',
                                        errorText: _fieldError(state, 'country'),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      key: const ValueKey('tc_s2_mob_building_floors_field'),
                                      controller: _floorsCtrl,
                                      keyboardType: TextInputType.number,
                                      decoration: InputDecoration(
                                        labelText: 'Floors *',
                                        errorText: _fieldError(state, 'num_floors'),
                                      ),
                                      validator: (value) {
                                        final parsed = int.tryParse(value ?? '');
                                        if (parsed == null || parsed < 1) {
                                          return 'Must be ≥ 1';
                                        }
                                        return null;
                                      },
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: TextFormField(
                                      key: const ValueKey('tc_s2_mob_building_apartments_field'),
                                      controller: _apartmentsCtrl,
                                      keyboardType: TextInputType.number,
                                      decoration: InputDecoration(
                                        labelText: '# Apartments',
                                        errorText: _fieldError(state, 'num_apartments'),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: TextFormField(
                                      key: const ValueKey('tc_s2_mob_building_stores_field'),
                                      controller: _storesCtrl,
                                      keyboardType: TextInputType.number,
                                      decoration: InputDecoration(
                                        labelText: '# Stores',
                                        errorText: _fieldError(state, 'num_stores'),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              TextFormField(
                                key: const ValueKey('tc_s2_mob_building_description_field'),
                                controller: _descriptionCtrl,
                                minLines: 2,
                                maxLines: 4,
                                decoration: InputDecoration(
                                  labelText: 'Notes',
                                  helperText: 'Visible internally for admins',
                                  errorText: _fieldError(state, 'description'),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
                      child: SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          key: const ValueKey('tc_s2_mob_building_save_btn'),
                          onPressed: isSubmitting ? null : () => _submit(context),
                          icon: isSubmitting
                              ? SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: theme.colorScheme.onPrimary,
                                  ),
                                )
                              : const Icon(Icons.save_outlined),
                          label: Text(widget.isEdit ? 'Save Changes' : 'Create Building'),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
