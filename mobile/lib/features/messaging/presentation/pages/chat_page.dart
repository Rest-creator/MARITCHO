import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/accounts/data/repositories/account_repository.dart';
import 'package:mobile/features/messaging/data/repositories/chat_repository.dart';
import 'package:mobile/features/messaging/presentation/cubit/chat_cubit.dart';
import 'package:mobile/features/messaging/presentation/cubit/chat_state.dart';
import 'package:mobile/features/messaging/presentation/widgets/message_bubble.dart';

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
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.jobTitle ?? 'Job Chat'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
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
                  return const Center(child: CircularProgressIndicator());
                }
                if (state is ChatFailure) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          'Could not load chat: ${state.errorMessage}',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: () =>
                              context.read<ChatCubit>().loadMessages(),
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  );
                }

                final loadedState = state as ChatLoaded;
                final messages = loadedState.messages;

                if (messages.isEmpty) {
                  return const Center(
                    child: Text(
                      'No messages yet.\nSay hello or discuss job details.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                  );
                }

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
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
    );
  }

  Widget _buildComposer(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        border: Border(
          top: BorderSide(color: AppTheme.lightBlueGray.withValues(alpha: 0.3)),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _messageController,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  hintText: 'Type a message...',
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 10,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  filled: true,
                  fillColor: AppTheme.lightBlueGray.withValues(alpha: 0.2),
                ),
              ),
            ),
            const SizedBox(width: 8),
            BlocBuilder<ChatCubit, ChatState>(
              builder: (context, state) {
                final isSending = state is ChatLoaded && state.isSending;
                return IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: AppTheme.primaryBlueGray,
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
                      : const Icon(Icons.send, color: Colors.white),
                  onPressed: isSending
                      ? null
                      : () async {
                          final text = _messageController.text.trim();
                          if (text.isEmpty) return;
                          _messageController.clear();
                          final cubit = context.read<ChatCubit>();
                          final messenger = ScaffoldMessenger.of(context);
                          final ok = await cubit.sendMessage(text);
                          if (!ok && mounted) {
                            messenger.showSnackBar(
                              const SnackBar(
                                content: Text('Could not deliver message'),
                              ),
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
