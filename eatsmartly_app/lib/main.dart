import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'screens/welcome_screen.dart';
import 'screens/home_screen.dart';
import 'screens/comprehensive_profile_screen.dart';
import 'services/api_service.dart';
import 'services/server_discovery.dart';
import 'services/auth_service.dart';
import 'services/supabase_service.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'firebase_options.dart';
void main() async {
  // Ensure Flutter binding is initialized
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  // Initialize Supabase
  await SupabaseService.initialize(
    url: 'https://reqfxmbjbfzhxvufrpsr.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlcWZ4bWJqYmZ6aHh2dWZycHNyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAxOTc4ODksImV4cCI6MjA4NTc3Mzg4OX0.6TOp7lIqbVCvgit-ApNon6xeXF4EQfhqf67ndYLu210',
  );

  // Initialize API service (loads saved server URL)
  await EatSmartlyAPI.initialize();

  // Try saved ngrok URL first, then auto-discover in background
  final savedNgrok = await ServerDiscovery.getSavedNgrokUrl();
  if (savedNgrok != null) {
    await EatSmartlyAPI.setBaseUrl(savedNgrok);
    debugPrint('✅ Using saved ngrok URL: $savedNgrok');
  }

  // Auto-discover server in background (non-blocking)
  _autoDiscoverServer();

  runApp(const EatSmartlyApp());
}

/// Automatically discover and connect to backend server
void _autoDiscoverServer() async {
  try {
    debugPrint('🔍 Auto-discovering backend server...');

    // Try to discover server
    final foundUrl = await ServerDiscovery.discoverServer();

    if (foundUrl != null) {
      debugPrint('✅ Server found at: $foundUrl');
      await EatSmartlyAPI.setBaseUrl(foundUrl);
      debugPrint('✅ Server configured automatically!');
    } else {
      debugPrint(
          '⚠️  Could not auto-discover server. Using saved/default configuration.');
      debugPrint('ℹ️  Make sure backend is running: start_server.bat');
    }
  } catch (e) {
    debugPrint('⚠️  Auto-discovery failed: $e');
    debugPrint('ℹ️  Will use saved/default server configuration');
  }
}

class EatSmartlyApp extends StatelessWidget {
  const EatSmartlyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<AuthService>(
          create: (_) => AuthService(),
        ),
      ],
      child: MaterialApp(
        title: 'EatSmartly',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const AuthWrapper(),
      ),
    );
  }
}

// Authentication wrapper to handle navigation based on auth state
class AuthWrapper extends StatefulWidget {
  const AuthWrapper({Key? key}) : super(key: key);

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  User? _previousUser;
  bool _showingWelcome = false;
  Future<bool>? _profileFuture;
  String? _lastCheckedUid;

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);

    return StreamBuilder<User?>(
      stream: authService.authStateChanges,
      builder: (context, snapshot) {
        debugPrint('🟡 AuthWrapper - Connection state: ${snapshot.connectionState}');
        debugPrint('🟡 AuthWrapper - Has data: ${snapshot.hasData}');
        debugPrint('🟡 AuthWrapper - User: ${snapshot.data?.email}');

        // Show loading screen while checking authentication
        if (snapshot.connectionState == ConnectionState.waiting) {
          debugPrint('🟡 AuthWrapper - Showing loading screen');
          return _buildLoadingScreen('Loading EatSmartly...');
        }

        // User is not authenticated - show welcome/login flow
        if (!snapshot.hasData || snapshot.data == null) {
          debugPrint('🟡 AuthWrapper - No user, showing WelcomeScreen');
          _previousUser = null;
          _showingWelcome = false;
          _profileFuture = null;
          _lastCheckedUid = null;
          return const WelcomeScreen();
        }

        final currentUser = snapshot.data!;

        // Check if this is a new authentication (user just logged in)
        final isNewLogin = _previousUser == null && currentUser != null;
        _previousUser = currentUser;

        debugPrint('🔵 AuthWrapper - Current user: ${currentUser.email}');
        debugPrint('🔵 AuthWrapper - User UID: ${currentUser.uid}');
        debugPrint('🔵 AuthWrapper - Is new login: $isNewLogin');

        // Show welcome popup for new login
        if (isNewLogin && !_showingWelcome) {
          _showingWelcome = true;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _showWelcomePopup(context, currentUser);
          });
        }

        // Cache the profile future so it doesn't re-fire on every rebuild
        if (_lastCheckedUid != currentUser.uid) {
          _lastCheckedUid = currentUser.uid;
          _profileFuture = authService.hasCompletedProfile();
        }

        // User is authenticated - check if profile is completed
        return FutureBuilder<bool>(
          future: _profileFuture,
          builder: (context, profileSnapshot) {
            debugPrint('🟡 AuthWrapper - Profile check state: ${profileSnapshot.connectionState}');
            debugPrint('🟡 AuthWrapper - Profile completed: ${profileSnapshot.data}');

            if (profileSnapshot.connectionState == ConnectionState.waiting) {
              return _buildLoadingScreen('Checking profile...');
            }

            // Profile not completed - show profile setup
            if (!profileSnapshot.hasData || !profileSnapshot.data!) {
              debugPrint('🟡 AuthWrapper - Profile incomplete, showing profile setup');
              return Scaffold(
                backgroundColor: Color(0xFFFFF8E1),
                appBar: AppBar(
                  title: Text('Profile Setup'),
                  backgroundColor: Colors.transparent,
                  actions: [
                    IconButton(
                      icon: Icon(Icons.logout, color: Colors.red),
                      onPressed: () async {
                        _showingWelcome = false;
                        await authService.signOut();
                      },
                    ),
                  ],
                ),
                body: ComprehensiveProfileScreen(),
              );
            }

            // Profile completed - show main app
            debugPrint('🟢 AuthWrapper - Profile complete, showing HomeScreen');
            return const HomeScreen();
          },
        );
      },
    );
  }

  Widget _buildLoadingScreen(String message) {
    return Scaffold(
      backgroundColor: Color(0xFFFFF8E1),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFFFC1CC)),
            ),
            SizedBox(height: 20),
            Text(
              message,
              style: TextStyle(
                fontSize: 18,
                color: Color(0xFF2C2C2C),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showWelcomePopup(BuildContext context, User user) {
    final userName = user.displayName ?? user.email?.split('@')[0] ?? 'User';

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext dialogContext) {
        // Auto-dismiss after 2 seconds from inside the dialog context
        Future.delayed(const Duration(seconds: 2), () {
          if (Navigator.of(dialogContext).canPop()) {
            Navigator.of(dialogContext).pop();
          }
          _showingWelcome = false;
        });

        return Dialog(
          backgroundColor: Colors.transparent,
          child: Container(
            padding: EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Color(0xFFFFF8E1),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 10,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.celebration,
                  size: 48,
                  color: Color(0xFFFFC1CC),
                ),
                SizedBox(height: 16),
                Text(
                  'Welcome!',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF2C2C2C),
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  userName,
                  style: TextStyle(
                    fontSize: 20,
                    color: Color(0xFF2C2C2C),
                  ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 16),
                Text(
                  'Welcome to EatSmartly!',
                  style: TextStyle(
                    fontSize: 16,
                    color: Color(0xFF666666),
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
