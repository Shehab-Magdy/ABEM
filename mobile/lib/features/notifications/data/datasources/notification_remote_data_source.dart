import 'package:dio/dio.dart';

import '../../../../core/api/api_endpoints.dart';
import '../../../../core/api/api_exception.dart';

/// Remote data source for notification operations via REST API.
class NotificationRemoteDataSource {
  final Dio _dio;
  NotificationRemoteDataSource(this._dio);

  Future<List<Map<String, dynamic>>> getNotifications({
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.notifications,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
        },
      );
      final data = response.data;
      if (data is Map && data.containsKey('results')) {
        return List<Map<String, dynamic>>.from(data['results']);
      }
      return List<Map<String, dynamic>>.from(data);
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to load notifications',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<void> markRead(String id) async {
    try {
      await _dio.post(ApiEndpoints.notificationRead(id));
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to mark notification as read',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<void> markAllRead() async {
    try {
      // Mark all as read by posting to the notifications endpoint with action
      await _dio.post(
        '${ApiEndpoints.notifications}mark-all-read/',
      );
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to mark all as read',
        statusCode: e.response?.statusCode ?? 0,
      );
    }
  }

  Future<Map<String, dynamic>> broadcast(
    String buildingId,
    String subject,
    String message,
  ) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.broadcast,
        data: {
          'building': buildingId,
          'subject': subject,
          'message': message,
        },
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to send broadcast',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }

  Future<Map<String, dynamic>> sendMessage(
    String recipientType,
    List<String> recipients,
    String subject,
    String body,
  ) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.sendMessage,
        data: {
          'recipient_type': recipientType,
          'recipients': recipients,
          'subject': subject,
          'body': body,
        },
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ServerException(
        e.response?.data?['detail']?.toString() ??
            'Failed to send message',
        statusCode: e.response?.statusCode ?? 0,
        fieldErrors: e.response?.data is Map
            ? Map<String, dynamic>.from(e.response!.data)
            : null,
      );
    }
  }
}
