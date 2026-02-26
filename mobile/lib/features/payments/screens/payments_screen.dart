import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/payments_api.dart';

class PaymentsScreen extends StatefulWidget {
  const PaymentsScreen({super.key});

  @override
  State<PaymentsScreen> createState() => _PaymentsScreenState();
}

class _PaymentsScreenState extends State<PaymentsScreen> {
  List<Map<String, dynamic>> _payments = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPayments();
  }

  PaymentsApi get _api => PaymentsApi(apiClient: context.read<ApiClient>());

  Future<void> _loadPayments() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payments = await _api.fetchPayments();
      setState(() => _payments = payments);
    } catch (e) {
      setState(() => _error = 'Failed to load payments.');
    } finally {
      setState(() => _loading = false);
    }
  }

  String _formatAmount(dynamic amount) {
    final num val = num.tryParse(amount?.toString() ?? '0') ?? 0;
    return NumberFormat('#,##0.00').format(val);
  }

  Color _statusColor(String? status, ColorScheme cs) {
    switch (status) {
      case 'confirmed':
        return cs.tertiary;
      case 'pending':
        return cs.secondary;
      case 'rejected':
        return cs.error;
      default:
        return cs.outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _loadPayments,
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
                            onPressed: _loadPayments,
                            child: const Text('Retry')),
                      ],
                    ),
                  )
                : _payments.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.payment_outlined,
                                size: 64,
                                color: theme.colorScheme.onSurfaceVariant),
                            const SizedBox(height: 16),
                            Text('No payments found.',
                                style: theme.textTheme.titleMedium?.copyWith(
                                    color:
                                        theme.colorScheme.onSurfaceVariant)),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _payments.length,
                        itemBuilder: (ctx, i) {
                          final p = _payments[i];
                          final statusStr = p['status'] as String?;
                          final statusColor = _statusColor(
                              statusStr, theme.colorScheme);
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor:
                                    theme.colorScheme.tertiaryContainer,
                                child: Icon(Icons.payment,
                                    color: theme
                                        .colorScheme.onTertiaryContainer),
                              ),
                              title: Text(
                                p['payment_date'] as String? ?? '',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600),
                              ),
                              subtitle: Text(
                                  p['payment_method'] as String? ?? ''),
                              trailing: Column(
                                mainAxisAlignment:
                                    MainAxisAlignment.center,
                                crossAxisAlignment:
                                    CrossAxisAlignment.end,
                                children: [
                                  Text(
                                    _formatAmount(p['amount']),
                                    style: theme.textTheme.titleSmall
                                        ?.copyWith(
                                            fontWeight: FontWeight.bold,
                                            color:
                                                theme.colorScheme.primary),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: statusColor.withOpacity(0.15),
                                      borderRadius:
                                          BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      statusStr ?? '',
                                      style: TextStyle(
                                          fontSize: 11,
                                          color: statusColor,
                                          fontWeight: FontWeight.w600),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
