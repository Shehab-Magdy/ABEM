import 'package:flutter_test/flutter_test.dart';
import 'package:abem_mobile/core/utils/round_up.dart';

void main() {
  group('roundUpToNearest5', () {
    test('rounds 22.01 up to 25', () {
      expect(roundUpToNearest5(22.01), 25.0);
    });

    test('rounds 25.00 stays at 25', () {
      expect(roundUpToNearest5(25.0), 25.0);
    });

    test('rounds 0.01 up to 5', () {
      expect(roundUpToNearest5(0.01), 5.0);
    });

    test('rounds 101 / 4 = 25.25 up to 30', () {
      expect(roundUpToNearest5(101 / 4), 30.0);
    });

    test('rounds 5 stays at 5', () {
      expect(roundUpToNearest5(5.0), 5.0);
    });

    test('returns 0 for 0', () {
      expect(roundUpToNearest5(0), 0);
    });

    test('returns 0 for negative', () {
      expect(roundUpToNearest5(-10), 0);
    });

    test('rounds 1.0 to 5', () {
      expect(roundUpToNearest5(1.0), 5.0);
    });

    test('rounds 10.0 stays at 10', () {
      expect(roundUpToNearest5(10.0), 10.0);
    });

    test('rounds 33.33 up to 35', () {
      expect(roundUpToNearest5(33.33), 35.0);
    });
  });
}
