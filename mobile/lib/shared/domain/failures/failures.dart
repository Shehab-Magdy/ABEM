/// Failure hierarchy — used as Left values in Either<Failure, T>.
abstract class Failure {
  final String message;
  const Failure(this.message);

  @override
  String toString() => '$runtimeType: $message';
}

class ServerFailure extends Failure {
  final int statusCode;
  final Map<String, dynamic>? fieldErrors;

  const ServerFailure(
    super.message, {
    required this.statusCode,
    this.fieldErrors,
  });
}

class NetworkFailure extends Failure {
  const NetworkFailure([super.message = 'No internet connection']);
}

class CacheFailure extends Failure {
  const CacheFailure([super.message = 'Cache read/write failed']);
}

class AuthFailure extends Failure {
  const AuthFailure([super.message = 'Authentication failed']);
}
