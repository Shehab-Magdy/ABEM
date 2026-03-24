import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for apartment/unit operations.
class ApartmentRemoteDataSource {
  final Dio _dio;
  ApartmentRemoteDataSource(this._dio);

  Future<Map<String, dynamic>> getApartment(String id) async {
    try {
      final response = await _dio.get(ApiEndpoints.apartmentDetail(id));
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Apartment not found',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> getApartmentBalance(String id) async {
    try {
      final response = await _dio.get(ApiEndpoints.apartmentBalance(id));
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load balance',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> updateApartment(
    String id,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.patch(
        ApiEndpoints.apartmentDetail(id),
        data: data,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to update',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> generateInvite(String apartmentId) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.apartmentInvite(apartmentId),
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to generate invite',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> validateInviteCode(String code) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.inviteValidate,
        queryParameters: {'code': code},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Invalid or expired code',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> useInviteCode(String code) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.inviteUse,
        data: {'code': code},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to use invite',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> claimApartment(String id) async {
    try {
      final response = await _dio.post(ApiEndpoints.apartmentClaim(id));
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to claim unit',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }
}
