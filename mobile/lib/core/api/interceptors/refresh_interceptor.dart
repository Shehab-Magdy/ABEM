import 'package:dio/dio.dart';

import '../../auth/token_storage.dart';
import '../api_endpoints.dart';

/// Silently refreshes the access token on 401 responses.
///
/// Flow:
///   1. Original request gets 401
///   2. Read refresh token from secure storage
///   3. POST /auth/refresh/ to get a new access token
///   4. Save the new access token
///   5. Retry the original request with the new token
///   6. If refresh itself fails → reject (AuthBloc will handle logout)
class RefreshInterceptor extends Interceptor {
  final Dio _dio;
  final TokenStorage _tokenStorage;
  bool _isRefreshing = false;

  RefreshInterceptor(this._dio, this._tokenStorage);

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode != 401 || _isRefreshing) {
      return handler.next(err);
    }

    // Don't try to refresh if the failing request IS the refresh endpoint
    if (err.requestOptions.path.contains('auth/refresh')) {
      return handler.reject(err);
    }

    _isRefreshing = true;
    try {
      final refreshToken = await _tokenStorage.refreshToken;
      if (refreshToken == null || refreshToken.isEmpty) {
        return handler.reject(err);
      }

      final response = await _dio.post(
        ApiEndpoints.refresh,
        data: {'refresh': refreshToken},
        options: Options(headers: {'Authorization': null}),
      );

      final newAccess = response.data['access'] as String;
      await _tokenStorage.saveTokens(access: newAccess, refresh: refreshToken);

      // Retry the original request with the new token
      final retryOptions = err.requestOptions;
      retryOptions.headers['Authorization'] = 'Bearer $newAccess';
      final retried = await _dio.fetch(retryOptions);
      handler.resolve(retried);
    } on DioException {
      // Refresh failed — clear tokens, let AuthBloc handle logout
      await _tokenStorage.clearAll();
      handler.reject(err);
    } catch (_) {
      await _tokenStorage.clearAll();
      handler.reject(err);
    } finally {
      _isRefreshing = false;
    }
  }
}
