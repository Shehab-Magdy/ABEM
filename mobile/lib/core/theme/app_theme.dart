import 'package:flutter/material.dart';

class AppColors {
  // Light mode
  static const primaryLight = Color(0xFF1E3A8A); // Deep Cobalt
  static const secondaryLight = Color(0xFF10B981); // Mint Green
  static const backgroundLight = Color(0xFFF3F4F6); // Soft Light Gray
  static const surfaceLight = Color(0xFFFFFFFF); // Pure White
  static const textLight = Color(0xFF1E293B); // Slate Gray

  // Dark mode
  static const primaryDark = Color(0xFF3B82F6); // Electric Blue
  static const secondaryDark = Color(0xFF10B981);
  static const backgroundDark = Color(0xFF0F172A); // Deep Charcoal
  static const surfaceDark = Color(0xFF1E293B); // Slate Navy
  static const textDark = Color(0xFFF8FAFC); // Off-White

  static const danger = Color(0xFFEF4444); // Alert Crimson
}

class AppTheme {
  static ThemeData get light => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primaryLight,
          secondary: AppColors.secondaryLight,
          error: AppColors.danger,
          surface: AppColors.surfaceLight,
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: AppColors.backgroundLight,
        fontFamily: 'Inter',
        appBarTheme: AppBarTheme(
          centerTitle: false,
          elevation: 1,
          backgroundColor: AppColors.surfaceLight.withOpacity(0.8),
          shadowColor: Colors.transparent,
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
        bottomNavigationBarTheme: BottomNavigationBarThemeData(
          backgroundColor: AppColors.surfaceLight.withOpacity(0.8),
          elevation: 0,
        ),
      );

  static ThemeData get dark => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primaryDark,
          secondary: AppColors.secondaryDark,
          error: AppColors.danger,
          surface: AppColors.surfaceDark,
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: AppColors.backgroundDark,
        fontFamily: 'Inter',
        appBarTheme: AppBarTheme(
          centerTitle: false,
          elevation: 1,
          backgroundColor: AppColors.surfaceDark.withOpacity(0.8),
          shadowColor: Colors.transparent,
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
        bottomNavigationBarTheme: BottomNavigationBarThemeData(
          backgroundColor: AppColors.surfaceDark.withOpacity(0.8),
          elevation: 0,
        ),
      );
}
