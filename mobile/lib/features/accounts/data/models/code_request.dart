import 'package:equatable/equatable.dart';

/// The BFF's answer to "send me a sign-in code" (`POST /api/session/code`).
class CodeRequest extends Equatable {
  /// False while the backend can't send codes yet: sign in without one.
  final bool isCodeRequired;
  final int resendAfterSeconds;

  const CodeRequest({
    required this.isCodeRequired,
    this.resendAfterSeconds = 0,
  });

  factory CodeRequest.fromJson(Map<String, dynamic> json) {
    final Object? wait = json['resend_after_seconds'];
    return CodeRequest(
      isCodeRequired: json['code_required'] == true,
      resendAfterSeconds: wait is int ? wait : 0,
    );
  }

  @override
  List<Object?> get props => <Object?>[isCodeRequired, resendAfterSeconds];
}
