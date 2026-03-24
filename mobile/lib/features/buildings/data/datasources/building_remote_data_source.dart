import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for building operations via REST API.
class BuildingRemoteDataSource {
  final Dio _dio;
  BuildingRemoteDataSource(this._dio);

  Future<List<Map<String, dynamic>>> getBuildings({
    String? search,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.buildings,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (search != null && search.isNotEmpty) 'search': search,
        },
      );
      final data = response.data;
      if (data is Map && data.containsKey('results')) {
        return List<Map<String, dynamic>>.from(data['results']);
      }
      return List<Map<String, dynamic>>.from(data);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load buildings',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> getBuilding(String id) async {
    try {
      final response = await _dio.get(ApiEndpoints.buildingDetail(id));
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Building not found',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> createBuilding(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(ApiEndpoints.buildings, data: data);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to create building',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<Map<String, dynamic>> updateBuilding(
    String id,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.patch(
        ApiEndpoints.buildingDetail(id),
        data: data,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to update building',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<void> deleteBuilding(String id) async {
    try {
      await _dio.delete(ApiEndpoints.buildingDetail(id));
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to delete building',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<void> activateBuilding(String id) async {
    try {
      await _dio.post(ApiEndpoints.buildingActivate(id));
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to activate',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<void> deactivateBuilding(String id) async {
    try {
      await _dio.post(ApiEndpoints.buildingDeactivate(id));
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to deactivate',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<List<Map<String, dynamic>>> getBuildingUnits(
    String buildingId, {
    int pageSize = 100,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.buildingApartments(buildingId),
        queryParameters: {'page_size': pageSize},
      );
      final data = response.data;
      if (data is Map && data.containsKey('results')) {
        return List<Map<String, dynamic>>.from(data['results']);
      }
      return List<Map<String, dynamic>>.from(data);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load units',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }
}
