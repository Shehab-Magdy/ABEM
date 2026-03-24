import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/expense_remote_data_source.dart';

/// Repository that wraps [ExpenseRemoteDataSource] in Either<Failure, T>.
class ExpenseRepository {
  final ExpenseRemoteDataSource _remote;
  ExpenseRepository(this._remote);

  Future<Either<Failure, List<Map<String, dynamic>>>> getExpenses({
    String? buildingId,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final data = await _remote.getExpenses(
        buildingId: buildingId,
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

  Future<Either<Failure, Map<String, dynamic>>> getExpense(String id) async {
    try {
      final data = await _remote.getExpense(id);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> createExpense(
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.createExpense(payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> updateExpense(
    String id,
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.updateExpense(id, payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, void>> deleteExpense(String id) async {
    try {
      await _remote.deleteExpense(id);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> uploadBill(
    String expenseId,
    String filePath,
    String fileName,
  ) async {
    try {
      final data = await _remote.uploadBill(expenseId, filePath, fileName);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, List<Map<String, dynamic>>>> getCategories({
    String? buildingId,
  }) async {
    try {
      final data = await _remote.getCategories(buildingId: buildingId);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    } catch (e) {
      return Left(ServerFailure(e.toString(), statusCode: 0));
    }
  }
}
