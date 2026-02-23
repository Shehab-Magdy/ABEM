import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/api/api_client.dart';

class AccountLockedException implements Exception {
  final String message;
  final String? lockedUntil;
  const AccountLockedException(this.message, {this.lockedUntil});
}

class AuthRepository {
  final ApiClient apiClient;
  static const String _userKey = 'abem_user';

  AuthRepository({required this.apiClient});

  /// Login and persist tokens + user profile locally.
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await apiClient.dio.post(
        '/auth/login/',
        data: {'email': email, 'password': password},
      );
      final data = response.data as Map<String, dynamic>;
      await apiClient.saveTokens(
        data['access'] as String,
        data['refresh'] as String,
      );
      await _storeUser(data['user'] as Map<String, dynamic>);
      return data;
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      final body = e.response?.data as Map<String, dynamic>?;
      final detail = body?['detail'] as String? ?? 'An error occurred.';

      if (status == 423) {
        throw AccountLockedException(
          detail,
          lockedUntil: body?['locked_until'] as String?,
        );
      }
      rethrow;
    }
  }

  /// Logout: blacklist refresh token on server, clear local storage.
  Future<void> logout() async {
    try {
      final refresh = await apiClient.getRefreshToken();
      if (refresh != null) {
        await apiClient.dio.post('/auth/logout/', data: {'refresh': refresh});
      }
    } catch (_) {
      // Best-effort – always clear local data even if server call fails.
    } finally {
      await apiClient.clearTokens();
      await _clearUser();
    }
  }

  Future<String?> getStoredAccessToken() => apiClient.getAccessToken();

  /// Read persisted user profile from shared_preferences.
  Future<Map<String, dynamic>?> getStoredUser() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_userKey);
    if (raw == null) return null;
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  Future<void> _storeUser(Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userKey, jsonEncode(user));
  }

  Future<void> _clearUser() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userKey);
  }
}
