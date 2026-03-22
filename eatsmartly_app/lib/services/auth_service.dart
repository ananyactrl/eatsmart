import 'dart:convert';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:local_auth/local_auth.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'supabase_service.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();
  final LocalAuthentication _localAuth = LocalAuthentication();

  // Get current user
  User? get currentUser => _auth.currentUser;

  // Auth state stream
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  // ── Email & Password Sign Up ───────────────────────────────
  Future<UserCredential?> signUpWithEmailPassword({
    required String email,
    required String password,
  }) async {
    try {
      UserCredential result = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      await result.user?.sendEmailVerification();
      // syncFirebaseUser is a no-op in the new schema but kept for logging
      if (result.user != null) {
        try {
          await SupabaseService.instance.syncFirebaseUser(result.user!);
        } catch (e) {
          debugPrint('Supabase sync failed (non-critical): $e');
        }
      }
      return result;
    } on FirebaseAuthException catch (e) {
      throw _handleAuthError(e);
    }
  }

  // ── Email & Password Sign In ───────────────────────────────
  Future<UserCredential?> signInWithEmailPassword({
    required String email,
    required String password,
  }) async {
    try {
      UserCredential result = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      await _storeUserForBiometric(email, password);
      if (result.user != null) {
        try {
          await SupabaseService.instance.syncFirebaseUser(result.user!);
        } catch (e) {
          debugPrint('Supabase sync failed (non-critical): $e');
        }
      }
      return result;
    } on FirebaseAuthException catch (e) {
      throw _handleAuthError(e);
    }
  }

  // ── Google Sign In ─────────────────────────────────────────
  Future<UserCredential?> signInWithGoogle() async {
    try {
      debugPrint('🔵 Starting Google Sign In...');
      await _googleSignIn.signOut();

      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) throw 'Google sign in was cancelled';

      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      UserCredential result = await _auth.signInWithCredential(credential);
      debugPrint('🟢 Google sign in successful: ${result.user?.email}');

      if (result.user != null) {
        try {
          await SupabaseService.instance.syncFirebaseUser(result.user!);
        } catch (e) {
          debugPrint('🟡 Supabase sync failed (non-critical): $e');
        }
      }
      return result;
    } catch (e) {
      debugPrint('🔴 Google sign in error: $e');
      throw 'Google sign in failed: $e';
    }
  }

  // ── Google Sign Up ─────────────────────────────────────────
  Future<UserCredential?> signUpWithGoogle() async {
    try {
      debugPrint('🔵 Starting Google Sign Up...');
      await _googleSignIn.signOut();

      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) throw 'Google sign up was cancelled';

      final signInMethods =
          await _auth.fetchSignInMethodsForEmail(googleUser.email);
      if (signInMethods.isNotEmpty) {
        await _googleSignIn.signOut();
        throw 'Account already exists with this email. Please sign in instead.';
      }

      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      UserCredential result = await _auth.signInWithCredential(credential);
      debugPrint('🟢 Google sign up successful: ${result.user?.email}');

      if (result.user != null) {
        try {
          await SupabaseService.instance.syncFirebaseUser(result.user!);
        } catch (e) {
          debugPrint('🟡 Supabase sync failed (non-critical): $e');
        }
      }
      return result;
    } catch (e) {
      debugPrint('🔴 Google sign up error: $e');
      throw 'Google sign up failed: $e';
    }
  }

  // ── Biometric Authentication ───────────────────────────────
  Future<bool> isBiometricAvailable() async {
    try {
      final isAvailable = await _localAuth.canCheckBiometrics;
      final isDeviceSupported = await _localAuth.isDeviceSupported();
      return isAvailable && isDeviceSupported;
    } catch (e) {
      return false;
    }
  }

  Future<List<BiometricType>> getAvailableBiometrics() async {
    try {
      return await _localAuth.getAvailableBiometrics();
    } catch (e) {
      return [];
    }
  }

  Future<bool> authenticateWithBiometrics() async {
    try {
      final bool didAuthenticate = await _localAuth.authenticate(
        localizedReason: 'Please authenticate to sign in to EatSmartly',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
      if (didAuthenticate) {
        return await _signInWithStoredCredentials();
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  // ── Password Reset ─────────────────────────────────────────
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email);
    } on FirebaseAuthException catch (e) {
      throw _handleAuthError(e);
    }
  }

  // ── Sign Out ───────────────────────────────────────────────
  Future<void> signOut() async {
    try {
      await Future.wait([
        _auth.signOut(),
        _googleSignIn.signOut(),
      ]);
      await _clearStoredCredentials();
    } catch (e) {
      throw 'Sign out failed: $e';
    }
  }

  // ── Profile: check completed ───────────────────────────────
  Future<bool> hasCompletedProfile() async {
    try {
      if (currentUser == null) {
        debugPrint('🔴 hasCompletedProfile: No current user');
        return false;
      }

      final firebaseUid = currentUser!.uid;
      debugPrint('🔵 hasCompletedProfile: checking uid=$firebaseUid');

      // Check local cache first (fast path)
      final prefs = await SharedPreferences.getInstance();
      final localCompleted = prefs.getBool('profile_completed_$firebaseUid') ?? false;
      if (localCompleted) {
        debugPrint('🔵 hasCompletedProfile: local cache says completed');
        return true;
      }

      // Fall back to Supabase
      try {
        final exists = await SupabaseService.instance.profileExists(firebaseUid);
        debugPrint('🔵 hasCompletedProfile: Supabase result = $exists');
        if (exists) {
          // Cache it locally so next check is instant
          await prefs.setBool('profile_completed_$firebaseUid', true);
        }
        return exists;
      } catch (e) {
        debugPrint('🟡 Supabase check failed, using local storage: $e');
        return localCompleted;
      }
    } catch (e) {
      debugPrint('🔴 hasCompletedProfile error: $e');
      return false;
    }
  }

  // ── Profile: save ──────────────────────────────────────────
  Future<bool> saveUserProfile(Map<String, dynamic> profileData) async {
    try {
      if (currentUser == null) return false;

      final firebaseUid = currentUser!.uid;
      final email = currentUser!.email ?? '';

      bool supabaseSuccess = false;
      try {
        supabaseSuccess = await SupabaseService.instance.saveUserProfile(
          firebaseUserId: firebaseUid,
          email: email,
          profileData: profileData,
        );
        debugPrint('🔵 Supabase saveUserProfile returned: $supabaseSuccess');
      } catch (e) {
        debugPrint('🟡 Supabase save threw exception: $e');
      }

      // Always save locally as fallback / cache
      await markProfileCompleted();
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('user_profile_$firebaseUid', json.encode(profileData));

      if (!supabaseSuccess) {
        debugPrint('🟡 Supabase save failed — profile saved locally only');
      }

      // Return true as long as local save succeeded (Supabase is non-critical)
      return true;
    } catch (e) {
      debugPrint('🔴 saveUserProfile error: $e');
      return false;
    }
  }

  // ── Profile: get ───────────────────────────────────────────
  Future<Map<String, dynamic>?> getUserProfile() async {
    try {
      if (currentUser == null) return null;

      final firebaseUid = currentUser!.uid;

      try {
        return await SupabaseService.instance.getUserProfile(firebaseUid);
      } catch (e) {
        // Fallback to local storage
        debugPrint('🟡 Supabase profile fetch failed, using local: $e');
        final prefs = await SharedPreferences.getInstance();
        final profileJson = prefs.getString('user_profile_$firebaseUid');
        if (profileJson != null) return json.decode(profileJson);
        return null;
      }
    } catch (e) {
      debugPrint('🔴 getUserProfile error: $e');
      return null;
    }
  }

  // ── Profile: mark completed ────────────────────────────────
  Future<void> markProfileCompleted() async {
    try {
      if (currentUser != null) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('profile_completed_${currentUser!.uid}', true);
      }
    } catch (e) {
      // Handle silently
    }
  }

  // ── Private helpers ────────────────────────────────────────
  Future<void> _storeUserForBiometric(String email, String password) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('stored_email', email);
      await prefs.setString('stored_password', password);
    } catch (e) {
      // Handle silently
    }
  }

  Future<bool> _signInWithStoredCredentials() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final email = prefs.getString('stored_email');
      final password = prefs.getString('stored_password');
      if (email != null && password != null) {
        await _auth.signInWithEmailAndPassword(
            email: email, password: password);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<void> _clearStoredCredentials() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await Future.wait([
        prefs.remove('stored_email'),
        prefs.remove('stored_password'),
      ]);
    } catch (e) {
      // Handle silently
    }
  }

  String _handleAuthError(FirebaseAuthException e) {
    switch (e.code) {
      case 'user-not-found':
        return 'No user found with this email.';
      case 'wrong-password':
        return 'Wrong password provided.';
      case 'email-already-in-use':
        return 'An account already exists with this email.';
      case 'weak-password':
        return 'Password is too weak.';
      case 'invalid-email':
        return 'Invalid email format.';
      case 'user-disabled':
        return 'This user account has been disabled.';
      case 'too-many-requests':
        return 'Too many failed attempts. Please try again later.';
      default:
        return 'Authentication failed: ${e.message}';
    }
  }
}
