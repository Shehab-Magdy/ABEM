import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/utils/currency_formatter.dart';

/// Color-coded balance display chip.
///
/// - Positive balance (outstanding): red
/// - Zero balance (settled): green
/// - Negative balance (credit): blue
class BalanceChip extends StatelessWidget {
  final double balance;
  const BalanceChip({super.key, required this.balance});

  @override
  Widget build(BuildContext context) {
    final Color color;
    final String label;

    if (balance < 0) {
      color = AppColors.balanceCredit;
      label = 'Credit';
    } else if (balance == 0) {
      color = AppColors.balanceSettled;
      label = 'Settled';
    } else {
      color = AppColors.balanceOutstanding;
      label = 'Outstanding';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            formatCurrency(balance.abs()),
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w700,
              fontSize: 13,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w500,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}
