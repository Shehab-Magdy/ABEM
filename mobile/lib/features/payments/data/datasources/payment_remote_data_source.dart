import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for payment operations via REST API.
class PaymentRemoteDataSource {
  final Dio _dio;
  PaymentRemoteDataSource(this._dio);

  Future<List<Map<String, dynamic>>> getPayments({
    String? apartmentId,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.payments,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (apartmentId != null && apartmentId.isNotEmpty)
            'apartment': apartmentId,
        },
      );
      final data = response.data;
      if (data is Map && data.containsKey('results')) {
        return List<Map<String, dynamic>>.from(data['results']);
      }
      return List<Map<String, dynamic>>.from(data);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load payments',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> recordPayment(
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.post(ApiEndpoints.payments, data: data);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to record payment',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<Uint8List> getReceipt(String paymentId) async {
    try {
      final response = await _dio.get<List<int>>(
        ApiEndpoints.paymentReceipt(paymentId),
        options: Options(responseType: ResponseType.bytes),
      );
      return Uint8List.fromList(response.data!);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ?? 'Failed to load receipt',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }
}
