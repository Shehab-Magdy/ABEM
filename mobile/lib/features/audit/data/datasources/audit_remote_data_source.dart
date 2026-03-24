import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for audit log operations via REST API.
class AuditRemoteDataSource {
  final Dio _dio;
  AuditRemoteDataSource(this._dio);

  Future<Map<String, dynamic>> getAuditLogs({
    String? entityType,
    String? action,
    String? dateFrom,
    String? dateTo,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.audit,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (entityType != null && entityType.isNotEmpty)
            'entity_type': entityType,
          if (action != null && action.isNotEmpty) 'action': action,
          if (dateFrom != null && dateFrom.isNotEmpty) 'date_from': dateFrom,
          if (dateTo != null && dateTo.isNotEmpty) 'date_to': dateTo,
        },
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to load audit logs',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }
}
