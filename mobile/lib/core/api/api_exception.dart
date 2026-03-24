/// Exception types thrown by data sources.
class ServerException implements Exception {
  final String message;
  final int statusCode;
  final Map<String, dynamic>? fieldErrors;

  const ServerException(this.message, {required this.statusCode, this.fieldErrors});

  @override
  String toString() => 'ServerException($statusCode): $message';
}

class CacheException implements Exception {
  final String message;
  const CacheException(this.message);

  @override
  String toString() => 'CacheException: $message';
}

class NetworkException implements Exception {
  final String message;
  const NetworkException([this.message = 'No internet connection']);

  @override
  String toString() => 'NetworkException: $message';
}
