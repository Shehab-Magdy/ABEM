import 'dart:typed_data';

import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/payment_remote_data_source.dart';

/// Repository that wraps [PaymentRemoteDataSource] in Either<Failure, T>.
class PaymentRepository {
  final PaymentRemoteDataSource _remote;
  PaymentRepository(this._remote);

  Future<Either<Failure, List<Map<String, dynamic>>>> getPayments({
    String? apartmentId,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final data = await _remote.getPayments(
        apartmentId: apartmentId,
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

  Future<Either<Failure, Map<String, dynamic>>> recordPayment(
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.recordPayment(payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(
        e.message,
        statusCode: e.statusCode,
        fieldErrors: e.fieldErrors,
      ));
    }
  }

  Future<Either<Failure, Uint8List>> getReceipt(String paymentId) async {
    try {
      final data = await _remote.getReceipt(paymentId);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }
}
