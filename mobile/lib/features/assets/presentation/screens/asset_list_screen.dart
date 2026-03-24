import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/utils/currency_formatter.dart';
import '../bloc/asset_list_cubit.dart';
import '../bloc/asset_sale_cubit.dart';
import 'asset_create_screen.dart';

/// Admin asset list screen with filter chips, summary row, and sale recording.
class AssetListScreen extends StatefulWidget {
  const AssetListScreen({super.key});

  @override
  State<AssetListScreen> createState() => _AssetListScreenState();
}

class _AssetListScreenState extends State<AssetListScreen> {
  String _filter = 'all'; // all, active, sold

  List<Map<String, dynamic>> _applyFilter(
    List<Map<String, dynamic>> assets,
  ) {
    switch (_filter) {
      case 'active':
        return assets.where((a) => a['is_sold'] != true).toList();
      case 'sold':
        return assets.where((a) => a['is_sold'] == true).toList();
      default:
        return assets;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      key: const ValueKey('tc_s8_mob_asset_list'),
      appBar: AppBar(title: const Text('Building Assets')),
      body: Column(
        children: [
          // ── Filter chips ──────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Row(
              children: [
                _FilterChip(
                  label: 'All',
                  selected: _filter == 'all',
                  onTap: () => setState(() => _filter = 'all'),
                ),
                const SizedBox(width: 8),
                _FilterChip(
                  label: 'Active',
                  selected: _filter == 'active',
                  onTap: () => setState(() => _filter = 'active'),
                ),
                const SizedBox(width: 8),
                _FilterChip(
                  label: 'Sold',
                  selected: _filter == 'sold',
                  onTap: () => setState(() => _filter = 'sold'),
                ),
              ],
            ),
          ),

          // ── Content ───────────────────────────────────────────────────
          Expanded(
            child: BlocConsumer<AssetSaleCubit, AssetSaleState>(
              listener: (context, saleState) {
                if (saleState is AssetSaleSold) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Sale recorded successfully')),
                  );
                  context.read<AssetListCubit>().refresh();
                }
                if (saleState is AssetSaleError) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(saleState.message),
                      backgroundColor: colorScheme.error,
                    ),
                  );
                }
              },
              builder: (context, saleState) {
                return BlocBuilder<AssetListCubit, AssetListState>(
                  builder: (context, state) {
                    if (state is AssetListLoading) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (state is AssetListError) {
                      return _ErrorView(
                        message: state.message,
                        onRetry: () =>
                            context.read<AssetListCubit>().loadAssets(),
                      );
                    }
                    if (state is AssetListLoaded) {
                      final filtered = _applyFilter(state.assets);
                      return RefreshIndicator(
                        onRefresh: () =>
                            context.read<AssetListCubit>().refresh(),
                        child: ListView(
                          padding: const EdgeInsets.all(16),
                          children: [
                            _SummaryRow(
                              totalAssets: state.assets.length,
                              totalSaleProceeds: state.totalSaleProceeds,
                            ),
                            const SizedBox(height: 12),
                            if (filtered.isEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 48),
                                child: Center(
                                  child: Text(
                                    'No assets found.',
                                    style: TextStyle(
                                      color: colorScheme.onSurfaceVariant,
                                    ),
                                  ),
                                ),
                              )
                            else
                              ...filtered.map(
                                (asset) => _AssetCard(
                                  asset: asset,
                                  onTap: () {
                                    if (asset['is_sold'] != true) {
                                      _showRecordSaleSheet(context, asset);
                                    }
                                  },
                                ),
                              ),
                          ],
                        ),
                      );
                    }
                    return const SizedBox.shrink();
                  },
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        key: const ValueKey('tc_s8_mob_asset_create_fab'),
        onPressed: () => _navigateToCreate(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _navigateToCreate(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const AssetCreateScreen()),
    );
  }

  void _showRecordSaleSheet(
    BuildContext context,
    Map<String, dynamic> asset,
  ) {
    final saleDateCtrl = TextEditingController();
    final salePriceCtrl = TextEditingController();
    final buyerNameCtrl = TextEditingController();
    final buyerContactCtrl = TextEditingController();
    final notesCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();
    DateTime? selectedDate;

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
          child: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Record Sale',
                    style: Theme.of(ctx)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(ctx)
                          .colorScheme
                          .errorContainer
                          .withAlpha(80),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.warning_amber_rounded,
                          color: Theme.of(ctx).colorScheme.error,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'This action is permanent',
                            style: TextStyle(
                              color: Theme.of(ctx).colorScheme.error,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: saleDateCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Sale Date *',
                      suffixIcon: Icon(Icons.calendar_today, size: 18),
                    ),
                    readOnly: true,
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Required' : null,
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: ctx,
                        initialDate: DateTime.now(),
                        firstDate: DateTime(2000),
                        lastDate: DateTime.now(),
                      );
                      if (picked != null) {
                        setSheetState(() {
                          selectedDate = picked;
                          saleDateCtrl.text =
                              '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: salePriceCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Sale Price *'),
                    keyboardType: TextInputType.number,
                    validator: (v) {
                      if (v == null || v.isEmpty) return 'Required';
                      if (double.tryParse(v) == null) return 'Enter a number';
                      return null;
                    },
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: buyerNameCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Buyer Name'),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: buyerContactCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Buyer Contact'),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: notesCtrl,
                    decoration: const InputDecoration(labelText: 'Notes'),
                    maxLines: 2,
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      style: FilledButton.styleFrom(
                        backgroundColor:
                            Theme.of(ctx).colorScheme.error,
                      ),
                      onPressed: () {
                        if (!formKey.currentState!.validate()) return;
                        _confirmSale(
                          ctx,
                          asset,
                          selectedDate,
                          salePriceCtrl.text,
                          buyerNameCtrl.text,
                          buyerContactCtrl.text,
                          notesCtrl.text,
                        );
                      },
                      child: const Text('Record Sale'),
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

  void _confirmSale(
    BuildContext ctx,
    Map<String, dynamic> asset,
    DateTime? saleDate,
    String salePrice,
    String buyerName,
    String buyerContact,
    String notes,
  ) {
    showDialog(
      context: ctx,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Confirm Sale'),
        content: const Text(
          'Are you sure you want to record this sale? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(dialogCtx).colorScheme.error,
            ),
            onPressed: () {
              Navigator.pop(dialogCtx);
              Navigator.pop(ctx);
              final assetId = asset['id']?.toString() ?? '';
              context.read<AssetSaleCubit>().recordSale(assetId, {
                'sale_date': saleDate != null
                    ? '${saleDate.year}-${saleDate.month.toString().padLeft(2, '0')}-${saleDate.day.toString().padLeft(2, '0')}'
                    : null,
                'sale_price': salePrice,
                if (buyerName.isNotEmpty) 'buyer_name': buyerName,
                if (buyerContact.isNotEmpty) 'buyer_contact': buyerContact,
                if (notes.isNotEmpty) 'notes': notes,
              });
            },
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _FilterChip({
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

class _SummaryRow extends StatelessWidget {
  final int totalAssets;
  final double totalSaleProceeds;

  const _SummaryRow({
    required this.totalAssets,
    required this.totalSaleProceeds,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Column(
                children: [
                  Text(
                    '$totalAssets',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Total Assets',
                    style: TextStyle(
                      fontSize: 12,
                      color: colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            Container(
              width: 1,
              height: 32,
              color: colorScheme.outlineVariant,
            ),
            Expanded(
              child: Column(
                children: [
                  Text(
                    formatCurrency(totalSaleProceeds),
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Total Sale Proceeds',
                    style: TextStyle(
                      fontSize: 12,
                      color: colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AssetCard extends StatelessWidget {
  final Map<String, dynamic> asset;
  final VoidCallback onTap;

  const _AssetCard({required this.asset, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final name = asset['name'] as String? ?? '';
    final type = asset['asset_type'] as String? ?? 'other';
    final acquisitionValue =
        double.tryParse(asset['acquisition_value']?.toString() ?? '0') ?? 0;
    final isSold = asset['is_sold'] as bool? ?? false;

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
                child: Icon(
                  _iconForType(type),
                  color: colorScheme.onPrimaryContainer,
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
                            name,
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 16,
                            ),
                          ),
                        ),
                        if (isSold)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: colorScheme.errorContainer,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              'SOLD',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: colorScheme.onErrorContainer,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: colorScheme.secondaryContainer,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            _formatType(type),
                            style: TextStyle(
                              fontSize: 11,
                              color: colorScheme.onSecondaryContainer,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          formatCurrency(acquisitionValue),
                          style: TextStyle(
                            fontSize: 13,
                            color: colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (!isSold)
                Icon(
                  Icons.chevron_right,
                  color: colorScheme.onSurfaceVariant,
                ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _iconForType(String type) {
    switch (type.toLowerCase()) {
      case 'vehicle':
        return Icons.directions_car;
      case 'equipment':
        return Icons.build;
      case 'furniture':
        return Icons.chair;
      case 'electronics':
        return Icons.devices;
      case 'property':
        return Icons.home;
      default:
        return Icons.category;
    }
  }

  String _formatType(String type) {
    if (type.isEmpty) return 'Other';
    return type[0].toUpperCase() + type.substring(1).toLowerCase();
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
