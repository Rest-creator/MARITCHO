import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/features/accounts/data/repositories/account_repository.dart';
import 'package:mobile/features/messaging/data/models/chat_message.dart';
import 'package:mobile/features/messaging/data/repositories/chat_repository.dart';
import 'package:mobile/features/messaging/presentation/cubit/chat_state.dart';

class ChatCubit extends Cubit<ChatState> {
  final ChatRepository chatRepository;
  final AccountRepository accountRepository;
  final String jobId;

  String? _currentUserId;

  ChatCubit({
    required this.chatRepository,
    required this.accountRepository,
    required this.jobId,
  }) : super(const ChatInitial());

  Future<void> loadMessages() async {
    emit(const ChatLoading());

    if (_currentUserId == null) {
      final userResult = await accountRepository.getCurrentUser();
      userResult.match(
        onOk: (person) => _currentUserId = person.id,
        onError: (_) {},
      );
    }

    final result = await chatRepository.listMessages(jobId);
    result.match(
      onOk: (messages) {
        emit(ChatLoaded(messages: messages, currentUserId: _currentUserId));
        chatRepository.markRead(jobId);
      },
      onError: (failure) => emit(ChatFailure(errorMessage: failure.message)),
    );
  }

  Future<bool> sendMessage(String text, {String? mediaUrl}) async {
    final currentState = state;
    if (currentState is! ChatLoaded) return false;

    emit(currentState.copyWith(isSending: true));
    final result = await chatRepository.sendMessage(
      jobId: jobId,
      body: text,
      messageType: mediaUrl != null ? 'PHOTO' : 'TEXT',
      mediaUrl: mediaUrl,
    );

    return result.fold<bool>(
      onOk: (newMessage) {
        final List<ChatMessage> updated = [
          ...currentState.messages,
          newMessage,
        ];
        emit(currentState.copyWith(messages: updated, isSending: false));
        return true;
      },
      onError: (_) {
        emit(currentState.copyWith(isSending: false));
        return false;
      },
    );
  }
}
