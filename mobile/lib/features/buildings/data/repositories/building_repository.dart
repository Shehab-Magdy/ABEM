import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/building_remote_data_source.dart';

/// Repository that wraps [BuildingRemoteDataSource] in Either<Failure, T>.
class BuildingRepository {
  final BuildingRemoteDataSource _remote;
  BuildingRepository(this._remote);

  Future<Either<Failure, List<Map<String, dynamic>>>> getBuildings({
    String? search,
    int page = 1,
  }) async {
    try {
      final data = await _remote.getBuildings(search: search, page: page);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } catch (e) {
      return Left(ServerFailure(e.toString(), statusCode: 0));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> getBuilding(String id) async {
    try {
      final data = await _remote.getBuilding(id);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> createBuilding(
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.createBuilding(payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> updateBuilding(
    String id,
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.updateBuilding(id, payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, void>> deleteBuilding(String id) async {
    try {
      await _remote.deleteBuilding(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, void>> activateBuilding(String id) async {
    try {
      await _remote.activateBuilding(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, void>> deactivateBuilding(String id) async {
    try {
      await _remote.deactivateBuilding(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, List<Map<String, dynamic>>>> getBuildingUnits(
    String buildingId,
  ) async {
    try {
      final data = await _remote.getBuildingUnits(buildingId);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }
}
