import 'package:flutter/material.dart';
import 'theme.dart';
import 'screens/welcome_screen.dart';

void main() {
  runApp(const EatSmartlyApp());
}

class EatSmartlyApp extends StatelessWidget {
  const EatSmartlyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EatSmartly',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const WelcomeScreen(),
    );
  }
}
