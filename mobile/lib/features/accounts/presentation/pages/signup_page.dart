import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'package:mobile/core/theme/app_notification.dart';
import 'package:mobile/core/theme/app_theme.dart';
import 'package:mobile/core/theme/screen_shell.dart';
import 'package:mobile/features/accounts/data/repositories/auth_repository.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_cubit.dart';
import 'package:mobile/features/accounts/presentation/cubit/auth_state.dart';
import 'package:mobile/features/suburbs/data/models/suburb.dart';
import 'package:mobile/features/suburbs/data/repositories/suburbs_repository.dart';

/// Full-fidelity Sign Up / Setup Screen matching `frontend/src/features/accounts/SignUpScreen.tsx`:
/// - Step indicator: "Step 1 of 2" + 50% progress bar (for worker sign up)
/// - Title: "Let's get you set up" (or "Welcome back" when in login mode)
/// - Subtitle: "A few details so the right people can find you — no email needed."
/// - Segmented role tabs: "I need work done" (BUYER) vs "I find work" (WORKER)
/// - Full name field ("Your full name")
/// - Phone number with "+263" country tag and "71 950 9816" placeholder
/// - Password with eye visibility toggle ("At least 8 characters")
/// - Suburb selection ("Where are you based?" / "Use my location", with dynamic list)
/// - Suburb note: "We show you jobs near here first."
/// - Travel means tags: "Walking", "Kombi / bus", "Bicycle", "Motorbike", "Own vehicle"
/// - Emergency contact: "Emergency contact number (optional)", e.g. "77 200 0111"
/// - CTA button: "Create account" / "Log in"
/// - Footer switcher: "Already have an account? Log in"
/// - Legal agreement line: "By continuing you agree to our Terms and Conditions and Privacy Policy"
class SignUpPage extends StatefulWidget {
  final String role;
  final bool initialIsLogin;

  const SignUpPage({
    super.key,
    required this.role,
    this.initialIsLogin = false, // defaults to sign-up setup
  });

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  static const List<String> _travelMeansOptions = [
    "Walking",
    "Kombi / bus",
    "Bicycle",
    "Motorbike",
    "Own vehicle",
  ];

  late bool _isLogin;
  late String _role;
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emergencyController = TextEditingController();

  bool _showPassword = false;
  String? _selectedSuburb;
  final Set<String> _selectedTravelMeans = <String>{};
  String? _validationError;

  List<Suburb> _suburbs = [];
  bool _loadingSuburbs = false;

  @override
  void initState() {
    super.initState();
    _isLogin = widget.initialIsLogin;
    _role = widget.role;
    _loadSuburbs();
  }

  Future<void> _loadSuburbs() async {
    setState(() => _loadingSuburbs = true);
    final repo = context.read<SuburbsRepository>();
    final result = await repo.listSuburbs();
    if (mounted) {
      setState(() {
        _loadingSuburbs = false;
        if (result.isOk) {
          _suburbs = result.okValue;
        }
      });
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _emergencyController.dispose();
    super.dispose();
  }

  void _validateAndSubmit(BuildContext context) {
    setState(() => _validationError = null);
    final phone = _phoneController.text.trim();
    final password = _passwordController.text;
    final name = _nameController.text.trim();

    if (!_isLogin && name.length < 2) {
      setState(
        () => _validationError =
            "Tell us your name so people know who they're dealing with.",
      );
      return;
    }
    if (phone.isEmpty) {
      setState(
        () => _validationError = "Enter your mobile number, e.g. 71 950 9816.",
      );
      return;
    }
    if (password.length < 8) {
      setState(
        () => _validationError = "Use a password with at least 8 characters.",
      );
      return;
    }
    if (!_isLogin && (_selectedSuburb == null || _selectedSuburb!.isEmpty)) {
      setState(
        () => _validationError = _role == 'WORKER'
            ? "Choose the suburb you're based in so we can show jobs nearby."
            : "Choose the suburb where you usually need work done.",
      );
      return;
    }

    if (_isLogin) {
      context.read<AuthCubit>().signIn(phone: phone, password: password);
    } else {
      context.read<AuthCubit>().signUp(
        phone: phone,
        password: password,
        name: name,
        role: _role,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isWorker = _role == 'WORKER';

    return BlocProvider(
      create: (ctx) => AuthCubit(ctx.read<AuthRepository>()),
      child: ScreenShell(
        appBar: AppBar(
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: AppTheme.text),
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          actions: [
            if (!_isLogin && isWorker)
              const Padding(
                padding: EdgeInsets.only(right: 20, top: 16),
                child: Text(
                  'Step 1 of 2',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.cyanAccent,
                  ),
                ),
              ),
          ],
        ),
        child: BlocConsumer<AuthCubit, AuthState>(
          listener: (context, state) {
            if (!mounted) return;

            if (state is AuthSuccess) {
              AppNotification.success(
                context,
                _isLogin
                    ? "Signed in successfully"
                    : "Account created successfully",
                title: "Welcome ${state.person.displayName ?? 'back'}",
              );
              final route = state.person.role == 'BUYER'
                  ? '/employer-home'
                  : (_isLogin ? '/worker-home' : '/worker-skills');
              Navigator.of(context).pushReplacementNamed(route);
            } else if (state is AuthFailure) {
              AppNotification.error(
                context,
                state.errorMessage,
                title: "Authentication failed",
              );
            }
          },
          builder: (context, state) {
            final isLoading = state is AuthLoading;

            return SingleChildScrollView(
              padding: const EdgeInsets.symmetric(
                horizontal: 20.0,
                vertical: 8,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Progress Bar for Step 1 of 2
                  if (!_isLogin && isWorker) ...[
                    Container(
                      height: 4,
                      decoration: BoxDecoration(
                        color: AppTheme.lineSubtle,
                        borderRadius: BorderRadius.circular(2),
                      ),
                      child: FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: 0.5,
                        child: Container(
                          decoration: BoxDecoration(
                            color: AppTheme.cyanAccent,
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Display Title
                  Text(
                    _isLogin ? "Welcome back" : "Let's get you set up",
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.text,
                      letterSpacing: -0.5,
                    ),
                  ),
                  const SizedBox(height: 8),

                  // Subtitle
                  Text(
                    _isLogin ? "Log in with your phone number and password." : "A few details so the right people can find you — no email needed.",
                    style: const TextStyle(
                      fontSize: 14,
                      color: AppTheme.textSecondary,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Role Switcher Segmented Control
                  Container(
                    height: 48,
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: AppTheme.glass,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.lineSubtle),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _role = 'BUYER'),
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 180),
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: _role == 'BUYER'
                                    ? AppTheme.cyanAccent
                                    : Colors.transparent,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                'I need work done',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: _role == 'BUYER'
                                      ? FontWeight.w700
                                      : FontWeight.w500,
                                  color: _role == 'BUYER'
                                      ? Colors.white
                                      : AppTheme.textMuted,
                                ),
                              ),
                            ),
                          ),
                        ),
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _role = 'WORKER'),
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 180),
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: _role == 'WORKER'
                                    ? AppTheme.emeraldAccent
                                    : Colors.transparent,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                'I find work',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: _role == 'WORKER'
                                      ? FontWeight.w700
                                      : FontWeight.w500,
                                  color: _role == 'WORKER'
                                      ? Colors.white
                                      : AppTheme.textMuted,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Full name if sign up
                  if (!_isLogin) ...[
                    const Text(
                      'Your full name',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppTheme.glassStrong,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.line),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      alignment: Alignment.centerLeft,
                      child: TextField(
                        controller: _nameController,
                        style: const TextStyle(
                          color: AppTheme.text,
                          fontSize: 15,
                        ),
                        decoration: const InputDecoration(
                          hintText: 'Tinotenda Mupezeni',
                          hintStyle: TextStyle(color: AppTheme.textMuted),
                          border: InputBorder.none,
                          isDense: true,
                        ),
                      ),
                    ),
                    const SizedBox(height: 18),
                  ],

                  // Phone number field
                  const Text(
                    'Phone number',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    height: 52,
                    decoration: BoxDecoration(
                      color: AppTheme.glassStrong,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.line),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14),
                          alignment: Alignment.center,
                          decoration: const BoxDecoration(
                            border: Border(
                              right: BorderSide(color: AppTheme.lineSubtle),
                            ),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                '+263',
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.text,
                                ),
                              ),
                              SizedBox(width: 4),
                              Icon(
                                Icons.keyboard_arrow_down,
                                size: 18,
                                color: AppTheme.textMuted,
                              ),
                            ],
                          ),
                        ),
                        Expanded(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 14),
                            child: TextField(
                              controller: _phoneController,
                              keyboardType: TextInputType.phone,
                              style: const TextStyle(
                                color: AppTheme.text,
                                fontSize: 15,
                              ),
                              decoration: const InputDecoration(
                                hintText: '71 950 9816',
                                hintStyle: TextStyle(color: AppTheme.textMuted),
                                border: InputBorder.none,
                                isDense: true,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),

                  // Password field
                  const Text(
                    'Password',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    height: 52,
                    decoration: BoxDecoration(
                      color: AppTheme.glassStrong,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.line),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _passwordController,
                            obscureText: !_showPassword,
                            style: const TextStyle(
                              color: AppTheme.text,
                              fontSize: 15,
                            ),
                            decoration: const InputDecoration(
                              hintText: 'At least 8 characters',
                              hintStyle: TextStyle(color: AppTheme.textMuted),
                              border: InputBorder.none,
                              isDense: true,
                            ),
                          ),
                        ),
                        IconButton(
                          icon: Icon(
                            _showPassword
                                ? Icons.visibility_off
                                : Icons.visibility,
                            color: AppTheme.textMuted,
                            size: 20,
                          ),
                          onPressed: () =>
                              setState(() => _showPassword = !_showPassword),
                        ),
                      ],
                    ),
                  ),

                  // Sign up specific fields (Where are you based, Suburbs, Travel means, Emergency contact)
                  if (!_isLogin) ...[
                    const SizedBox(height: 22),

                    // Where are you based? + Use my location
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          isWorker
                              ? "Where are you based?"
                              : "Where do you need work done?",
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                        GestureDetector(
                          onTap: () {
                            if (_suburbs.isNotEmpty) {
                              setState(
                                () => _selectedSuburb = _suburbs.first.name,
                              );
                            }
                          },
                          child: const Row(
                            children: [
                              Icon(
                                Icons.near_me_outlined,
                                size: 14,
                                color: AppTheme.cyanAccent,
                              ),
                              SizedBox(width: 4),
                              Text(
                                'Use my location',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: AppTheme.cyanAccent,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    // Suburb dropdown picker
                    Container(
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppTheme.glassStrong,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.line),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: _selectedSuburb,
                          isExpanded: true,
                          hint: Text(
                            _loadingSuburbs
                                ? "Loading suburbs…"
                                : "Choose your suburb",
                            style: const TextStyle(
                              color: AppTheme.textMuted,
                              fontSize: 14,
                            ),
                          ),
                          dropdownColor: AppTheme.brandNavy,
                          icon: const Icon(
                            Icons.keyboard_arrow_down,
                            color: AppTheme.textMuted,
                          ),
                          items: _suburbs.map((suburb) {
                            return DropdownMenuItem<String>(
                              value: suburb.name,
                              child: Text(
                                suburb.name,
                                style: const TextStyle(
                                  color: AppTheme.text,
                                  fontSize: 14,
                                ),
                              ),
                            );
                          }).toList(),
                          onChanged: (val) =>
                              setState(() => _selectedSuburb = val),
                        ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'We show you jobs near here first.',
                      style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                    ),
                    const SizedBox(height: 20),

                    // How do you get to jobs? (for workers)
                    if (isWorker) ...[
                      const Text(
                        'How do you get to jobs?',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: _travelMeansOptions.map((mode) {
                          final isSelected = _selectedTravelMeans.contains(
                            mode,
                          );
                          return FilterChip(
                            label: Text(mode),
                            selected: isSelected,
                            onSelected: (selected) {
                              setState(() {
                                if (selected) {
                                  _selectedTravelMeans.add(mode);
                                } else {
                                  _selectedTravelMeans.remove(mode);
                                }
                              });
                            },
                            backgroundColor: AppTheme.glass,
                            selectedColor: AppTheme.cyanTint,
                            side: BorderSide(
                              color: isSelected
                                  ? AppTheme.cyanAccent
                                  : AppTheme.lineSubtle,
                            ),
                            labelStyle: TextStyle(
                              color: isSelected
                                  ? AppTheme.cyanAccent
                                  : AppTheme.textSecondary,
                              fontWeight: isSelected
                                  ? FontWeight.w700
                                  : FontWeight.w500,
                              fontSize: 13,
                            ),
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: 20),
                    ],

                    // Emergency contact number (optional)
                    const Text(
                      'Emergency contact number (optional)',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppTheme.glassStrong,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.line),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      alignment: Alignment.centerLeft,
                      child: TextField(
                        controller: _emergencyController,
                        keyboardType: TextInputType.phone,
                        style: const TextStyle(
                          color: AppTheme.text,
                          fontSize: 15,
                        ),
                        decoration: const InputDecoration(
                          hintText: 'e.g. 77 200 0111',
                          hintStyle: TextStyle(color: AppTheme.textMuted),
                          border: InputBorder.none,
                          isDense: true,
                        ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Someone we can call if something goes wrong on a job.',
                      style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                    ),
                  ],

                  // Validation Error Message
                  if (_validationError != null) ...[
                    const SizedBox(height: 16),
                    Text(
                      _validationError!,
                      style: const TextStyle(
                        color: AppTheme.danger,
                        fontSize: 13,
                      ),
                    ),
                  ],

                  const SizedBox(height: 28),

                  // CTA Button: "Create account" or "Log in"
                  SizedBox(
                    height: 54,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _role == 'WORKER'
                            ? AppTheme.emeraldAccent
                            : AppTheme.cyanAccent,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      onPressed: isLoading
                          ? null
                          : () => _validateAndSubmit(context),
                      child: isLoading
                          ? const SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 2.5,
                              ),
                            )
                          : Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  _isLogin ? 'Log in' : 'Create account',
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                const Icon(Icons.arrow_forward, size: 18),
                              ],
                            ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Switch between Login and Create Account
                  Center(
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          _isLogin = !_isLogin;
                          _validationError = null;
                        });
                      },
                      child: RichText(
                        text: TextSpan(
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppTheme.textSecondary,
                          ),
                          children: [
                            TextSpan(
                              text: _isLogin
                                  ? "Don't have an account? "
                                  : "Already have an account? ",
                            ),
                            TextSpan(
                              text: _isLogin ? "Create account" : "Log in",
                              style: const TextStyle(
                                color: AppTheme.cyanAccent,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Legal agreement line
                  Center(
                    child: Text(
                      'By continuing you agree to our Terms and Conditions and Privacy Policy',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 12,
                        color: AppTheme.textMuted.withValues(alpha: 0.8),
                        height: 1.4,
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
