import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for dashboard statistics via REST API.
class DashboardRemoteDataSource {
  final Dio _dio;
  DashboardRemoteDataSource(this._dio);

  Future<Map<String, dynamic>> getAdminDashboard({
    String? buildingId,
    String? dateFrom,
    String? dateTo,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.adminDashboard,
        queryParameters: {
          if (buildingId != null && buildingId.isNotEmpty)
            'building': buildingId,
          if (dateFrom != null && dateFrom.isNotEmpty) 'date_from': dateFrom,
          if (dateTo != null && dateTo.isNotEmpty) 'date_to': dateTo,
        },
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to load admin dashboard',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> getOwnerDashboard({
    String? dateFrom,
    String? dateTo,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.ownerDashboard,
        queryParameters: {
          if (dateFrom != null && dateFrom.isNotEmpty) 'date_from': dateFrom,
          if (dateTo != null && dateTo.isNotEmpty) 'date_to': dateTo,
        },
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to load owner dashboard',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }
}
