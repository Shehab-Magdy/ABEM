import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/utils/currency_formatter.dart';
import '../bloc/record_payment_cubit.dart';

/// Record payment screen with unit selector, amount, date, method, and review.
class RecordPaymentScreen extends StatefulWidget {
  const RecordPaymentScreen({super.key});

  @override
  State<RecordPaymentScreen> createState() => _RecordPaymentScreenState();
}

class _RecordPaymentScreenState extends State<RecordPaymentScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _notesController = TextEditingController();
  final _otherMethodController = TextEditingController();
  final _unitSearchController = TextEditingController();

  DateTime _selectedDate = DateTime.now();
  String _selectedMethod = 'cash';
  String? _selectedUnitId;
  String? _selectedUnitLabel;

  // These would be populated from building units
  final List<Map<String, dynamic>> _units = [];

  @override
  void dispose() {
    _amountController.dispose();
    _notesController.dispose();
    _otherMethodController.dispose();
    _unitSearchController.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> get _filteredUnits {
    final query = _unitSearchController.text.toLowerCase();
    if (query.isEmpty) return _units;
    return _units.where((u) {
      final label = u['unit_number']?.toString().toLowerCase() ?? '';
      final owner = u['owner_name']?.toString().toLowerCase() ?? '';
      return label.contains(query) || owner.contains(query);
    }).toList();
  }

  Map<String, dynamic> _buildPayload() {
    return {
      'apartment': _selectedUnitId,
      'amount': _amountController.text.trim(),
      'payment_date':
          '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
      'payment_method': _selectedMethod == 'other'
          ? _otherMethodController.text.trim()
          : _selectedMethod,
      if (_notesController.text.trim().isNotEmpty)
        'notes': _notesController.text.trim(),
    };
  }

  void _showReviewSheet() {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedUnitId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a unit')),
      );
      return;
    }

    final amount =
        double.tryParse(_amountController.text.trim()) ?? 0;
    final methodLabel = _selectedMethod == 'other'
        ? _otherMethodController.text.trim()
        : _selectedMethod;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Review Payment',
                style: Theme.of(ctx)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            _ConfirmRow(label: 'Unit', value: _selectedUnitLabel ?? '?'),
            _ConfirmRow(
                label: 'Amount', value: formatCurrency(amount)),
            _ConfirmRow(label: 'Method', value: methodLabel),
            _ConfirmRow(
              label: 'Date',
              value:
                  '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: BlocBuilder<RecordPaymentCubit, RecordPaymentState>(
                builder: (context, state) {
                  final isRecording = state is RecordPaymentRecording;
                  return FilledButton(
                    onPressed: isRecording
                        ? null
                        : () {
                            Navigator.of(ctx).pop();
                            context
                                .read<RecordPaymentCubit>()
                                .recordPayment(_buildPayload());
                          },
                    child: isRecording
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Confirm Payment'),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      key: const ValueKey('tc_s4_mob_record_payment'),
      appBar: AppBar(title: const Text('Record Payment')),
      body: BlocListener<RecordPaymentCubit, RecordPaymentState>(
        listener: (context, state) {
          if (state is RecordPaymentRecorded) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Payment recorded successfully')),
            );
            context.pop();
          }
          if (state is RecordPaymentError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message)),
            );
          }
        },
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // ── Unit selector (searchable) ──
              Text('Unit',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              TextField(
                controller: _unitSearchController,
                decoration: const InputDecoration(
                  hintText: 'Search units...',
                  prefixIcon: Icon(Icons.search),
                  border: OutlineInputBorder(),
                ),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 8),
              Container(
                constraints: const BoxConstraints(maxHeight: 160),
                decoration: BoxDecoration(
                  border: Border.all(color: theme.dividerColor),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: _filteredUnits.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Text('No units available',
                              style: TextStyle(
                                  color:
                                      theme.colorScheme.onSurfaceVariant)),
                        ),
                      )
                    : ListView.builder(
                        shrinkWrap: true,
                        itemCount: _filteredUnits.length,
                        itemBuilder: (ctx, i) {
                          final unit = _filteredUnits[i];
                          final id = unit['id']?.toString() ?? '';
                          final label =
                              'Unit ${unit['unit_number'] ?? '?'}';
                          final isSelected = _selectedUnitId == id;
                          return ListTile(
                            dense: true,
                            selected: isSelected,
                            selectedTileColor:
                                theme.colorScheme.primaryContainer,
                            title: Text(label),
                            subtitle: unit['owner_name'] != null
                                ? Text(unit['owner_name'] as String)
                                : null,
                            trailing: isSelected
                                ? const Icon(Icons.check_circle,
                                    size: 20)
                                : null,
                            onTap: () => setState(() {
                              _selectedUnitId = id;
                              _selectedUnitLabel = label;
                            }),
                          );
                        },
                      ),
              ),
              const SizedBox(height: 16),

              // ── Amount ──
              TextFormField(
                controller: _amountController,
                decoration: const InputDecoration(
                  labelText: 'Amount (EGP) *',
                  border: OutlineInputBorder(),
                  prefixText: 'EGP ',
                ),
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                validator: (v) {
                  if (v == null || v.trim().isEmpty) {
                    return 'Amount is required';
                  }
                  if (double.tryParse(v.trim()) == null) {
                    return 'Invalid amount';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // ── Date picker ──
              InkWell(
                onTap: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: _selectedDate,
                    firstDate: DateTime(2020),
                    lastDate:
                        DateTime.now().add(const Duration(days: 365)),
                  );
                  if (picked != null) {
                    setState(() => _selectedDate = picked);
                  }
                },
                child: InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Date *',
                    border: OutlineInputBorder(),
                    suffixIcon: Icon(Icons.calendar_today_outlined),
                  ),
                  child: Text(
                    '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // ── Payment method segmented button ──
              Text('Payment Method',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(
                    value: 'cash',
                    icon: Icon(Icons.money_outlined, size: 18),
                    label: Text('Cash'),
                  ),
                  ButtonSegment(
                    value: 'bank_transfer',
                    icon: Icon(Icons.account_balance_outlined, size: 18),
                    label: Text('Bank'),
                  ),
                  ButtonSegment(
                    value: 'mobile_wallet',
                    icon: Icon(Icons.phone_android_outlined, size: 18),
                    label: Text('Wallet'),
                  ),
                  ButtonSegment(
                    value: 'other',
                    icon: Icon(Icons.more_horiz, size: 18),
                    label: Text('Other'),
                  ),
                ],
                selected: {_selectedMethod},
                onSelectionChanged: (set) =>
                    setState(() => _selectedMethod = set.first),
              ),
              if (_selectedMethod == 'other') ...[
                const SizedBox(height: 12),
                TextFormField(
                  controller: _otherMethodController,
                  decoration: const InputDecoration(
                    labelText: 'Specify method *',
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) =>
                      _selectedMethod == 'other' &&
                              (v == null || v.trim().isEmpty)
                          ? 'Please specify the payment method'
                          : null,
                ),
              ],
              const SizedBox(height: 16),

              // ── Notes ──
              TextFormField(
                controller: _notesController,
                decoration: const InputDecoration(
                  labelText: 'Notes',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 24),

              // ── Review button ──
              FilledButton.icon(
                onPressed: _showReviewSheet,
                icon: const Icon(Icons.preview_outlined),
                label: const Text('Review Payment'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConfirmRow extends StatelessWidget {
  final String label;
  final String value;
  const _ConfirmRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: TextStyle(
                  color: theme.colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w500)),
          Text(value,
              style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
