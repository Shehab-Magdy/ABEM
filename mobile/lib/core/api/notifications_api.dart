import 'api_client.dart';

class NotificationsApi {
  final ApiClient apiClient;
  NotificationsApi({required this.apiClient});

  Future<List<Map<String, dynamic>>> fetchNotifications() async {
    final response = await apiClient.dio.get('/notifications/');
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }

  Future<void> markRead(String id) async {
    await apiClient.dio.post('/notifications/$id/mark-read/');
  }

  Future<void> markAllRead() async {
    await apiClient.dio.post('/notifications/mark-all-read/');
  }
}
