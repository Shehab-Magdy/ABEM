import 'package:dio/dio.dart';

import 'api_endpoints.dart';

class NotificationsApi {
  final Dio _dio;
  NotificationsApi({required Dio dio}) : _dio = dio;

  Future<List<Map<String, dynamic>>> fetchNotifications() async {
    final response = await _dio.get(ApiEndpoints.notifications);
    final data = response.data;
    if (data is Map && data.containsKey('results')) {
      return List<Map<String, dynamic>>.from(data['results']);
    }
    return List<Map<String, dynamic>>.from(data);
  }

  Future<void> markRead(String id) async {
    await _dio.post(ApiEndpoints.notificationRead(id));
  }

  Future<void> markAllRead() async {
    await _dio.post('/notifications/mark-all-read/');
  }
}
