import 'package:dio/dio.dart';
import 'api_client.dart';

class BuildingsApi {
  final ApiClient apiClient;
  BuildingsApi({required this.apiClient});

  Future<List<Map<String, dynamic>>> fetchBuildings() async {
    final response = await apiClient.dio.get('/buildings/');
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }

  Future<Map<String, dynamic>> createBuilding(Map<String, dynamic> payload) async {
    final response = await apiClient.dio.post('/buildings/', data: payload);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateBuilding(
      String id, Map<String, dynamic> payload) async {
    final response = await apiClient.dio.patch('/buildings/$id/', data: payload);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteBuilding(String id) async {
    await apiClient.dio.delete('/buildings/$id/');
  }
}
