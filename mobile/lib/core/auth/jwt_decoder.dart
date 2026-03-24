import 'dart:convert';

/// Decode JWT payload without verifying the signature.
///
/// Used client-side to extract user_id, role, and exp from the
/// access token. Signature verification is the backend's concern.
class JwtDecoder {
  JwtDecoder._();

  /// Decode the JWT payload section (index 1) from a dot-separated token.
  static Map<String, dynamic> decode(String token) {
    final parts = token.split('.');
    if (parts.length != 3) {
      throw const FormatException('Invalid JWT token format');
    }
    final payload = parts[1];
    final normalized = base64Url.normalize(payload);
    final decoded = utf8.decode(base64Url.decode(normalized));
    return jsonDecode(decoded) as Map<String, dynamic>;
  }

  /// Extract the user role from a JWT access token.
  static String? getRole(String token) {
    try {
      final payload = decode(token);
      return payload['role'] as String?;
    } catch (_) {
      return null;
    }
  }

  /// Extract the user ID from a JWT access token.
  static String? getUserId(String token) {
    try {
      final payload = decode(token);
      return payload['user_id']?.toString();
    } catch (_) {
      return null;
    }
  }

  /// Check if the token expires within [withinSeconds] from now.
  static bool isExpiringSoon(String token, {int withinSeconds = 60}) {
    try {
      final payload = decode(token);
      final exp = payload['exp'] as int?;
      if (exp == null) return true;
      final expiresAt = DateTime.fromMillisecondsSinceEpoch(exp * 1000);
      final buffer = DateTime.now().add(Duration(seconds: withinSeconds));
      return expiresAt.isBefore(buffer);
    } catch (_) {
      return true;
    }
  }

  /// Check if the token is already expired.
  static bool isExpired(String token) => isExpiringSoon(token, withinSeconds: 0);
}
