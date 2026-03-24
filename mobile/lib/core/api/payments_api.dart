import 'package:dio/dio.dart';

import 'api_endpoints.dart';

class PaymentsApi {
  final Dio _dio;
  PaymentsApi({required Dio dio}) : _dio = dio;

  Future<List<Map<String, dynamic>>> fetchPayments() async {
    final response = await _dio.get(ApiEndpoints.payments);
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }
}
