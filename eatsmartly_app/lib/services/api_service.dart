import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../models/food_analysis.dart';

class EatSmartlyAPI {
  // IMPORTANT: Change this based on your environment
  // For local testing on physical device: use your PC's IP address (192.168.1.2)
  // For local testing on emulator: use 10.0.2.2
  // For production: use your deployed API URL
  // Backend is running on port 8000 (FastAPI with product search and RAG)
  static const String baseUrl =
      'http://192.168.1.2:8000'; // Use your PC's IP for physical devices

  // Timeout duration - increased for slow API responses
  static const Duration timeout = Duration(seconds: 60);
  static const int maxRetries = 2;

  /// Analyze product by name or ID (no barcode required)
  Future<FoodAnalysis> analyzeProduct(
      {int? productId,
      String? productName,
      required String userId,
      bool detailed = true}) async {
    int retries = 0;

    while (retries <= maxRetries) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/analyze-product'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode({
                'product_id': productId,
                'product_name': productName,
                'user_id': userId,
                'detailed': detailed
              }),
            )
            .timeout(timeout);

        if (response.statusCode == 200) {
          return FoodAnalysis.fromJson(json.decode(response.body));
        } else if (response.statusCode == 404) {
          throw Exception('Product not found in database');
        } else if (response.statusCode >= 500) {
          throw Exception('Server error. Please try again.');
        } else {
          throw Exception('Error: ${response.body}');
        }
      } on TimeoutException {
        retries++;
        if (retries > maxRetries) {
          throw Exception(
              'Connection timeout. Please check your internet connection and ensure the backend server is running.');
        }
        await Future.delayed(const Duration(seconds: 2));
      } on http.ClientException {
        throw Exception(
            'Cannot connect to server. Make sure the backend is running on $baseUrl');
      } catch (e) {
        if (e.toString().contains('SocketException')) {
          throw Exception('No internet connection or server is offline');
        }
        rethrow;
      }
    }
    throw Exception('Failed after $maxRetries retries');
  }

  /// Analyze barcode (legacy method - use analyzeProduct instead)
  Future<FoodAnalysis> analyzeBarcode(
      {required String barcode,
      required String userId,
      bool detailed = true}) async {
    int retries = 0;

    while (retries <= maxRetries) {
      try {
        final response = await http
            .post(
              Uri.parse('$baseUrl/analyze-barcode'),
              headers: {'Content-Type': 'application/json'},
              body: json.encode({
                'barcode': barcode,
                'user_id': userId,
                'detailed': detailed
              }),
            )
            .timeout(timeout);

        if (response.statusCode == 200) {
          return FoodAnalysis.fromJson(json.decode(response.body));
        } else if (response.statusCode == 404) {
          throw Exception('Product not found in database');
        } else if (response.statusCode >= 500) {
          throw Exception('Server error. Please try again.');
        } else {
          throw Exception('Error: ${response.body}');
        }
      } on TimeoutException {
        retries++;
        if (retries > maxRetries) {
          throw Exception(
              'Connection timeout. Please check your internet connection and ensure the backend server is running.');
        }
        await Future.delayed(const Duration(seconds: 2));
      } on http.ClientException {
        throw Exception(
            'Cannot connect to server. Make sure the backend is running on $baseUrl');
      } catch (e) {
        if (e.toString().contains('SocketException')) {
          throw Exception('No internet connection or server is offline');
        }
        rethrow;
      }
    }
    throw Exception('Failed after $maxRetries retries');
  }

  /// Search food by name (LEGACY - use searchProducts instead)
  Future<Map<String, dynamic>> searchFood(String query, String userId,
      {int limit = 5}) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/search'),
            headers: {'Content-Type': 'application/json'},
            body: json
                .encode({'query': query, 'user_id': userId, 'limit': limit}),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Search failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Search products - optimized for showing all available products
  /// Returns products from local database (Amazon, BigBasket, etc) AND main database
  /// Use this for the main search functionality in the app
  Future<Map<String, dynamic>> searchProducts(String query,
      {int limit = 20}) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/search-products'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({'query': query, 'limit': limit}),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Search failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Add a product to the database
  /// Example: {'name': 'Barilla Pasta', 'brand': 'Barilla', 'calories': 131, ...}
  Future<Map<String, dynamic>> addProduct(
      Map<String, dynamic> productData) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/add-product'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode(productData),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to add product: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Get user profile
  Future<UserProfile> getUserProfile(String userId) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/user/$userId/profile'))
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return UserProfile.fromJson(data['profile']);
      } else {
        throw Exception('Failed to load profile');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Update user profile
  Future<void> updateUserProfile(String userId, UserProfile profile) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/user/$userId/profile'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode(profile.toJson()),
          )
          .timeout(timeout);

      if (response.statusCode != 200) {
        throw Exception('Failed to update profile');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Get healthier alternatives for a product
  Future<Map<String, dynamic>> getAlternatives(
      String productName, String userId,
      {String criteria = 'all'}) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/alternatives'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({
              'product_name': productName,
              'user_id': userId,
              'criteria': criteria
            }),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get alternatives: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Health check
  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Generate meal plan based on ingredients and preferences
  Future<Map<String, dynamic>> generateMealPlan({
    required List<String> availableIngredients,
    required Map<String, dynamic> nutritionalGoals,
    List<String>? dietaryRestrictions,
    List<String>? cuisinePreferences,
    required String mealType,
    required int numMeals,
    required int cookingTimeLimit,
  }) async {
    try {
      final requestBody = {
        'available_ingredients': availableIngredients,
        'nutritional_goals': nutritionalGoals,
        'dietary_restrictions': dietaryRestrictions ?? [],
        'cuisine_preferences': cuisinePreferences ?? [],
        'meal_type': mealType,
        'num_meals': numMeals,
        'cooking_time_limit': cookingTimeLimit,
      };

      final response = await http
          .post(
            Uri.parse('$baseUrl/meal-plan'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode(requestBody),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else if (response.statusCode == 400) {
        throw Exception('Invalid request parameters');
      } else {
        throw Exception('Failed to generate meal plan: ${response.body}');
      }
    } catch (e) {
      throw Exception('Meal plan generation error: $e');
    }
  }
}
