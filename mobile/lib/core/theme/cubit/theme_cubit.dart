import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:hive/hive.dart';

/// Cubit that manages the app theme mode (light / dark / system).
///
/// Persisted to Hive so the user's choice survives cold restarts.
/// Loaded from Hive **before** [runApp] to prevent a theme flash.
class ThemeCubit extends Cubit<ThemeMode> {
  static const String _boxName = 'settings';
  static const String _key = 'themeMode';

  final Box _box;

  ThemeCubit(this._box) : super(_readInitial(_box));

  static ThemeMode _readInitial(Box box) {
    final stored = box.get(_key, defaultValue: 'system') as String;
    switch (stored) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }

  void setTheme(ThemeMode mode) {
    final label = switch (mode) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'system',
    };
    _box.put(_key, label);
    emit(mode);
  }

  /// Convenience: open the Hive box and create the cubit.
  static Future<ThemeCubit> create() async {
    final box = await Hive.openBox(_boxName);
    return ThemeCubit(box);
  }
}
