import 'package:equatable/equatable.dart';

class ChatMessage extends Equatable {
  final String id;
  final String jobId;
  final String senderId;
  final String messageType;
  final String? body;
  final String? mediaUrl;
  final DateTime createdAt;
  final DateTime? readAt;

  const ChatMessage({
    required this.id,
    required this.jobId,
    required this.senderId,
    required this.messageType,
    this.body,
    this.mediaUrl,
    required this.createdAt,
    this.readAt,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as String,
      jobId: json['job_id'] as String,
      senderId: json['sender_id'] as String,
      messageType: json['message_type'] as String? ?? 'TEXT',
      body: json['body'] as String?,
      mediaUrl: json['media_url'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      readAt: json['read_at'] != null
          ? DateTime.parse(json['read_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'job_id': jobId,
      'sender_id': senderId,
      'message_type': messageType,
      'body': body,
      'media_url': mediaUrl,
      'created_at': createdAt.toIso8601String(),
      'read_at': readAt?.toIso8601String(),
    };
  }

  @override
  List<Object?> get props => [
    id,
    jobId,
    senderId,
    messageType,
    body,
    mediaUrl,
    createdAt,
    readAt,
  ];
}
