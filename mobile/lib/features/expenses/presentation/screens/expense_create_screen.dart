import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../../../core/utils/round_up.dart';
import '../../../buildings/data/repositories/building_repository.dart';
import '../../../../injection.dart';
import '../bloc/expense_form_cubit.dart';

/// Multi-step expense creation screen using PageView.
class ExpenseCreateScreen extends StatefulWidget {
  const ExpenseCreateScreen({super.key});

  @override
  State<ExpenseCreateScreen> createState() => _ExpenseCreateScreenState();
}

class _ExpenseCreateScreenState extends State<ExpenseCreateScreen> {
  final PageController _pageController = PageController();
  int _currentStep = 0;

  // Step 1 fields
  final _titleController = TextEditingController();
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  DateTime _selectedDate = DateTime.now();
  String? _selectedCategoryId;
  String? _selectedCategoryName;
  bool _isRecurring = false;

  // Step 2 fields
  String _splitType = 'equal_all';
  final Map<String, double> _customWeights = {};
  final Map<String, bool> _selectedUnits = {};
  List<Map<String, dynamic>> _units = [];
  bool _unitsLoading = false;
  String? _unitsError;

  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      context.read<ExpenseFormCubit>().loadCategories();
      _loadUnits();
    });
  }

  Future<void> _loadUnits() async {
    setState(() {
      _unitsLoading = true;
      _unitsError = null;
    });
    final repo = getIt<BuildingRepository>();
    final result = await repo.getBuildingUnits('');
    result.fold(
      (failure) => setState(() {
        _unitsError = failure.message;
        _unitsLoading = false;
      }),
      (units) => setState(() {
        _units = units;
        _unitsLoading = false;
      }),
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    _titleController.dispose();
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  void _goToStep(int step) {
    if (step == 1 && !_formKey.currentState!.validate()) return;
    setState(() => _currentStep = step);
    _pageController.animateToPage(
      step,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  double get _totalAmount =>
      double.tryParse(_amountController.text) ?? 0;

  double _estimatedTotal() {
    if (_splitType == 'custom') {
      final selected = _selectedUnits.entries
          .where((e) => e.value)
          .toList();
      if (selected.isEmpty) return 0;
      double totalWeight = 0;
      for (final entry in selected) {
        totalWeight += _customWeights[entry.key] ?? 1;
      }
      if (totalWeight == 0) return 0;
      double total = 0;
      for (final entry in selected) {
        final weight = _customWeights[entry.key] ?? 1;
        final share = (_totalAmount * weight) / totalWeight;
        total += roundUpToNearest5(share);
      }
      return total;
    }
    return _totalAmount;
  }

  Map<String, dynamic> _buildPayload() {
    return {
      'title': _titleController.text.trim(),
      'amount': _amountController.text.trim(),
      'expense_date':
          '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
      if (_selectedCategoryId != null) 'category': _selectedCategoryId,
      'description': _descriptionController.text.trim(),
      'is_recurring': _isRecurring,
      'split_type': _splitType,
      if (_splitType == 'custom')
        'custom_shares': _selectedUnits.entries
            .where((e) => e.value)
            .map((e) => {
                  'apartment': e.key,
                  'weight': _customWeights[e.key] ?? 1,
                })
            .toList(),
    };
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      key: const ValueKey('tc_s3_mob_expense_create'),
      appBar: AppBar(
        title: Text('Create Expense (${_currentStep + 1}/3)'),
      ),
      body: BlocConsumer<ExpenseFormCubit, ExpenseFormState>(
        listener: (context, state) {
          if (state is ExpenseFormCreated) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Expense created successfully')),
            );
            context.pop();
          }
          if (state is ExpenseFormError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message)),
            );
          }
          if (state is ExpenseFormCategoriesLoaded) {
            // Categories loaded — no action needed, builder handles it
          }
        },
        builder: (context, state) {
          final categories = state is ExpenseFormCategoriesLoaded
              ? state.categories
              : <Map<String, dynamic>>[];

          return Column(
            children: [
              // ── Step indicators ──
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: List.generate(3, (i) {
                    final isActive = i <= _currentStep;
                    return Expanded(
                      child: Container(
                        height: 4,
                        margin: const EdgeInsets.symmetric(horizontal: 2),
                        decoration: BoxDecoration(
                          color: isActive
                              ? theme.colorScheme.primary
                              : theme.colorScheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    );
                  }),
                ),
              ),

              // ── Pages ──
              Expanded(
                child: PageView(
                  controller: _pageController,
                  physics: const NeverScrollableScrollPhysics(),
                  children: [
                    _Step1Details(
                      formKey: _formKey,
                      titleController: _titleController,
                      amountController: _amountController,
                      descriptionController: _descriptionController,
                      selectedDate: _selectedDate,
                      onDateChanged: (d) =>
                          setState(() => _selectedDate = d),
                      selectedCategoryId: _selectedCategoryId,
                      selectedCategoryName: _selectedCategoryName,
                      categories: categories,
                      onCategoryChanged: (id, name) => setState(() {
                        _selectedCategoryId = id;
                        _selectedCategoryName = name;
                      }),
                      isRecurring: _isRecurring,
                      onRecurringChanged: (v) =>
                          setState(() => _isRecurring = v),
                      onNext: () => _goToStep(1),
                    ),
                    _Step2SplitType(
                      splitType: _splitType,
                      onSplitTypeChanged: (t) =>
                          setState(() => _splitType = t),
                      units: _units,
                      unitsLoading: _unitsLoading,
                      unitsError: _unitsError,
                      onReloadUnits: _loadUnits,
                      selectedUnits: _selectedUnits,
                      customWeights: _customWeights,
                      totalAmount: _totalAmount,
                      estimatedTotal: _estimatedTotal(),
                      onBack: () => _goToStep(0),
                      onNext: () => _goToStep(2),
                      onUnitsChanged: () => setState(() {}),
                    ),
                    _Step3Review(
                      title: _titleController.text,
                      amount: _totalAmount,
                      date: _selectedDate,
                      categoryName: _selectedCategoryName,
                      splitType: _splitType,
                      isRecurring: _isRecurring,
                      description: _descriptionController.text,
                      estimatedTotal: _estimatedTotal(),
                      isSubmitting: state is ExpenseFormSubmitting,
                      onBack: () => _goToStep(1),
                      onSubmit: () {
                        context
                            .read<ExpenseFormCubit>()
                            .createExpense(_buildPayload());
                      },
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

// ── Step 1: Details ─────────────────────────────────────────────────────────

class _Step1Details extends StatelessWidget {
  final GlobalKey<FormState> formKey;
  final TextEditingController titleController;
  final TextEditingController amountController;
  final TextEditingController descriptionController;
  final DateTime selectedDate;
  final ValueChanged<DateTime> onDateChanged;
  final String? selectedCategoryId;
  final String? selectedCategoryName;
  final List<Map<String, dynamic>> categories;
  final void Function(String? id, String? name) onCategoryChanged;
  final bool isRecurring;
  final ValueChanged<bool> onRecurringChanged;
  final VoidCallback onNext;

  const _Step1Details({
    required this.formKey,
    required this.titleController,
    required this.amountController,
    required this.descriptionController,
    required this.selectedDate,
    required this.onDateChanged,
    required this.selectedCategoryId,
    required this.selectedCategoryName,
    required this.categories,
    required this.onCategoryChanged,
    required this.isRecurring,
    required this.onRecurringChanged,
    required this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Form(
      key: formKey,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Expense Details',
              style: theme.textTheme.titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          TextFormField(
            controller: titleController,
            decoration: const InputDecoration(
              labelText: 'Title *',
              border: OutlineInputBorder(),
            ),
            validator: (v) =>
                v == null || v.trim().isEmpty ? 'Title is required' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: amountController,
            decoration: const InputDecoration(
              labelText: 'Amount (EGP) *',
              border: OutlineInputBorder(),
              prefixText: 'EGP ',
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            validator: (v) {
              if (v == null || v.trim().isEmpty) return 'Amount is required';
              if (double.tryParse(v.trim()) == null) return 'Invalid amount';
              return null;
            },
          ),
          const SizedBox(height: 16),
          InkWell(
            onTap: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: selectedDate,
                firstDate: DateTime(2020),
                lastDate: DateTime.now().add(const Duration(days: 365)),
              );
              if (picked != null) onDateChanged(picked);
            },
            child: InputDecorator(
              decoration: const InputDecoration(
                labelText: 'Date *',
                border: OutlineInputBorder(),
                suffixIcon: Icon(Icons.calendar_today_outlined),
              ),
              child: Text(
                '${selectedDate.year}-${selectedDate.month.toString().padLeft(2, '0')}-${selectedDate.day.toString().padLeft(2, '0')}',
              ),
            ),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: selectedCategoryId,
            decoration: const InputDecoration(
              labelText: 'Category *',
              border: OutlineInputBorder(),
            ),
            items: categories.map((cat) {
              return DropdownMenuItem<String>(
                value: cat['id']?.toString(),
                child: Text(cat['name'] as String? ?? ''),
              );
            }).toList(),
            onChanged: (id) {
              final cat = categories.firstWhere(
                (c) => c['id']?.toString() == id,
                orElse: () => {},
              );
              onCategoryChanged(id, cat['name'] as String?);
            },
            validator: (v) => v == null ? 'Category is required' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: descriptionController,
            decoration: const InputDecoration(
              labelText: 'Description',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 16),
          SwitchListTile(
            title: const Text('Recurring'),
            subtitle: const Text('This expense repeats monthly'),
            value: isRecurring,
            onChanged: onRecurringChanged,
            contentPadding: EdgeInsets.zero,
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: onNext,
            child: const Text('Next: Split Type'),
          ),
        ],
      ),
    );
  }
}

// ── Step 2: Split Type ──────────────────────────────────────────────────────

class _Step2SplitType extends StatelessWidget {
  final String splitType;
  final ValueChanged<String> onSplitTypeChanged;
  final List<Map<String, dynamic>> units;
  final bool unitsLoading;
  final String? unitsError;
  final Map<String, bool> selectedUnits;
  final Map<String, double> customWeights;
  final double totalAmount;
  final double estimatedTotal;
  final VoidCallback onBack;
  final VoidCallback onNext;
  final VoidCallback onUnitsChanged;
  final Future<void> Function() onReloadUnits;

  const _Step2SplitType({
    required this.splitType,
    required this.onSplitTypeChanged,
    required this.units,
    required this.unitsLoading,
    required this.unitsError,
    required this.selectedUnits,
    required this.customWeights,
    required this.totalAmount,
    required this.estimatedTotal,
    required this.onBack,
    required this.onNext,
    required this.onUnitsChanged,
    required this.onReloadUnits,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Split Type',
            style: theme.textTheme.titleLarge
                ?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 16),
        ..._splitOptions.map((option) {
          return RadioListTile<String>(
            title: Text(option['label']!),
            subtitle: Text(option['description']!),
            value: option['value']!,
            groupValue: splitType,
            onChanged: (v) {
              if (v != null) onSplitTypeChanged(v);
            },
          );
        }),
        if (splitType == 'custom') ...[
          const SizedBox(height: 16),
          Text('Select Units & Weights',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          if (unitsLoading)
            const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (unitsError != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Text(
                    'Failed to load units\n${unitsError ?? ''}',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: theme.colorScheme.error),
                  ),
                  const SizedBox(height: 8),
                  FilledButton(
                    onPressed: onReloadUnits,
                    child: const Text('Try Again'),
                  ),
                ],
              ),
            )
          else if (units.isEmpty)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text('No units available',
                  style: TextStyle(
                      color: theme.colorScheme.onSurfaceVariant)),
            )
          else
            ...units.map((unit) {
              final unitId = unit['id']?.toString() ?? '';
              final unitNumber = unit['unit_number']?.toString() ?? '?';
              final isSelected = selectedUnits[unitId] ?? false;
              final weight = customWeights[unitId] ?? 1;

              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      Checkbox(
                        value: isSelected,
                        onChanged: (v) {
                          selectedUnits[unitId] = v ?? false;
                          onUnitsChanged();
                        },
                      ),
                      Expanded(
                        child: Text('Unit $unitNumber',
                            style: const TextStyle(
                                fontWeight: FontWeight.w600)),
                      ),
                      SizedBox(
                        width: 80,
                        child: TextFormField(
                          initialValue: weight.toStringAsFixed(0),
                          decoration: const InputDecoration(
                            labelText: 'Weight',
                            isDense: true,
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.number,
                          enabled: isSelected,
                          onChanged: (v) {
                            customWeights[unitId] =
                                double.tryParse(v) ?? 1;
                            onUnitsChanged();
                          },
                        ),
                      ),
                      if (isSelected) ...[
                        const SizedBox(width: 8),
                        Text(
                          formatCurrency(
                            roundUpToNearest5(
                              _sharePreview(unitId),
                            ),
                          ),
                          style: TextStyle(
                            fontSize: 12,
                            color: theme.colorScheme.primary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            }),
          const SizedBox(height: 8),
          Card(
            color: theme.colorScheme.primaryContainer,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Estimated Total',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.w600)),
                  Text(
                    formatCurrency(estimatedTotal),
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: theme.colorScheme.onPrimaryContainer,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: onBack,
                child: const Text('Back'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton(
                onPressed: onNext,
                child: const Text('Next: Review'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  double _sharePreview(String unitId) {
    final selected =
        selectedUnits.entries.where((e) => e.value).toList();
    if (selected.isEmpty) return 0;
    double totalWeight = 0;
    for (final entry in selected) {
      totalWeight += customWeights[entry.key] ?? 1;
    }
    if (totalWeight == 0) return 0;
    final weight = customWeights[unitId] ?? 1;
    return (totalAmount * weight) / totalWeight;
  }

  static const _splitOptions = [
    {
      'value': 'equal_all',
      'label': 'Equal — All Units',
      'description': 'Split equally among all units in the building',
    },
    {
      'value': 'apartments',
      'label': 'Apartments Only',
      'description': 'Split among apartment units only',
    },
    {
      'value': 'stores',
      'label': 'Stores Only',
      'description': 'Split among store units only',
    },
    {
      'value': 'custom',
      'label': 'Custom',
      'description': 'Pick units and set weight per unit',
    },
  ];
}

// ── Step 3: Review & Submit ─────────────────────────────────────────────────

class _Step3Review extends StatelessWidget {
  final String title;
  final double amount;
  final DateTime date;
  final String? categoryName;
  final String splitType;
  final bool isRecurring;
  final String description;
  final double estimatedTotal;
  final bool isSubmitting;
  final VoidCallback onBack;
  final VoidCallback onSubmit;

  const _Step3Review({
    required this.title,
    required this.amount,
    required this.date,
    required this.categoryName,
    required this.splitType,
    required this.isRecurring,
    required this.description,
    required this.estimatedTotal,
    required this.isSubmitting,
    required this.onBack,
    required this.onSubmit,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Review & Submit',
            style: theme.textTheme.titleLarge
                ?.copyWith(fontWeight: FontWeight.w700)),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _ReviewRow(label: 'Title', value: title),
                _ReviewRow(
                    label: 'Amount', value: formatCurrency(amount)),
                _ReviewRow(
                  label: 'Date',
                  value:
                      '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}',
                ),
                _ReviewRow(
                    label: 'Category',
                    value: categoryName ?? 'None'),
                _ReviewRow(
                    label: 'Split Type',
                    value: _splitLabel(splitType)),
                _ReviewRow(
                    label: 'Recurring',
                    value: isRecurring ? 'Yes' : 'No'),
                if (description.isNotEmpty)
                  _ReviewRow(
                      label: 'Description', value: description),
                if (splitType == 'custom')
                  _ReviewRow(
                    label: 'Estimated Total',
                    value: formatCurrency(estimatedTotal),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: isSubmitting ? null : onBack,
                child: const Text('Back'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton(
                onPressed: isSubmitting ? null : onSubmit,
                child: isSubmitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Submit'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  String _splitLabel(String type) {
    switch (type) {
      case 'equal_all':
        return 'Equal — All Units';
      case 'apartments':
        return 'Apartments Only';
      case 'stores':
        return 'Stores Only';
      case 'custom':
        return 'Custom';
      default:
        return type;
    }
  }
}

class _ReviewRow extends StatelessWidget {
  final String label;
  final String value;
  const _ReviewRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: TextStyle(
                  color: theme.colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w500)),
          const SizedBox(width: 16),
          Flexible(
            child: Text(value,
                textAlign: TextAlign.end,
                style: const TextStyle(fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}
