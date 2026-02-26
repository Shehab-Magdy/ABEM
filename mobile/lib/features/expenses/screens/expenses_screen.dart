import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/expenses_api.dart';

class ExpensesScreen extends StatefulWidget {
  const ExpensesScreen({super.key});

  @override
  State<ExpensesScreen> createState() => _ExpensesScreenState();
}

class _ExpensesScreenState extends State<ExpensesScreen> {
  List<Map<String, dynamic>> _expenses = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadExpenses();
  }

  ExpensesApi get _api => ExpensesApi(apiClient: context.read<ApiClient>());

  Future<void> _loadExpenses() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final expenses = await _api.fetchExpenses();
      setState(() => _expenses = expenses);
    } catch (e) {
      setState(() => _error = 'Failed to load expenses.');
    } finally {
      setState(() => _loading = false);
    }
  }

  String _formatAmount(dynamic amount) {
    final num val = num.tryParse(amount?.toString() ?? '0') ?? 0;
    return NumberFormat('#,##0.00').format(val);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _loadExpenses,
        child: _loading
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
                            onPressed: _loadExpenses,
                            child: const Text('Retry')),
                      ],
                    ),
                  )
                : _expenses.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.receipt_long_outlined,
                                size: 64,
                                color: theme.colorScheme.onSurfaceVariant),
                            const SizedBox(height: 16),
                            Text('No expenses found.',
                                style: theme.textTheme.titleMedium?.copyWith(
                                    color:
                                        theme.colorScheme.onSurfaceVariant)),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _expenses.length,
                        itemBuilder: (ctx, i) {
                          final e = _expenses[i];
                          final isRecurring = e['is_recurring'] == true;
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor:
                                    theme.colorScheme.secondaryContainer,
                                child: Icon(Icons.receipt_long,
                                    color: theme.colorScheme
                                        .onSecondaryContainer),
                              ),
                              title: Text(e['title'] as String? ?? '',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w600)),
                              subtitle: Text(
                                '${e['expense_date'] ?? ''} · ${e['split_type'] ?? ''}'
                                '${isRecurring ? ' · Recurring' : ''}',
                              ),
                              trailing: Text(
                                _formatAmount(e['amount']),
                                style: theme.textTheme.titleSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: theme.colorScheme.primary),
                              ),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
