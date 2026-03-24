import 'package:dio/dio.dart';

import 'api_endpoints.dart';

class ExpensesApi {
  final Dio _dio;
  ExpensesApi({required Dio dio}) : _dio = dio;

  Future<List<Map<String, dynamic>>> fetchExpenses({String? buildingId}) async {
    final response = await _dio.get(
      ApiEndpoints.expenses,
      queryParameters: buildingId != null ? {'building_id': buildingId} : null,
    );
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }
}
