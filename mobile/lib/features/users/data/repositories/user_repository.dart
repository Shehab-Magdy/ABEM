import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/user_remote_data_source.dart';

/// Repository that wraps [UserRemoteDataSource] in Either<Failure, T>.
class UserRepository {
  final UserRemoteDataSource _remote;
  UserRepository(this._remote);

  Future<Either<Failure, List<Map<String, dynamic>>>> getUsers({
    String? buildingId,
    String? search,
    String? role,
  }) async {
    try {
      final data = await _remote.getUsers(
        buildingId: buildingId,
        search: search,
        role: role,
      );
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } catch (e) {
      return Left(ServerFailure(e.toString(), statusCode: 0));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> getUser(String id) async {
    try {
      final data = await _remote.getUser(id);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> createUser(
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.createUser(payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> updateUser(
    String id,
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.updateUser(id, payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, void>> activateUser(String id) async {
    try {
      await _remote.activateUser(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, void>> deactivateUser(String id) async {
    try {
      await _remote.deactivateUser(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, void>> resetPassword(
    String id,
    String newPassword,
  ) async {
    try {
      await _remote.resetPassword(id, newPassword);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, void>> setMessagingBlock(
    String id, {
    required bool blocked,
    required bool individualBlocked,
  }) async {
    try {
      await _remote.setMessagingBlock(
        id,
        blocked: blocked,
        individualBlocked: individualBlocked,
      );
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }
}
