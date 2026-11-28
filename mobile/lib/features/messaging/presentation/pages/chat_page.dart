import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_notification.dart';
import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/core/theme/screen_shell.dart';
import 'package:mobile/features/accounts/data/repositories/account_repository.dart';
import 'package:mobile/features/messaging/data/repositories/chat_repository.dart';
import 'package:mobile/features/messaging/presentation/cubit/chat_cubit.dart';
import 'package:mobile/features/messaging/presentation/cubit/chat_state.dart';
import 'package:mobile/features/messaging/presentation/widgets/message_bubble.dart';

/// Design 3 · Real-Time Chat (matching web ChatScreen).
/// Polished with ScreenShell, ambient glows, quick action buttons,
/// clear message bubbles, and floating delivery error notifications.
class ChatPage extends StatelessWidget {
  final String jobId;
  final String? jobTitle;

  const ChatPage({super.key, required this.jobId, this.jobTitle});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => ChatCubit(
        chatRepository: ctx.read<ChatRepository>(),
        accountRepository: ctx.read<AccountRepository>(),
        jobId: jobId,
      )..loadMessages(),
      child: _ChatView(jobTitle: jobTitle),
    );
  }
}

class _ChatView extends StatefulWidget {
  final String? jobTitle;

  const _ChatView({this.jobTitle});

  @override
  State<_ChatView> createState() => _ChatViewState();
}

class _ChatViewState extends State<_ChatView> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent + 80,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return ScreenShell(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          title: Text(
            widget.jobTitle ?? 'Job Chat',
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh, color: Colors.white),
              onPressed: () => context.read<ChatCubit>().loadMessages(),
            ),
          ],
        ),
        body: Column(
          children: [
            Expanded(
              child: BlocConsumer<ChatCubit, ChatState>(
                listener: (context, state) {
                  if (!mounted) return;
                  if (state is ChatLoaded) {
                    WidgetsBinding.instance.addPostFrameCallback((_) {
                      _scrollToBottom();
                    });
                  }
                },
                builder: (context, state) {
                  if (state is ChatLoading || state is ChatInitial) {
                    return const Center(
                      child: CircularProgressIndicator(
                        color: AppTheme.cyanAccent,
                      ),
                    );
                  }
                  if (state is ChatFailure) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(
                              Icons.chat_bubble_outline,
                              color: AppTheme.textMuted,
                              size: 48,
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Could not load chat: ${state.errorMessage}',
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                color: AppTheme.textSecondary,
                              ),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              onPressed: () =>
                                  context.read<ChatCubit>().loadMessages(),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.cyanAccent,
                              ),
                              child: const Text('Retry'),
                            ),
                          ],
                        ),
                      ),
                    );
                  }

                  final loadedState = state as ChatLoaded;
                  final messages = loadedState.messages;

                  if (messages.isEmpty) {
                    return const Center(
                      child: Padding(
                        padding: EdgeInsets.all(32),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.chat_outlined,
                              size: 56,
                              color: AppTheme.textMuted,
                            ),
                            SizedBox(height: 16),
                            Text(
                              'No messages yet',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                            ),
                            SizedBox(height: 6),
                            Text(
                              'Say hello, share directions, or confirm job details directly.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: AppTheme.textSecondary,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }

                  return ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 16,
                    ),
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      final msg = messages[index];
                      final isMe =
                          loadedState.currentUserId != null &&
                          msg.senderId == loadedState.currentUserId;
                      return MessageBubble(message: msg, isMe: isMe);
                    },
                  );
                },
              ),
            ),
            _buildComposer(context),
          ],
        ),
      ),
    );
  }

  Widget _buildComposer(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppTheme.colorBgRaised,
        border: const Border(top: BorderSide(color: AppTheme.line)),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: AppTheme.glass,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: AppTheme.line),
                ),
                child: TextField(
                  controller: _messageController,
                  textCapitalization: TextCapitalization.sentences,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: const InputDecoration(
                    hintText: 'Type a message...',
                    hintStyle: TextStyle(color: AppTheme.textMuted),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 10,
                    ),
                    border: InputBorder.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            BlocBuilder<ChatCubit, ChatState>(
              builder: (context, state) {
                final isSending = state is ChatLoaded && state.isSending;
                return IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: AppTheme.cyanAccent,
                    padding: const EdgeInsets.all(12),
                  ),
                  icon: isSending
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.send, color: Colors.white, size: 20),
                  onPressed: isSending
                      ? null
                      : () async {
                          final text = _messageController.text.trim();
                          if (text.isEmpty) return;
                          _messageController.clear();
                          final cubit = context.read<ChatCubit>();
                          final ok = await cubit.sendMessage(text);
                          if (!ok && context.mounted) {
                            AppNotification.show(
                              context,
                              message: 'Could not deliver message',
                              type: NotificationType.error,
                            );
                          }
                        },
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
