import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../models/food_analysis.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'server_discovery.dart';

class EatSmartlyAPI {
  // Default fallback URL - using ngrok for external access
  static const String _defaultBaseUrl =
      'https://fawn-bespoke-unglacially.ngrok-free.dev';

  // Current base URL (can be changed at runtime)
  static String _currentBaseUrl = _defaultBaseUrl;

  // Auto-discovery in progress flag
  static bool _discoveryInProgress = false;

  // Getter for base URL
  static String get baseUrl => _currentBaseUrl;

  // Timeout duration - increased for slow API responses
  static const Duration timeout = Duration(seconds: 60);
  static const int maxRetries = 2;

  // Common headers including ngrok bypass
  static Map<String, String> get headers => {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      };

  /// Initialize API service - loads saved server URL or uses default
  static Future<void> initialize() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedUrl = prefs.getString('server_base_url');
      if (savedUrl != null && savedUrl.isNotEmpty) {
        _currentBaseUrl = savedUrl;
        print('✅ Loaded saved server URL: $_currentBaseUrl');
      } else {
        _currentBaseUrl = _defaultBaseUrl;
        print('ℹ️  Using default server URL: $_currentBaseUrl');
      }
    } catch (e) {
      print('⚠️  Could not load saved URL: $e');
      _currentBaseUrl = _defaultBaseUrl;
    }
  }

  /// Update the base URL and save it
  static Future<void> setBaseUrl(String newUrl) async {
    try {
      _currentBaseUrl = newUrl;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('server_base_url', newUrl);
      print('✅ Server URL updated to: $newUrl');
    } catch (e) {
      print('⚠️  Could not save server URL: $e');
    }
  }

  /// Get the current base URL
  static String getCurrentBaseUrl() => _currentBaseUrl;

  /// Quick set ngrok URL (for development)
  static Future<void> setNgrokUrl(String ngrokUrl) async {
    // Ensure URL has protocol
    String url = ngrokUrl.trim();
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://$url';
    }

    // Remove trailing slash
    if (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }

    await setBaseUrl(url);
    print('✅ Ngrok URL configured: $url');
  }

  /// Test if server is reachable
  static Future<bool> testConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      print('Connection test failed: $e');
      return false;
    }
  }

  /// Automatically try to discover and reconnect to server
  static Future<bool> autoRediscover() async {
    if (_discoveryInProgress) return false;

    _discoveryInProgress = true;
    print('🔍 Connection failed. Attempting auto-discovery...');

    try {
      final foundUrl = await ServerDiscovery.discoverServer();
      if (foundUrl != null) {
        await setBaseUrl(foundUrl);
        print('✅ Auto-discovery successful: $foundUrl');
        _discoveryInProgress = false;
        return true;
      }
    } catch (e) {
      print('⚠️  Auto-discovery failed: $e');
    }

    _discoveryInProgress = false;
    return false;
  }

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
              headers: headers,
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
              headers: headers,
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
            headers: headers,
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
            headers: headers,
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
            headers: headers,
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
            headers: headers,
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
            headers: headers,
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
            headers: headers,
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
      if (e.toString().contains('SocketException') ||
          e.toString().contains('ConnectionRefused')) {
        throw Exception(
            'Cannot connect to server at $baseUrl. Please ensure:\n• Backend server is running\n• Check network connection\n• IP address 192.168.1.2 is correct for your network');
      } else if (e.toString().contains('TimeoutException')) {
        throw Exception(
            'Connection timeout. Server may be overloaded or not responding.');
      } else {
        throw Exception('Meal plan generation error: $e');
      }
    }
  }

  /// Chat with meal planning assistant
  Future<Map<String, dynamic>> mealChat({
    required String message,
    List<Map<String, dynamic>>? history,
  }) async {
    try {
      final requestBody = {
        'message': message,
        'history': history,
      };

      final response = await http
          .post(
            Uri.parse('$baseUrl/meal-chat'),
            headers: headers,
            body: json.encode(requestBody),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Chat failed: ${response.body}');
      }
    } catch (e) {
      if (e.toString().contains('SocketException') ||
          e.toString().contains('ConnectionRefused')) {
        throw Exception(
            'Cannot connect to server. Please check your connection.');
      } else if (e.toString().contains('TimeoutException')) {
        throw Exception('Connection timeout. Please try again.');
      } else {
        throw Exception('Chat error: $e');
      }
    }
  }
}
