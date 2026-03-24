import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/datasources/asset_remote_data_source.dart';
import '../../data/repositories/asset_repository.dart';

/// Asset creation screen with form fields for name, type, description,
/// acquisition date, and acquisition value.
class AssetCreateScreen extends StatefulWidget {
  const AssetCreateScreen({super.key});

  @override
  State<AssetCreateScreen> createState() => _AssetCreateScreenState();
}

class _AssetCreateScreenState extends State<AssetCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _descriptionCtrl = TextEditingController();
  final _acqDateCtrl = TextEditingController();
  final _acqValueCtrl = TextEditingController();
  String _selectedType = 'equipment';
  DateTime? _selectedDate;
  bool _submitting = false;

  static const _assetTypes = [
    'vehicle',
    'equipment',
    'furniture',
    'electronics',
    'property',
    'other',
  ];

  @override
  void dispose() {
    _nameCtrl.dispose();
    _descriptionCtrl.dispose();
    _acqDateCtrl.dispose();
    _acqValueCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);

    final repo = AssetRepository(context.read<AssetRemoteDataSource>());
    final result = await repo.createAsset({
      'name': _nameCtrl.text.trim(),
      'asset_type': _selectedType,
      if (_descriptionCtrl.text.trim().isNotEmpty)
        'description': _descriptionCtrl.text.trim(),
      if (_selectedDate != null)
        'acquisition_date':
            '${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}',
      if (_acqValueCtrl.text.trim().isNotEmpty)
        'acquisition_value': _acqValueCtrl.text.trim(),
    });

    if (!mounted) return;
    setState(() => _submitting = false);

    result.fold(
      (failure) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(failure.message),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      },
      (_) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Asset created successfully')),
        );
        Navigator.of(context).pop(true);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const ValueKey('tc_s8_mob_asset_create'),
      appBar: AppBar(title: const Text('Create Asset')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _nameCtrl,
                decoration: const InputDecoration(labelText: 'Name *'),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedType,
                decoration: const InputDecoration(labelText: 'Type *'),
                items: _assetTypes
                    .map((t) => DropdownMenuItem(
                          value: t,
                          child: Text(
                            t[0].toUpperCase() + t.substring(1),
                          ),
                        ))
                    .toList(),
                onChanged: (v) {
                  if (v != null) setState(() => _selectedType = v);
                },
                validator: (v) =>
                    (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descriptionCtrl,
                decoration: const InputDecoration(labelText: 'Description'),
                maxLines: 3,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _acqDateCtrl,
                decoration: const InputDecoration(
                  labelText: 'Acquisition Date',
                  suffixIcon: Icon(Icons.calendar_today, size: 18),
                ),
                readOnly: true,
                onTap: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: DateTime.now(),
                    firstDate: DateTime(2000),
                    lastDate: DateTime.now(),
                  );
                  if (picked != null) {
                    setState(() {
                      _selectedDate = picked;
                      _acqDateCtrl.text =
                          '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
                    });
                  }
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _acqValueCtrl,
                decoration:
                    const InputDecoration(labelText: 'Acquisition Value'),
                keyboardType: TextInputType.number,
                validator: (v) {
                  if (v != null && v.isNotEmpty && double.tryParse(v) == null) {
                    return 'Enter a valid number';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _submitting ? null : _submit,
                  child: _submitting
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Create Asset'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
