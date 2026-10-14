import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/repositories/auth_repository.dart';
import '../cubit/auth_cubit.dart';
import '../cubit/auth_state.dart';

/// Ports SignUp.dc.html's name+phone step only. The wireframe's 6-digit
/// SMS OTP step is dropped: the backend doesn't perform real OTP
/// verification yet (it's an explicitly documented dev mock pending
/// WhatsApp OTP, ADR-006/BACK-009) — showing a code-entry UI that
/// verifies nothing would be dishonest. "Continue" submits name+phone+role
/// directly against the real /token endpoint.
class SignUpPage extends StatefulWidget {
  final String role;

  const SignUpPage({super.key, required this.role});

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => AuthCubit(ctx.read<AuthRepository>()),
      child: Scaffold(
        appBar: AppBar(title: const Text("Let's get you set up")),
        body: BlocConsumer<AuthCubit, AuthState>(
          listener: (context, state) {
            if (!mounted) return; // Engineering Standard: Async Gap Safety

            if (state is AuthSuccess) {
              final route = state.person.role == 'BUYER'
                  ? '/employer-home'
                  : '/worker-skills';
              Navigator.of(context).pushReplacementNamed(route);
            } else if (state is AuthFailure) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(state.errorMessage),
                  backgroundColor: Colors.red,
                ),
              );
            }
          },
          builder: (context, state) {
            final isLoading = state is AuthLoading;
            return Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    "Just your name and phone number. No email needed.",
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 28),
                  TextField(
                    controller: _nameController,
                    enabled: !isLoading,
                    decoration: const InputDecoration(
                      labelText: 'Your name',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 18),
                  TextField(
                    controller: _phoneController,
                    enabled: !isLoading,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      labelText: 'Phone number',
                      hintText: '+263 77 412 3089',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 28),
                  ElevatedButton(
                    onPressed: isLoading
                        ? null
                        : () {
                            final phone = _phoneController.text.trim();
                            if (phone.isEmpty) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    'Enter a phone number to continue',
                                  ),
                                ),
                              );
                              return;
                            }
                            context.read<AuthCubit>().login(
                              phone: phone,
                              role: widget.role,
                            );
                          },
                    child: isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Continue'),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
