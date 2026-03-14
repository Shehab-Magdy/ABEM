import 'package:flutter/material.dart';

class AppColors {
  static const primary = Color(0xFF2563EB);
  static const primaryDark = Color(0xFF1D4ED8);
  static const primaryLight = Color(0xFFDBEAFE);
  static const secondary = Color(0xFF10B981);
  static const secondaryDark = Color(0xFF059669);
  static const secondaryLight = Color(0xFFD1FAE5);
  static const accent = Color(0xFFF59E0B);
  static const accentDark = Color(0xFFD97706);
  static const accentLight = Color(0xFFFEF3C7);
  static const neutralDark = Color(0xFF1F2937);
  static const neutralMid = Color(0xFF6B7280);
  static const background = Color(0xFFF9FAFB);
  static const danger = Color(0xFFEF4444);
  static const purple = Color(0xFF7C3AED);
  static const orange = Color(0xFFEA580C);
}

class AppTheme {
  static ThemeData get light => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primary,
          secondary: AppColors.secondary,
          error: AppColors.danger,
          surface: Colors.white,
        ),
        scaffoldBackgroundColor: AppColors.background,
        fontFamily: 'Inter',
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          elevation: 1,
        ),
        cardTheme: const CardThemeData(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(12)),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
}
