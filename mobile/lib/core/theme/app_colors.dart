import 'package:flutter/material.dart';

/// All color constants for the ABEM design system.
class AppColors {
  AppColors._();

  // ── Brand ────────────────────────────────────────────────
  static const primary = Color(0xFF1A6B5A);
  static const primaryLight = Color(0xFF4CAF82);
  static const primaryDark = Color(0xFF0D4A3E);

  static const secondary = Color(0xFF4CAF82);
  static const secondaryLight = Color(0xFFD1FAE5);

  static const accent = Color(0xFFF59E0B);
  static const accentDark = Color(0xFFD97706);
  static const accentLight = Color(0xFFFEF3C7);

  // ── Neutrals ─────────────────────────────────────────────
  static const neutralDark = Color(0xFF1F2937);
  static const neutralMid = Color(0xFF6B7280);
  static const backgroundLight = Color(0xFFF8FAFB);
  static const backgroundDark = Color(0xFF141A18);
  static const surfaceDark = Color(0xFF1E2826);

  // ── Semantic ─────────────────────────────────────────────
  static const danger = Color(0xFFD32F2F);
  static const dangerDark = Color(0xFFEF5350);
  static const purple = Color(0xFF7C3AED);
  static const orange = Color(0xFFEA580C);

  // ── Balance chip colors (same in both themes) ────────────
  static const balanceSettled = Color(0xFF388E3C);
  static const balanceCredit = Color(0xFF1565C0);
  static const balanceOutstanding = Color(0xFFD32F2F);

  // ── Status chips ─────────────────────────────────────────
  static const statusOccupied = Color(0xFF388E3C);
  static const statusVacant = Color(0xFF9E9E9E);
  static const statusMaintenance = Color(0xFFF59E0B);
}
