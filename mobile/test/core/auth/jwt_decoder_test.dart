import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:abem_mobile/core/auth/jwt_decoder.dart';

/// Build a fake JWT with the given payload.
String _buildToken(Map<String, dynamic> payload) {
  final header = base64Url.encode(utf8.encode('{"alg":"HS256","typ":"JWT"}'));
  final body = base64Url.encode(utf8.encode(jsonEncode(payload)));
  return '$header.$body.fake_signature';
}

void main() {
  group('JwtDecoder', () {
    test('decode extracts payload', () {
      final token = _buildToken({'user_id': '123', 'role': 'admin', 'exp': 9999999999});
      final payload = JwtDecoder.decode(token);
      expect(payload['user_id'], '123');
      expect(payload['role'], 'admin');
    });

    test('getRole returns role', () {
      final token = _buildToken({'role': 'owner'});
      expect(JwtDecoder.getRole(token), 'owner');
    });

    test('getRole returns null for missing role', () {
      final token = _buildToken({'user_id': '123'});
      expect(JwtDecoder.getRole(token), null);
    });

    test('getUserId returns user_id', () {
      final token = _buildToken({'user_id': 'abc-123'});
      expect(JwtDecoder.getUserId(token), 'abc-123');
    });

    test('isExpired returns true for past exp', () {
      final pastExp = DateTime.now().subtract(const Duration(hours: 1)).millisecondsSinceEpoch ~/ 1000;
      final token = _buildToken({'exp': pastExp});
      expect(JwtDecoder.isExpired(token), true);
    });

    test('isExpired returns false for future exp', () {
      final futureExp = DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch ~/ 1000;
      final token = _buildToken({'exp': futureExp});
      expect(JwtDecoder.isExpired(token), false);
    });

    test('isExpiringSoon returns true when within buffer', () {
      final soonExp = DateTime.now().add(const Duration(seconds: 30)).millisecondsSinceEpoch ~/ 1000;
      final token = _buildToken({'exp': soonExp});
      expect(JwtDecoder.isExpiringSoon(token, withinSeconds: 60), true);
    });

    test('isExpiringSoon returns false when well in future', () {
      final farExp = DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch ~/ 1000;
      final token = _buildToken({'exp': farExp});
      expect(JwtDecoder.isExpiringSoon(token, withinSeconds: 60), false);
    });

    test('decode throws on invalid token', () {
      expect(() => JwtDecoder.decode('not.a.valid'), throwsFormatException);
    });

    test('decode throws on too few parts', () {
      expect(() => JwtDecoder.decode('onlyone'), throwsFormatException);
    });
  });
}
