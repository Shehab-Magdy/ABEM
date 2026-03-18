import 'api_client.dart';

class ApartmentsApi {
  final ApiClient apiClient;
  ApartmentsApi({required this.apiClient});

  /// All active buildings — used in sign-up wizard for any authenticated user.
  Future<List<Map<String, dynamic>>> buildingDirectory() async {
    final response = await apiClient.dio.get('/buildings/directory/');
    return List<Map<String, dynamic>>.from(response.data);
  }

  /// Unowned apartments for a building — used in sign-up wizard.
  Future<List<Map<String, dynamic>>> availableApartments(
      String buildingId) async {
    final response = await apiClient.dio.get(
      '/apartments/available/',
      queryParameters: {'building_id': buildingId},
    );
    return List<Map<String, dynamic>>.from(response.data);
  }

  /// Owner claims a vacant apartment during sign-up.
  Future<Map<String, dynamic>> claimApartment(String apartmentId) async {
    final response =
        await apiClient.dio.post('/apartments/$apartmentId/claim/');
    return response.data as Map<String, dynamic>;
  }
}
