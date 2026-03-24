import 'package:dio/dio.dart';

import 'api_endpoints.dart';

class ApartmentsApi {
  final Dio _dio;
  ApartmentsApi({required Dio dio}) : _dio = dio;

  /// All active buildings — used in sign-up wizard for any authenticated user.
  Future<List<Map<String, dynamic>>> buildingDirectory() async {
    final response = await _dio.get(ApiEndpoints.buildingDirectory);
    return List<Map<String, dynamic>>.from(response.data);
  }

  /// Unowned apartments for a building — used in sign-up wizard.
  Future<List<Map<String, dynamic>>> availableApartments(
      String buildingId) async {
    final response = await _dio.get(
      ApiEndpoints.apartmentsAvailable,
      queryParameters: {'building_id': buildingId},
    );
    return List<Map<String, dynamic>>.from(response.data);
  }

  /// Owner claims a vacant apartment during sign-up.
  Future<Map<String, dynamic>> claimApartment(String apartmentId) async {
    final response = await _dio.post(ApiEndpoints.apartmentClaim(apartmentId));
    return response.data as Map<String, dynamic>;
  }
}
