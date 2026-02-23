import '../../../core/api/api_client.dart';

class AccountLockedException implements Exception {
  final String message;
  const AccountLockedException(this.message);
}

class AuthRepository {
  final ApiClient apiClient;

  AuthRepository({required this.apiClient});

  Future<Map<String, dynamic>> login(String email, String password) async {
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
  }

  Future<void> logout() async {
    try {
      final refresh = await apiClient.getRefreshToken();
      if (refresh != null) {
        await apiClient.dio.post('/auth/logout/', data: {'refresh': refresh});
      }
    } catch (_) {
      // Best-effort; always clear local storage
    } finally {
      await apiClient.clearTokens();
    }
  }

  Future<String?> getStoredAccessToken() => apiClient.getAccessToken();

  Future<Map<String, dynamic>?> getStoredUser() async {
    // TODO Sprint 1: persist user profile using shared_preferences
    return null;
  }

  Future<void> _storeUser(Map<String, dynamic> user) async {
    // TODO Sprint 1: persist to shared_preferences
  }
}
