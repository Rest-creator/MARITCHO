import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Maricho',
      theme: AppTheme.lightTheme,
      home: const Scaffold(
        body: Center(child: Text('Maricho Mobile MVP')),
      ),
    );
  }
}
