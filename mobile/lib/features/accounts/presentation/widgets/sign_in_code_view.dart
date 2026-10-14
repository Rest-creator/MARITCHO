import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_state.dart';

/// "Enter your code": one numeric field so Android can fill it from the
/// SMS; it signs in by itself as soon as the sixth digit is in.
class SignInCodeView extends StatefulWidget {
  final AuthCodeRequired state;
  final ValueChanged<String> onVerify;
  final VoidCallback onResend;
  final VoidCallback onChangeNumber;

  const SignInCodeView({
    super.key,
    required this.state,
    required this.onVerify,
    required this.onResend,
    required this.onChangeNumber,
  });

  @override
  State<SignInCodeView> createState() => _SignInCodeViewState();
}

class _SignInCodeViewState extends State<SignInCodeView> {
  final TextEditingController _code = TextEditingController();

  void _onChanged(String value) {
    if (value.length == 6 && !widget.state.isVerifying) widget.onVerify(value);
  }

  @override
  void didUpdateWidget(SignInCodeView oldWidget) {
    super.didUpdateWidget(oldWidget);
    // A refused code is cleared so the next attempt starts fresh.
    if (widget.state.errorMessage != null &&
        oldWidget.state.errorMessage == null) {
      _code.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    final String? error = widget.state.errorMessage;
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            'Enter your code',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            'We sent a 6-digit code to ${widget.state.phone}.',
            style: const TextStyle(color: AppTheme.coolGray),
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _code,
            autofocus: true,
            enabled: !widget.state.isVerifying,
            keyboardType: TextInputType.number,
            autofillHints: const <String>[AutofillHints.oneTimeCode],
            inputFormatters: <TextInputFormatter>[
              FilteringTextInputFormatter.digitsOnly,
              LengthLimitingTextInputFormatter(6),
            ],
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 26,
              letterSpacing: 10,
              fontWeight: FontWeight.w700,
            ),
            decoration: InputDecoration(
              labelText: '6-digit code',
              border: const OutlineInputBorder(),
              errorText: error,
            ),
            onChanged: _onChanged,
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              TextButton(
                onPressed: widget.onChangeNumber,
                child: const Text('Change number'),
              ),
              TextButton(
                onPressed: widget.state.isVerifying ? null : widget.onResend,
                child: const Text('Send a new code'),
              ),
            ],
          ),
          const SizedBox(height: 20),
          if (widget.state.isVerifying)
            const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }
}
