import 'api_client.dart';

class PaymentsApi {
  final ApiClient apiClient;
  PaymentsApi({required this.apiClient});

  Future<List<Map<String, dynamic>>> fetchPayments() async {
    final response = await apiClient.dio.get('/payments/');
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }
}
