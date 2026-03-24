import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/api/api_endpoints.dart';
import '../../../core/auth/token_storage.dart';

class AccountLockedException implements Exception {
  final String message;
  final String? lockedUntil;
  const AccountLockedException(this.message, {this.lockedUntil});
}

class AuthRepository {
  final Dio _dio;
  final TokenStorage _tokenStorage;
  static const String _userKey = 'abem_user';

  AuthRepository({required Dio dio, required TokenStorage tokenStorage})
      : _dio = dio,
        _tokenStorage = tokenStorage;

  /// Login and persist tokens + user profile locally.
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.login,
        data: {'email': email, 'password': password},
      );
      final data = response.data as Map<String, dynamic>;
      await _tokenStorage.saveTokens(
        access: data['access'] as String,
        refresh: data['refresh'] as String,
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

  /// Self-register (public) — caller chooses role (admin | owner).
  /// Persists tokens + user profile locally, same as login.
  Future<Map<String, dynamic>> selfRegister(Map<String, dynamic> payload) async {
    final response = await _dio.post(ApiEndpoints.selfRegister, data: payload);
    final data = response.data as Map<String, dynamic>;
    await _tokenStorage.saveTokens(
      access: data['access'] as String,
      refresh: data['refresh'] as String,
    );
    await _storeUser(data['user'] as Map<String, dynamic>);
    return data;
  }

  /// Logout: blacklist refresh token on server, clear local storage.
  Future<void> logout() async {
    try {
      final refresh = await _tokenStorage.refreshToken;
      if (refresh != null) {
        await _dio.post(ApiEndpoints.logout, data: {'refresh': refresh});
      }
    } catch (_) {
      // Best-effort – always clear local data even if server call fails.
    } finally {
      await _tokenStorage.clearAll();
      await _clearUser();
    }
  }

  Future<String?> getStoredAccessToken() => _tokenStorage.accessToken;

  /// Read persisted user profile from shared_preferences.
  Future<Map<String, dynamic>?> getStoredUser() async {
    final raw = await _tokenStorage.readSecure(_userKey);
    if (raw == null) return null;
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  Future<void> _storeUser(Map<String, dynamic> user) async {
    await _tokenStorage.writeSecure(_userKey, jsonEncode(user));
  }

  Future<void> _clearUser() async {
    await _tokenStorage.deleteSecure(_userKey);
  }

  /// Upload a new profile picture and persist the updated user locally.
  Future<Map<String, dynamic>> uploadProfilePicture(XFile imageFile) async {
    final formData = FormData.fromMap({
      'profile_picture': await MultipartFile.fromFile(
        imageFile.path,
        filename: imageFile.name,
      ),
    });
    final response = await _dio.patch(
      ApiEndpoints.profile,
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
    );
    final data = response.data as Map<String, dynamic>;
    await _storeUser(data);
    return data;
  }

  /// Update profile fields (first_name, last_name, phone) and persist locally.
  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> fields) async {
    final response = await _dio.patch(ApiEndpoints.profile, data: fields);
    final data = response.data as Map<String, dynamic>;
    await _storeUser(data);
    return data;
  }
}
