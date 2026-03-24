import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for expense operations via REST API.
class ExpenseRemoteDataSource {
  final Dio _dio;
  ExpenseRemoteDataSource(this._dio);

  Future<List<Map<String, dynamic>>> getExpenses({
    String? buildingId,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.expenses,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (buildingId != null && buildingId.isNotEmpty)
            'building': buildingId,
        },
      );
      final data = response.data;
      if (data is Map && data.containsKey('results')) {
        return List<Map<String, dynamic>>.from(data['results']);
      }
      return List<Map<String, dynamic>>.from(data);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load expenses',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> getExpense(String id) async {
    try {
      final response = await _dio.get(ApiEndpoints.expenseDetail(id));
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Expense not found',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> createExpense(
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.post(ApiEndpoints.expenses, data: data);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to create expense',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<Map<String, dynamic>> updateExpense(
    String id,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.patch(
        ApiEndpoints.expenseDetail(id),
        data: data,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to update expense',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<void> deleteExpense(String id) async {
    try {
      await _dio.delete(ApiEndpoints.expenseDetail(id));
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to delete expense',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> uploadBill(
    String expenseId,
    String filePath,
    String fileName,
  ) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(filePath, filename: fileName),
      });
      final response = await _dio.post(
        ApiEndpoints.expenseUpload(expenseId),
        data: formData,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to upload bill',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<List<Map<String, dynamic>>> getCategories({
    String? buildingId,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.expenseCategories,
        queryParameters: {
          if (buildingId != null && buildingId.isNotEmpty)
            'building': buildingId,
        },
      );
      final data = response.data;
      if (data is Map && data.containsKey('results')) {
        return List<Map<String, dynamic>>.from(data['results']);
      }
      return List<Map<String, dynamic>>.from(data);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load categories',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }
}
