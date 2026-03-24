import 'package:dartz/dartz.dart';

import '../../../../core/api/api_exception.dart';
import '../../../../shared/domain/failures/failures.dart';
import '../datasources/apartment_remote_data_source.dart';

/// Repository wrapping apartment operations in Either.
class ApartmentRepository {
  final ApartmentRemoteDataSource _remote;
  ApartmentRepository(this._remote);

  Future<Either<Failure, Map<String, dynamic>>> getApartment(String id) async {
    try {
      final data = await _remote.getApartment(id);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> getBalance(String id) async {
    try {
      final data = await _remote.getApartmentBalance(id);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> updateApartment(
    String id,
    Map<String, dynamic> payload,
  ) async {
    try {
      final data = await _remote.updateApartment(id, payload);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> generateInvite(
    String apartmentId,
  ) async {
    try {
      final data = await _remote.generateInvite(apartmentId);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> validateInviteCode(
    String code,
  ) async {
    try {
      final data = await _remote.validateInviteCode(code);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }

  Future<Either<Failure, Map<String, dynamic>>> useInviteCode(
    String code,
  ) async {
    try {
      final data = await _remote.useInviteCode(code);
      return Right(data);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message, statusCode: e.statusCode));
    }
  }
}
