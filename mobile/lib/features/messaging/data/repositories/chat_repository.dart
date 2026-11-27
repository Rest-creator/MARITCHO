import 'package:dio/dio.dart';

import 'package:mobile/core/error/failure.dart';
import 'package:mobile/core/error/result.dart';
import 'package:mobile/features/messaging/data/models/chat_message.dart';

class ChatRepository {
  final Dio _dio;

  ChatRepository(this._dio);

  Future<Result<List<ChatMessage>, Failure>> listMessages(
    String jobId, {
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final Response<List<dynamic>> response = await _dio.get<List<dynamic>>(
        '/jobs/$jobId/messages',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      final List<ChatMessage> messages = (response.data ?? [])
          .map((item) => ChatMessage.fromJson(item as Map<String, dynamic>))
          .toList();
      return Ok(messages);
    } on DioException catch (error) {
      return Error(_failureFor(error));
    } on Object catch (error) {
      return Error(
        UnknownFailure(
          message: 'Could not load messages',
          exception: error is Exception ? error : Exception(error.toString()),
        ),
      );
    }
  }

  Future<Result<ChatMessage, Failure>> sendMessage({
    required String jobId,
    required String body,
    String messageType = 'TEXT',
    String? mediaUrl,
  }) async {
    try {
      final Response<Map<String, dynamic>> response = await _dio
          .post<Map<String, dynamic>>(
            '/jobs/$jobId/messages',
            data: {
              'message_type': messageType,
              'body': body,
              'media_url': mediaUrl,
            },
          );
      return Ok(ChatMessage.fromJson(response.data!));
    } on DioException catch (error) {
      return Error(_failureFor(error));
    } on Object catch (error) {
      return Error(
        UnknownFailure(
          message: 'Could not send message',
          exception: error is Exception ? error : Exception(error.toString()),
        ),
      );
    }
  }

  Future<Result<void, Failure>> markRead(String jobId) async {
    try {
      await _dio.post('/jobs/$jobId/messages/read');
      return const Ok(null);
    } on DioException catch (error) {
      return Error(_failureFor(error));
    } on Object catch (error) {
      return Error(
        UnknownFailure(
          message: 'Could not mark messages as read',
          exception: error is Exception ? error : Exception(error.toString()),
        ),
      );
    }
  }

  Failure _failureFor(DioException error) {
    final Object? data = error.response?.data;
    final Object? detail = data is Map ? data['detail'] : null;
    return NetworkFailure(
      message: detail?.toString() ?? error.message ?? 'Chat connection failed',
      exception: error,
    );
  }
}
