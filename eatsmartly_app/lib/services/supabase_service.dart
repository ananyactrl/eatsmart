import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import 'package:flutter/foundation.dart';

class SupabaseService {
  static SupabaseService? _instance;
  static SupabaseService get instance {
    _instance ??= SupabaseService._();
    return _instance!;
  }

  SupabaseService._();

  // Check if Supabase is initialized
  bool get isInitialized {
    try {
      // This will throw if not initialized
      Supabase.instance.client;
      return true;
    } catch (e) {
      return false;
    }
  }

  // Supabase client (only use if initialized)
  SupabaseClient get client {
    if (!isInitialized) {
      throw Exception('Supabase not initialized. Please initialize Supabase first.');
    }
    return Supabase.instance.client;
  }

  // Initialize Supabase
  static Future<void> initialize({
    required String url,
    required String anonKey,
  }) async {
    await Supabase.initialize(
      url: url,
      anonKey: anonKey,
      authOptions: const FlutterAuthClientOptions(
        authFlowType: AuthFlowType.pkce,
      ),
    );
  }

  // ── Enum value normalizers ─────────────────────────────────
  // Maps any app value → valid Supabase enum value (or null to use DB default)

  static const _validHealthGoals = {
    'maintain', 'lose_weight', 'gain_weight', 'build_muscle', 'manage_condition'
  };
  static const _healthGoalMap = {
    'lose_fat': 'lose_weight',
    'gain_muscle': 'build_muscle',
    'bulk': 'gain_weight',
    'recomp': 'maintain',
    'weight_loss': 'lose_weight',
    'weight_gain': 'gain_weight',
    'muscle_gain': 'build_muscle',
  };

  static const _validActivityLevels = {
    'sedentary', 'light', 'moderate', 'active', 'very_active'
  };

  static const _validGenders = {'male', 'female', 'other'};

  static const _validDietaryTypes = {
    'omnivore', 'vegetarian', 'vegan', 'eggetarian', 'pescatarian'
  };

  static const _validCookingSkills = {'beginner', 'intermediate', 'advanced'};

  static String? _mapHealthGoal(String? value) {
    if (value == null) return null;
    if (_validHealthGoals.contains(value)) return value;
    return _healthGoalMap[value] ?? 'maintain';
  }

  static String? _mapEnum(String? value, Set<String> valid, String fallback) {
    if (value == null) return null;
    return valid.contains(value) ? value : fallback;
  }

  // Save user health profile to Supabase (Clean Schema)
  Future<bool> saveUserProfile({
    required String firebaseUserId,
    required String email,
    required Map<String, dynamic> profileData,
  }) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping profile save');
        throw Exception('Supabase not initialized');
      }

      // Map profile data to single user_profiles table using Firebase UID as primary key
      // Keys match HealthProfile.toJson() output (snake_case)
      final supabaseProfileData = {
        'firebase_uid': firebaseUserId,
        'email': email,
        'full_name': profileData['nickname'] ?? profileData['full_name'] ?? email.split('@')[0],
        'age': profileData['age'],
        'gender': _mapEnum(profileData['gender'], _validGenders, 'other'),
        'weight_kg': profileData['weight_kg'],
        'height_cm': profileData['height_cm'],
        'activity_level': _mapEnum(profileData['activity_level'], _validActivityLevels, 'moderate'),
        'health_goal': _mapHealthGoal(profileData['health_goal']),
        'bmr_calories': profileData['bmr_calories'],
        'tdee_calories': profileData['tdee_calories'],
        'target_calories': profileData['target_calories'],
        'target_protein_g': profileData['target_protein_g'],
        'target_carbs_g': profileData['target_carbs_g'],
        'target_fat_g': profileData['target_fat_g'],
        'health_conditions': profileData['health_conditions'] ?? [],
        'allergies': profileData['allergies'] ?? [],
        'dietary_restrictions': profileData['dietary_restrictions'] ?? [],
        'medications': profileData['medications'] ?? [],
        'dietary_type': _mapEnum(profileData['dietary_type'], _validDietaryTypes, 'omnivore'),
        'cuisine_preferences': profileData['cuisine_preferences'] ?? [],
        'cooking_skill': _mapEnum(profileData['cooking_skill'], _validCookingSkills, 'intermediate'),
        'max_cooking_time_minutes': profileData['max_cooking_time_minutes'],
        'budget_per_meal_inr': profileData['budget_per_meal_inr'],
        'household_size': profileData['household_size'],
        'cooking_for_kids': profileData['cooking_for_kids'] ?? false,
        'kitchen_equipment': profileData['kitchen_equipment'] ?? [],
        'profile_completed': true,
        'updated_at': DateTime.now().toIso8601String(),
      };

      // Upsert user profile (insert or update if exists)
      debugPrint('🔵 Upserting profile: $supabaseProfileData');
      await client
          .from('user_profiles')
          .upsert(supabaseProfileData, onConflict: 'firebase_uid');

      debugPrint('🟢 Profile saved to Supabase successfully');
      return true;
    } catch (e) {
      debugPrint('🔴 Error saving user profile to Supabase: $e');
      return false;
    }
  }

  // Get user health profile from Supabase
  Future<Map<String, dynamic>?> getUserProfile(String firebaseUserId) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping profile fetch');
        throw Exception('Supabase not initialized');
      }

      final response = await client
          .from('user_profiles')
          .select('*')
          .eq('firebase_uid', firebaseUserId)
          .maybeSingle();

      if (response != null) {
        // Convert database columns back to profile data format
        return {
          'nickname': response['full_name'],
          'full_name': response['full_name'],
          'age': response['age'],
          'gender': response['gender'],
          'weight_kg': response['weight_kg'],
          'height_cm': response['height_cm'],
          'activity_level': response['activity_level'],
          'health_goal': response['health_goal'],
          'bmr_calories': response['bmr_calories'],
          'tdee_calories': response['tdee_calories'],
          'target_calories': response['target_calories'],
          'target_protein_g': response['target_protein_g'],
          'target_carbs_g': response['target_carbs_g'],
          'target_fat_g': response['target_fat_g'],
          'health_conditions': response['health_conditions'] ?? [],
          'allergies': response['allergies'] ?? [],
          'dietary_restrictions': response['dietary_restrictions'] ?? [],
          'medications': response['medications'] ?? [],
          'dietary_type': response['dietary_type'],
          'cuisine_preferences': response['cuisine_preferences'] ?? [],
          'cooking_skill': response['cooking_skill'],
          'max_cooking_time_minutes': response['max_cooking_time_minutes'],
          'budget_per_meal_inr': response['budget_per_meal_inr'],
          'household_size': response['household_size'],
          'cooking_for_kids': response['cooking_for_kids'] ?? false,
          'kitchen_equipment': response['kitchen_equipment'] ?? [],
        };
      }

      return null;
    } catch (e) {
      debugPrint('🔴 Error fetching user profile from Supabase: $e');
      return null;
    }
  }

  // Update user profile
  Future<bool> updateUserProfile({
    required String firebaseUserId,
    required Map<String, dynamic> profileData,
  }) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping profile update');
        throw Exception('Supabase not initialized');
      }

      // Map profile data to individual columns (keys match HealthProfile.toJson())
      final updateData = {
        'full_name': profileData['full_name'],
        'age': profileData['age'],
        'gender': _mapEnum(profileData['gender'], _validGenders, 'other'),
        'weight_kg': profileData['weight_kg'],
        'height_cm': profileData['height_cm'],
        'activity_level': _mapEnum(profileData['activity_level'], _validActivityLevels, 'moderate'),
        'health_goal': _mapHealthGoal(profileData['health_goal']),
        'bmr_calories': profileData['bmr_calories'],
        'tdee_calories': profileData['tdee_calories'],
        'target_calories': profileData['target_calories'],
        'target_protein_g': profileData['target_protein_g'],
        'target_carbs_g': profileData['target_carbs_g'],
        'target_fat_g': profileData['target_fat_g'],
        'health_conditions': profileData['health_conditions'] ?? [],
        'allergies': profileData['allergies'] ?? [],
        'dietary_restrictions': profileData['dietary_restrictions'] ?? [],
        'medications': profileData['medications'] ?? [],
        'dietary_type': _mapEnum(profileData['dietary_type'], _validDietaryTypes, 'omnivore'),
        'cuisine_preferences': profileData['cuisine_preferences'] ?? [],
        'cooking_skill': _mapEnum(profileData['cooking_skill'], _validCookingSkills, 'intermediate'),
        'max_cooking_time_minutes': profileData['max_cooking_time_minutes'],
        'budget_per_meal_inr': profileData['budget_per_meal_inr'],
        'household_size': profileData['household_size'],
        'cooking_for_kids': profileData['cooking_for_kids'] ?? false,
        'kitchen_equipment': profileData['kitchen_equipment'] ?? [],
        'updated_at': DateTime.now().toIso8601String(),
      };

      await client.from('user_profiles').update(updateData).eq('firebase_uid', firebaseUserId);

      return true;
    } catch (e) {
      debugPrint('🔴 Error updating user profile in Supabase: $e');
      return false;
    }
  }

  // Delete user profile
  Future<bool> deleteUserProfile(String firebaseUserId) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping profile delete');
        throw Exception('Supabase not initialized');
      }

      await client
          .from('user_profiles')
          .delete()
          .eq('firebase_uid', firebaseUserId);

      return true;
    } catch (e) {
      debugPrint('🔴 Error deleting user profile from Supabase: $e');
      return false;
    }
  }

  // Check if user profile exists
  Future<bool> profileExists(String firebaseUserId) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping profile check');
        throw Exception('Supabase not initialized');
      }

      final response = await client
          .from('user_profiles')
          .select('firebase_uid')
          .eq('firebase_uid', firebaseUserId)
          .maybeSingle();

      bool exists = response != null;
      debugPrint('🔵 Supabase profile exists for $firebaseUserId: $exists');
      return exists;
    } catch (e) {
      debugPrint('🔴 Error checking profile existence: $e');
      return false;
    }
  }

  // Save meal history
  Future<bool> saveMealHistory({
    required String firebaseUserId,
    required Map<String, dynamic> mealData,
  }) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping meal history save');
        throw Exception('Supabase not initialized');
      }

      await client.from('user_meal_history').insert({
        'firebase_uid': firebaseUserId,
        'meal_data': mealData,
        'created_at': DateTime.now().toIso8601String(),
      });

      return true;
    } catch (e) {
      debugPrint('🔴 Error saving meal history: $e');
      return false;
    }
  }

  // Get meal history
  Future<List<Map<String, dynamic>>> getMealHistory(
    String firebaseUserId, {
    int limit = 50,
  }) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping meal history fetch');
        throw Exception('Supabase not initialized');
      }

      final response = await client
          .from('user_meal_history')
          .select('meal_data, created_at')
          .eq('firebase_uid', firebaseUserId)
          .order('created_at', ascending: false)
          .limit(limit);

      return List<Map<String, dynamic>>.from(response);
    } catch (e) {
      debugPrint('🔴 Error fetching meal history: $e');
      return [];
    }
  }

  // Save food scan result
  Future<bool> saveFoodScan({
    required String firebaseUserId,
    required Map<String, dynamic> scanData,
  }) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping food scan save');
        throw Exception('Supabase not initialized');
      }

      await client.from('scan_history').insert({
        'firebase_uid': firebaseUserId,
        'scan_data': scanData,
        'created_at': DateTime.now().toIso8601String(),
      });

      return true;
    } catch (e) {
      debugPrint('🔴 Error saving food scan: $e');
      return false;
    }
  }

  // Get food scan history
  Future<List<Map<String, dynamic>>> getFoodScanHistory(
    String firebaseUserId, {
    int limit = 100,
  }) async {
    try {
      if (!isInitialized) {
        debugPrint('🟡 Supabase not initialized, skipping food scan history fetch');
        throw Exception('Supabase not initialized');
      }

      final response = await client
          .from('scan_history')
          .select('scan_data, created_at')
          .eq('firebase_uid', firebaseUserId)
          .order('created_at', ascending: false)
          .limit(limit);

      return List<Map<String, dynamic>>.from(response);
    } catch (e) {
      debugPrint('🔴 Error fetching food scan history: $e');
      return [];
    }
  }

  // No need for separate user sync - Firebase UID is used directly as primary key
  Future<void> syncFirebaseUser(firebase_auth.User firebaseUser) async {
    // Not needed anymore - Firebase UID is used directly
    debugPrint('🟢 Using Firebase UID directly - no sync needed');
  }
}