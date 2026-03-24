import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/audit_remote_data_source.dart';

/// Repository that wraps [AuditRemoteDataSource] in Either<Failure, T>.
class AuditRepository {
  final AuditRemoteDataSource _remote;
  AuditRepository(this._remote);

  Future<Either<Failure, Map<String, dynamic>>> getAuditLogs({
    String? entityType,
    String? action,
    String? dateFrom,
    String? dateTo,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final data = await _remote.getAuditLogs(
        entityType: entityType,
        action: action,
        dateFrom: dateFrom,
        dateTo: dateTo,
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
}
