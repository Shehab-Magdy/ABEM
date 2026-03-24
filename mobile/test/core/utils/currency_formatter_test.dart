import 'package:flutter_test/flutter_test.dart';
import 'package:abem_mobile/core/utils/currency_formatter.dart';

void main() {
  group('formatCurrency', () {
    test('formats positive amount in English', () {
      final result = formatCurrency(1234.56);
      expect(result, contains('1'));
      expect(result, contains('234'));
      expect(result, contains('EGP'));
    });

    test('formats zero', () {
      final result = formatCurrency(0);
      expect(result, contains('0.00'));
      expect(result, contains('EGP'));
    });

    test('formats with 2 decimal places', () {
      final result = formatCurrency(100.5);
      expect(result, contains('.50'));
    });
  });
}
