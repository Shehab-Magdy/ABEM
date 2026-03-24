import 'package:dio/dio.dart';

import 'api_endpoints.dart';

class BuildingsApi {
  final Dio _dio;
  BuildingsApi({required Dio dio}) : _dio = dio;

  Future<List<Map<String, dynamic>>> fetchBuildings() async {
    final response = await _dio.get(ApiEndpoints.buildings);
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }

  Future<Map<String, dynamic>> createBuilding(
      Map<String, dynamic> payload) async {
    final response = await _dio.post(ApiEndpoints.buildings, data: payload);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateBuilding(
      String id, Map<String, dynamic> payload) async {
    final response =
        await _dio.patch(ApiEndpoints.buildingDetail(id), data: payload);
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteBuilding(String id) async {
    await _dio.delete(ApiEndpoints.buildingDetail(id));
  }
}
