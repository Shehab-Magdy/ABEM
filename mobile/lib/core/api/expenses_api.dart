import 'api_client.dart';

class ExpensesApi {
  final ApiClient apiClient;
  ExpensesApi({required this.apiClient});

  Future<List<Map<String, dynamic>>> fetchExpenses({String? buildingId}) async {
    final response = await apiClient.dio.get(
      '/expenses/',
      queryParameters: buildingId != null ? {'building_id': buildingId} : null,
    );
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }
}
