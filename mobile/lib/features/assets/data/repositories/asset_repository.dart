import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/asset_remote_data_source.dart';

/// Repository that wraps [AssetRemoteDataSource] in Either<Failure, T>.
class AssetRepository {
  final AssetRemoteDataSource _remote;
  AssetRepository(this._remote);

  Future<Either<Failure, List<Map<String, dynamic>>>> getAssets({
    String? buildingId,
  }) async {
    try {
      final data = await _remote.getAssets(buildingId: buildingId);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } catch (e) {
      return Left(ServerFailure(e.toString(), statusCode: 0));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> createAsset(
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.createAsset(payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> updateAsset(
    String id,
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.updateAsset(id, payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> sellAsset(
    String id,
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.sellAsset(id, payload);
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
