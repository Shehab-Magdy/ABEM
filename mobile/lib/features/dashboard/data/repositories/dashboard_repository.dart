import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/dashboard_remote_data_source.dart';

/// Repository that wraps [DashboardRemoteDataSource] in Either<Failure, T>.
class DashboardRepository {
  final DashboardRemoteDataSource _remote;
  DashboardRepository(this._remote);

  Future<Either<Failure, Map<String, dynamic>>> getAdminDashboard({
    String? buildingId,
    String? dateFrom,
    String? dateTo,
  }) async {
    try {
      final data = await _remote.getAdminDashboard(
        buildingId: buildingId,
        dateFrom: dateFrom,
        dateTo: dateTo,
      );
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } catch (e) {
      return Left(ServerFailure(e.toString(), statusCode: 0));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> getOwnerDashboard({
    String? dateFrom,
    String? dateTo,
  }) async {
    try {
      final data = await _remote.getOwnerDashboard(
        dateFrom: dateFrom,
        dateTo: dateTo,
      );
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } catch (e) {
      return Left(ServerFailure(e.toString(), statusCode: 0));
    }
  }
}
