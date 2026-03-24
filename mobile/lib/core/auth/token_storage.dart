import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Secure wrapper around flutter_secure_storage for JWT tokens.
///
/// Tokens are stored in iOS Keychain / Android Keystore — never
/// in SharedPreferences or plain files.
class TokenStorage {
  static const String _accessKey = 'access_token';
  static const String _refreshKey = 'refresh_token';

  final FlutterSecureStorage _storage;

  const TokenStorage(this._storage);

  Future<String?> get accessToken => _storage.read(key: _accessKey);
  Future<String?> get refreshToken => _storage.read(key: _refreshKey);

  Future<String?> readSecure(String key) => _storage.read(key: key);

  Future<void> writeSecure(String key, String value) =>
      _storage.write(key: key, value: value);

  Future<void> deleteSecure(String key) => _storage.delete(key: key);

  Future<void> saveTokens({
    required String access,
    required String refresh,
  }) async {
    await Future.wait([
      _storage.write(key: _accessKey, value: access),
      _storage.write(key: _refreshKey, value: refresh),
    ]);
  }

  Future<void> clearAll() async {
    await Future.wait([
      _storage.delete(key: _accessKey),
      _storage.delete(key: _refreshKey),
    ]);
  }

  Future<bool> get hasTokens async {
    final access = await accessToken;
    return access != null && access.isNotEmpty;
  }
}
