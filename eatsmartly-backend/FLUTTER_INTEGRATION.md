# Flutter Integration Guide for EatSmartly Backend

## Overview
This guide shows how to integrate your Flutter app with the EatSmartly backend API.

## Setup

### 1. Add HTTP Package to Flutter

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  barcode_scan2: ^4.2.3  # For barcode scanning
```

### 2. Create API Service

```dart
// lib/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class EatSmartlyAPI {
  // Change to your backend URL
  static const String baseUrl = 'http://localhost:8000';
  
  // For production
  // static const String baseUrl = 'https://api.eatsmartly.com';
  
  // Analyze barcode
  Future<FoodAnalysis> analyzeBarcode(String barcode, String userId, {bool detailed = false}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/analyze-barcode'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'barcode': barcode,
        'user_id': userId,
        'detailed': detailed
      }),
    );
    
    if (response.statusCode == 200) {
      return FoodAnalysis.fromJson(json.decode(response.body));
    } else if (response.statusCode == 404) {
      throw Exception('Food not found for barcode: $barcode');
    } else {
      throw Exception('Failed to analyze barcode: ${response.body}');
    }
  }
  
  // Search food by name
  Future<SearchResults> searchFood(String query, String userId, {int limit = 5}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/search'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'query': query,
        'user_id': userId,
        'limit': limit
      }),
    );
    
    if (response.statusCode == 200) {
      return SearchResults.fromJson(json.decode(response.body));
    } else {
      throw Exception('Search failed: ${response.body}');
    }
  }
  
  // Get user profile
  Future<UserProfile> getUserProfile(String userId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/user/$userId/profile'),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return UserProfile.fromJson(data['profile']);
    } else {
      throw Exception('Failed to load profile');
    }
  }
  
  // Update user profile
  Future<void> updateUserProfile(String userId, UserProfile profile) async {
    final response = await http.post(
      Uri.parse('$baseUrl/user/$userId/profile'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(profile.toJson()),
    );
    
    if (response.statusCode != 200) {
      throw Exception('Failed to update profile');
    }
  }
  
  // Health check
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
```

### 3. Create Data Models

```dart
// lib/models/food_analysis.dart
class FoodAnalysis {
  final String barcode;
  final String? foodName;
  final String? brand;
  final String verdict;
  final String riskLevel;
  final double healthScore;
  final List<String> alerts;
  final List<String> warnings;
  final List<String> suggestions;
  final List<Alternative> alternatives;
  final List<Recipe> recipes;
  final List<String> nutritionTips;
  final DetailedNutrition? detailedNutrition;
  final String timestamp;
  
  FoodAnalysis({
    required this.barcode,
    this.foodName,
    this.brand,
    required this.verdict,
    required this.riskLevel,
    required this.healthScore,
    required this.alerts,
    required this.warnings,
    required this.suggestions,
    required this.alternatives,
    required this.recipes,
    required this.nutritionTips,
    this.detailedNutrition,
    required this.timestamp,
  });
  
  factory FoodAnalysis.fromJson(Map<String, dynamic> json) {
    return FoodAnalysis(
      barcode: json['barcode'],
      foodName: json['food_name'],
      brand: json['brand'],
      verdict: json['verdict'],
      riskLevel: json['risk_level'],
      healthScore: (json['health_score'] as num).toDouble(),
      alerts: List<String>.from(json['alerts']),
      warnings: List<String>.from(json['warnings']),
      suggestions: List<String>.from(json['suggestions']),
      alternatives: (json['alternatives'] as List)
          .map((a) => Alternative.fromJson(a))
          .toList(),
      recipes: (json['recipes'] as List)
          .map((r) => Recipe.fromJson(r))
          .toList(),
      nutritionTips: List<String>.from(json['nutrition_tips']),
      detailedNutrition: json['detailed_nutrition'] != null
          ? DetailedNutrition.fromJson(json['detailed_nutrition'])
          : null,
      timestamp: json['timestamp'],
    );
  }
}

class Alternative {
  final String name;
  final String reason;
  
  Alternative({required this.name, required this.reason});
  
  factory Alternative.fromJson(Map<String, dynamic> json) {
    return Alternative(
      name: json['name'],
      reason: json['reason'],
    );
  }
}

class Recipe {
  final String title;
  final String url;
  final String source;
  
  Recipe({required this.title, required this.url, required this.source});
  
  factory Recipe.fromJson(Map<String, dynamic> json) {
    return Recipe(
      title: json['title'],
      url: json['url'],
      source: json['source'],
    );
  }
}

class DetailedNutrition {
  final double? servingSize;
  final String? servingUnit;
  final double? calories;
  final double? proteinG;
  final double? carbsG;
  final double? fatG;
  final double? saturatedFatG;
  final double? sodiumMg;
  final double? sugarG;
  final double? fiberG;
  final String? ingredients;
  final List<String>? allergens;
  
  DetailedNutrition({
    this.servingSize,
    this.servingUnit,
    this.calories,
    this.proteinG,
    this.carbsG,
    this.fatG,
    this.saturatedFatG,
    this.sodiumMg,
    this.sugarG,
    this.fiberG,
    this.ingredients,
    this.allergens,
  });
  
  factory DetailedNutrition.fromJson(Map<String, dynamic> json) {
    return DetailedNutrition(
      servingSize: json['serving_size']?.toDouble(),
      servingUnit: json['serving_unit'],
      calories: json['calories']?.toDouble(),
      proteinG: json['protein_g']?.toDouble(),
      carbsG: json['carbs_g']?.toDouble(),
      fatG: json['fat_g']?.toDouble(),
      saturatedFatG: json['saturated_fat_g']?.toDouble(),
      sodiumMg: json['sodium_mg']?.toDouble(),
      sugarG: json['sugar_g']?.toDouble(),
      fiberG: json['fiber_g']?.toDouble(),
      ingredients: json['ingredients'],
      allergens: json['allergens'] != null 
          ? List<String>.from(json['allergens']) 
          : null,
    );
  }
}

class UserProfile {
  final int? age;
  final String? gender;
  final double? heightCm;
  final double? weightKg;
  final String? activityLevel;
  final String? healthGoal;
  final List<String> allergies;
  final List<String> healthConditions;
  final List<String> dietaryRestrictions;
  
  UserProfile({
    this.age,
    this.gender,
    this.heightCm,
    this.weightKg,
    this.activityLevel,
    this.healthGoal,
    this.allergies = const [],
    this.healthConditions = const [],
    this.dietaryRestrictions = const [],
  });
  
  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      age: json['age'],
      gender: json['gender'],
      heightCm: json['height_cm']?.toDouble(),
      weightKg: json['weight_kg']?.toDouble(),
      activityLevel: json['activity_level'],
      healthGoal: json['health_goal'],
      allergies: List<String>.from(json['allergies'] ?? []),
      healthConditions: List<String>.from(json['health_conditions'] ?? []),
      dietaryRestrictions: List<String>.from(json['dietary_restrictions'] ?? []),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'age': age,
      'gender': gender,
      'height_cm': heightCm,
      'weight_kg': weightKg,
      'activity_level': activityLevel,
      'health_goal': healthGoal,
      'allergies': allergies,
      'health_conditions': healthConditions,
      'dietary_restrictions': dietaryRestrictions,
    };
  }
}

class SearchResults {
  final String query;
  final int count;
  final List<Map<String, dynamic>> results;
  
  SearchResults({
    required this.query,
    required this.count,
    required this.results,
  });
  
  factory SearchResults.fromJson(Map<String, dynamic> json) {
    return SearchResults(
      query: json['query'],
      count: json['count'],
      results: List<Map<String, dynamic>>.from(json['results']),
    );
  }
}
```

### 4. Example Barcode Scanner Screen

```dart
// lib/screens/barcode_scanner_screen.dart
import 'package:flutter/material.dart';
import 'package:barcode_scan2/barcode_scan2.dart';
import '../services/api_service.dart';
import '../models/food_analysis.dart';

class BarcodeScannerScreen extends StatefulWidget {
  @override
  _BarcodeScannerScreenState createState() => _BarcodeScannerScreenState();
}

class _BarcodeScannerScreenState extends State<BarcodeScannerScreen> {
  final EatSmartlyAPI api = EatSmartlyAPI();
  String userId = 'test_user'; // Replace with actual user ID
  bool isLoading = false;
  FoodAnalysis? result;
  String? error;
  
  Future<void> scanBarcode() async {
    try {
      var scanResult = await BarcodeScanner.scan();
      
      if (scanResult.rawContent.isNotEmpty) {
        setState(() {
          isLoading = true;
          error = null;
        });
        
        final analysis = await api.analyzeBarcode(
          scanResult.rawContent,
          userId,
          detailed: true
        );
        
        setState(() {
          result = analysis;
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        error = e.toString();
        isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('EatSmartly Scanner'),
      ),
      body: Center(
        child: isLoading
            ? CircularProgressIndicator()
            : result != null
                ? _buildResultView()
                : _buildScanPrompt(),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: scanBarcode,
        child: Icon(Icons.camera_alt),
        tooltip: 'Scan Barcode',
      ),
    );
  }
  
  Widget _buildScanPrompt() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.qr_code_scanner, size: 100, color: Colors.grey),
        SizedBox(height: 20),
        Text('Tap the camera button to scan a barcode'),
        if (error != null) ...[
          SizedBox(height: 20),
          Text(error!, style: TextStyle(color: Colors.red)),
        ],
      ],
    );
  }
  
  Widget _buildResultView() {
    if (result == null) return Container();
    
    Color verdictColor = result!.verdict == 'safe'
        ? Colors.green
        : result!.verdict == 'caution'
            ? Colors.orange
            : Colors.red;
    
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Food name and brand
          Text(
            result!.foodName ?? 'Unknown Food',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          if (result!.brand != null)
            Text(result!.brand!, style: TextStyle(fontSize: 16, color: Colors.grey)),
          
          SizedBox(height: 20),
          
          // Verdict card
          Card(
            color: verdictColor.withOpacity(0.2),
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                children: [
                  Icon(
                    result!.verdict == 'safe' ? Icons.check_circle : Icons.warning,
                    color: verdictColor,
                    size: 50,
                  ),
                  SizedBox(height: 10),
                  Text(
                    result!.verdict.toUpperCase(),
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: verdictColor,
                    ),
                  ),
                  Text('Health Score: ${result!.healthScore.toStringAsFixed(1)}/100'),
                ],
              ),
            ),
          ),
          
          // Alerts
          if (result!.alerts.isNotEmpty) ...[
            SizedBox(height: 20),
            Text('⚠️ Alerts', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ...result!.alerts.map((alert) => ListTile(
              leading: Icon(Icons.error, color: Colors.red),
              title: Text(alert),
            )),
          ],
          
          // Suggestions
          if (result!.suggestions.isNotEmpty) ...[
            SizedBox(height: 20),
            Text('💡 Suggestions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ...result!.suggestions.map((suggestion) => ListTile(
              title: Text(suggestion),
            )),
          ],
          
          // Alternatives
          if (result!.alternatives.isNotEmpty) ...[
            SizedBox(height: 20),
            Text('🔄 Healthier Alternatives', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ...result!.alternatives.map((alt) => ListTile(
              title: Text(alt.name),
              subtitle: Text(alt.reason),
            )),
          ],
          
          // Scan another button
          SizedBox(height: 20),
          ElevatedButton(
            onPressed: () => setState(() => result = null),
            child: Text('Scan Another'),
          ),
        ],
      ),
    );
  }
}
```

## Testing Backend Connection

### Test from Flutter

```dart
// Test connection
final api = EatSmartlyAPI();
final isHealthy = await api.checkHealth();
print('Backend health: $isHealthy');
```

### Android Network Configuration

Add to `android/app/src/main/AndroidManifest.xml`:

```xml
<application
    android:usesCleartextTraffic="true">
    <!-- other config -->
</application>
```

For localhost on Android emulator, use `http://10.0.2.2:8000` instead of `http://localhost:8000`.

## Production Deployment

When deploying to production:

1. Change `baseUrl` to your production URL
2. Add authentication tokens
3. Enable HTTPS
4. Remove `usesCleartextTraffic` flag

---

**Ready to integrate! 🚀**
