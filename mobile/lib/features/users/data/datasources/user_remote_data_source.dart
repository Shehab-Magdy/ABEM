import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for user management operations via REST API.
class UserRemoteDataSource {
  final Dio _dio;
  UserRemoteDataSource(this._dio);

  Future<List<Map<String, dynamic>>> getUsers({
    String? buildingId,
    String? search,
    String? role,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.users,
        queryParameters: {
          if (buildingId != null && buildingId.isNotEmpty)
            'building_id': buildingId,
          if (search != null && search.isNotEmpty) 'search': search,
          if (role != null && role.isNotEmpty) 'role': role,
        },
      );
      final data = response.data;
      if (data is Map && data.containsKey('results')) {
        return List<Map<String, dynamic>>.from(data['results']);
      }
      return List<Map<String, dynamic>>.from(data);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load users',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> getUser(String id) async {
    try {
      final response = await _dio.get(ApiEndpoints.userDetail(id));
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'User not found',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> createUser(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(ApiEndpoints.users, data: data);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to create user',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<Map<String, dynamic>> updateUser(
    String id,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.patch(
        ApiEndpoints.userDetail(id),
        data: data,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to update user',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<void> activateUser(String id) async {
    try {
      await _dio.post(ApiEndpoints.userActivate(id));
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to activate user',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<void> deactivateUser(String id) async {
    try {
      await _dio.post(ApiEndpoints.userDeactivate(id));
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to deactivate user',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<void> resetPassword(String id, String newPassword) async {
    try {
      await _dio.post(
        ApiEndpoints.userResetPassword(id),
        data: {'new_password': newPassword},
      );
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to reset password',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<void> setMessagingBlock(
    String id, {
    required bool blocked,
    required bool individualBlocked,
  }) async {
    try {
      await _dio.post(
        ApiEndpoints.userMessagingBlock(id),
        data: {
          'is_messaging_blocked': blocked,
          'is_individual_messaging_blocked': individualBlocked,
        },
      );
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to update messaging block',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }
}
