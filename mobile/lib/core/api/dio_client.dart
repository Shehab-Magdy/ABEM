import 'package:dio/dio.dart';

import '../auth/token_storage.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/logging_interceptor.dart';
import 'interceptors/refresh_interceptor.dart';

/// Factory that creates and configures the singleton Dio instance.
///
/// All interceptors are wired here:
///   1. [AuthInterceptor] — attaches Bearer token
///   2. [RefreshInterceptor] — silent 401 → token refresh → retry
///   3. [LoggingInterceptor] — dev-only request/response logging
class DioClient {
  DioClient._();

  static const String _defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  /// Create a fully-configured Dio instance.
  static Dio create(TokenStorage tokenStorage, {String? baseUrl}) {
    final dio = Dio(
      BaseOptions(
        baseUrl: baseUrl ?? _defaultBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    dio.interceptors.addAll([
      AuthInterceptor(tokenStorage),
      RefreshInterceptor(dio, tokenStorage),
      LoggingInterceptor(),
    ]);

    return dio;
  }
}
