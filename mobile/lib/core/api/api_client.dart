import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

/// Centralized Dio HTTP client with JWT interceptor.
class ApiClient {
  static const String _baseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'http://127.0.0.1:8000/api/v1');

  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.addAll([
      _AuthInterceptor(_storage, _dio),
      PrettyDioLogger(requestHeader: false, responseBody: false),
    ]);
  }

  Dio get dio => _dio;

  Future<void> saveTokens(String access, String refresh) async {
    await Future.wait([
      _storage.write(key: _accessTokenKey, value: access),
      _storage.write(key: _refreshTokenKey, value: refresh),
    ]);
  }

  Future<void> clearTokens() async {
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _refreshTokenKey),
    ]);
  }

  Future<String?> getAccessToken() => _storage.read(key: _accessTokenKey);
  Future<String?> getRefreshToken() => _storage.read(key: _refreshTokenKey);
}

class _AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;
  final Dio _dio;
  bool _isRefreshing = false;

  _AuthInterceptor(this._storage, this._dio);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401 && !_isRefreshing) {
      _isRefreshing = true;
      try {
        final refreshToken = await _storage.read(key: 'refresh_token');
        if (refreshToken == null) {
          handler.reject(err);
          return;
        }
        final response = await _dio.post(
          '/auth/refresh/',
          data: {'refresh': refreshToken},
          options: Options(headers: {'Authorization': null}),
        );
        final newAccess = response.data['access'] as String;
        await _storage.write(key: 'access_token', value: newAccess);
        err.requestOptions.headers['Authorization'] = 'Bearer $newAccess';
        final retried = await _dio.fetch(err.requestOptions);
        handler.resolve(retried);
      } catch (_) {
        await _storage.deleteAll();
        handler.reject(err);
      } finally {
        _isRefreshing = false;
      }
    } else {
      handler.next(err);
    }
  }
}
