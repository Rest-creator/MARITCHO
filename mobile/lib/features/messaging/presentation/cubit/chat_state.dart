import 'package:equatable/equatable.dart';

import 'package:mobile/features/messaging/data/models/chat_message.dart';

abstract class ChatState extends Equatable {
  const ChatState();

  @override
  List<Object?> get props => [];
}

class ChatInitial extends ChatState {
  const ChatInitial();
}

class ChatLoading extends ChatState {
  const ChatLoading();
}

class ChatLoaded extends ChatState {
  final List<ChatMessage> messages;
  final bool isSending;
  final String? currentUserId;

  const ChatLoaded({
    required this.messages,
    this.isSending = false,
    this.currentUserId,
  });

  ChatLoaded copyWith({
    List<ChatMessage>? messages,
    bool? isSending,
    String? currentUserId,
  }) {
    return ChatLoaded(
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      currentUserId: currentUserId ?? this.currentUserId,
    );
  }

  @override
  List<Object?> get props => [messages, isSending, currentUserId];
}

class ChatFailure extends ChatState {
  final String errorMessage;

  const ChatFailure({required this.errorMessage});

  @override
  List<Object?> get props => [errorMessage];
}
