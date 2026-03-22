import 'package:flutter/material.dart';
import 'theme.dart';
import 'screens/welcome_screen.dart';
import 'services/api_service.dart';
import 'services/server_discovery.dart';

void main() async {
  // Ensure Flutter binding is initialized
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize API service (loads saved server URL)
  await EatSmartlyAPI.initialize();

  // Auto-discover server in background (non-blocking)
  _autoDiscoverServer();

  runApp(const EatSmartlyApp());
}

/// Automatically discover and connect to backend server
void _autoDiscoverServer() async {
  try {
    print('🔍 Auto-discovering backend server...');

    // Try to discover server
    final foundUrl = await ServerDiscovery.discoverServer();

    if (foundUrl != null) {
      print('✅ Server found at: $foundUrl');
      await EatSmartlyAPI.setBaseUrl(foundUrl);
      print('✅ Server configured automatically!');
    } else {
      print('⚠️  Could not auto-discover server. Using saved/default configuration.');
      print('ℹ️  Make sure backend is running: start_server.bat');
    }
  } catch (e) {
    print('⚠️  Auto-discovery failed: $e');
    print('ℹ️  Will use saved/default server configuration');
  }
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
