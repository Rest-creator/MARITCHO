import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_client.dart';

void main() {
  group('ClientCircuitBreaker', () {
    test('given fewer failures than the threshold, when checked, then stays closed', () {
      // Arrange
      final breaker = ClientCircuitBreaker(threshold: 3, resetTimeout: const Duration(seconds: 30));

      // Act
      breaker.recordFailure();
      breaker.recordFailure();

      // Assert
      expect(breaker.isOpen, isFalse);
    });

    test('given failures reach the threshold, when checked, then opens', () {
      // Arrange
      final breaker = ClientCircuitBreaker(threshold: 3, resetTimeout: const Duration(seconds: 30));

      // Act
      breaker.recordFailure();
      breaker.recordFailure();
      breaker.recordFailure();

      // Assert
      expect(breaker.isOpen, isTrue);
    });

    test('given an open breaker, when a success is recorded, then closes and resets the failure count', () {
      // Arrange
      final breaker = ClientCircuitBreaker(threshold: 2, resetTimeout: const Duration(seconds: 30));
      breaker.recordFailure();
      breaker.recordFailure();
      expect(breaker.isOpen, isTrue);

      // Act
      breaker.recordSuccess();

      // Assert
      expect(breaker.isOpen, isFalse);
    });

    test('given an open breaker past its reset timeout, when checked, then closes itself', () async {
      // Arrange
      final breaker = ClientCircuitBreaker(threshold: 1, resetTimeout: const Duration(milliseconds: 10));

      // Act
      breaker.recordFailure();
      expect(breaker.isOpen, isTrue);
      await Future<void>.delayed(const Duration(milliseconds: 20));

      // Assert
      expect(breaker.isOpen, isFalse);
    });
  });
}
