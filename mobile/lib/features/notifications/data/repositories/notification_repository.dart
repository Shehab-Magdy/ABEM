import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/notification_remote_data_source.dart';

/// Repository that wraps [NotificationRemoteDataSource] in Either<Failure, T>.
class NotificationRepository {
  final NotificationRemoteDataSource _remote;
  NotificationRepository(this._remote);

  Future<Either<Failure, List<Map<String, dynamic>>>> getNotifications({
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final data = await _remote.getNotifications(
        page: page,
        pageSize: pageSize,
      );
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } catch (e) {
      return Left(ServerFailure(e.toString(), statusCode: 0));
    }
  }

  Future<Either<Failure, void>> markRead(String id) async {
    try {
      await _remote.markRead(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, void>> markAllRead() async {
    try {
      await _remote.markAllRead();
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> broadcast(
    String buildingId,
    String subject,
    String message,
  ) async {
    try {
      final data = await _remote.broadcast(buildingId, subject, message);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> sendMessage(
    String recipientType,
    List<String> recipients,
    String subject,
    String body,
  ) async {
    try {
      final data =
          await _remote.sendMessage(recipientType, recipients, subject, body);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }
}
