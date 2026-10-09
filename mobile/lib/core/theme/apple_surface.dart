import 'dart:ui';
import 'package:flutter/material.dart';

/// An Apple-inspired translucent surface using BackdropFilter.
/// Best used for AppBars, BottomNavigationBar backgrounds, or sticky headers.
class AppleTranslucentSurface extends StatelessWidget {
  final Widget child;
  final double blurSigma;
  final Color baseColor;

  const AppleTranslucentSurface({
    super.key,
    required this.child,
    this.blurSigma = 10.0,
    this.baseColor = const Color(0xCCFFFFFF), // 80% opacity white
  });

  @override
  Widget build(BuildContext context) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blurSigma, sigmaY: blurSigma),
        child: Container(
          color: baseColor,
          child: child,
        ),
      ),
    );
  }
}

/// An Apple-inspired Spring animation wrapper for buttons.
class AppleSpringButton extends StatefulWidget {
  final Widget child;
  final VoidCallback onPressed;

  const AppleSpringButton({
    super.key,
    required this.child,
    required this.onPressed,
  });

  @override
  State<AppleSpringButton> createState() => _AppleSpringButtonState();
}

class _AppleSpringButtonState extends State<AppleSpringButton> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 150), // Snappy press
      reverseDuration: const Duration(milliseconds: 400), // Springy release
    );
    
    // Simulating a spring using easeOutElastic for the release
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.95).animate(
      CurvedAnimation(
        parent: _controller,
        curve: Curves.easeOut,
        reverseCurve: Curves.easeOutElastic, 
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTapDown(TapDownDetails details) {
    _controller.forward();
  }

  void _onTapUp(TapUpDetails details) {
    _controller.reverse();
    widget.onPressed();
  }

  void _onTapCancel() {
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: _onTapDown,
      onTapUp: _onTapUp,
      onTapCancel: _onTapCancel,
      behavior: HitTestBehavior.opaque,
      child: ScaleTransition(
        scale: _scaleAnimation,
        child: widget.child,
      ),
    );
  }
}
