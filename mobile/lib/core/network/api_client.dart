import 'dart:async';
import 'dart:math';

import 'package:dio/dio.dart';

import '../storage/token_storage.dart';
import 'api_config.dart';

/// Builds the shared Dio instance every online repository uses: base URL,
/// an interceptor that attaches the stored bearer token (if any) to every
/// outgoing request, a circuit breaker that fast-fails while the backend
/// looks unreachable, and a retry interceptor with exponential backoff and
/// jitter for transient failures — all three matter here specifically
/// because this app targets inexpensive devices on unreliable, low-bandwidth
/// connections (see AGENTS.md's offline-first constraints).
Dio buildApiDio(TokenStorage tokenStorage) {
  final dio = Dio(BaseOptions(baseUrl: ApiConfig.baseUrl));

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await tokenStorage.getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ),
  );

  final circuitBreaker = ClientCircuitBreaker(
    threshold: 5,
    resetTimeout: const Duration(seconds: 30),
  );
  dio.interceptors.add(CircuitBreakerInterceptor(circuitBreaker));
  dio.interceptors.add(NetworkRetryInterceptor(dio));

  return dio;
}

/// Rejects requests immediately while the backend looks unreachable,
/// instead of letting every screen's callers wait out their own timeout —
/// saves battery/data on a device that keeps retrying a dead connection.
class CircuitBreakerInterceptor extends Interceptor {
  final ClientCircuitBreaker _breaker;

  CircuitBreakerInterceptor(this._breaker);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (_breaker.isOpen) {
      handler.reject(
        DioException(
          requestOptions: options,
          type: DioExceptionType.cancel,
          error: 'Circuit open: too many recent failures, pausing requests.',
        ),
        true,
      );
      return;
    }
    handler.next(options);
  }

  @override
  void onResponse(Response<dynamic> response, ResponseInterceptorHandler handler) {
    _breaker.recordSuccess();
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    // Don't double-count a rejection this same interceptor just issued.
    if (err.type != DioExceptionType.cancel) {
      _breaker.recordFailure();
    }
    handler.next(err);
  }
}

class ClientCircuitBreaker {
  final int threshold;
  final Duration resetTimeout;

  int _failures = 0;
  DateTime? _cooldownExpiration;

  ClientCircuitBreaker({required this.threshold, required this.resetTimeout});

  bool get isOpen {
    if (_cooldownExpiration == null) return false;
    if (DateTime.now().isAfter(_cooldownExpiration!)) {
      _failures = 0;
      _cooldownExpiration = null;
      return false;
    }
    return true;
  }

  void recordSuccess() {
    _failures = 0;
    _cooldownExpiration = null;
  }

  void recordFailure() {
    _failures++;
    if (_failures >= threshold) {
      _cooldownExpiration = DateTime.now().add(resetTimeout);
    }
  }
}

/// Exponential backoff with randomized jitter for transient failures
/// (timeouts, connection errors, 5xx) — never retries a 4xx, since that's
/// a client-error response, not a flaky-network one.
class NetworkRetryInterceptor extends Interceptor {
  final Dio _dio;
  final int _maxAttempts;
  final int _baseDelayMs;
  final Random _random = Random();

  NetworkRetryInterceptor(this._dio, {this._maxAttempts = 3, this._baseDelayMs = 1000});

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (!_shouldRetry(err)) {
      return handler.next(err);
    }

    final requestOptions = err.requestOptions;
    int attempt = requestOptions.extra['retry_attempt'] as int? ?? 0;

    if (attempt >= _maxAttempts) {
      return handler.next(err);
    }

    attempt++;
    requestOptions.extra['retry_attempt'] = attempt;

    final jitter = _random.nextInt(500);
    final delayMs = (_baseDelayMs * pow(2, attempt)).toInt() + jitter;
    await Future<void>.delayed(Duration(milliseconds: delayMs));

    try {
      final response = await _dio.fetch<dynamic>(requestOptions);
      return handler.resolve(response);
    } on DioException catch (retryErr) {
      return handler.next(retryErr);
    }
  }

  bool _shouldRetry(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.connectionError ||
        (err.response?.statusCode != null && err.response!.statusCode! >= 500);
  }
}
