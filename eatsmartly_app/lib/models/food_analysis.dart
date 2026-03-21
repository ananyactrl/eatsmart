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
  final IngredientIntelligence? ingredientIntelligence;
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
    this.ingredientIntelligence,
    required this.timestamp,
  });

  factory FoodAnalysis.fromJson(Map<String, dynamic> json) {
    return FoodAnalysis(
      barcode: json['barcode'] ?? '',
      foodName: json['food_name'],
      brand: json['brand'],
      verdict: json['verdict'] ?? 'unknown',
      riskLevel: json['risk_level'] ?? 'low',
      healthScore: (json['health_score'] ?? 0).toDouble(),
      alerts: List<String>.from(json['alerts'] ?? []),
      warnings: List<String>.from(json['warnings'] ?? []),
      suggestions: List<String>.from(json['suggestions'] ?? []),
      alternatives: (json['alternatives'] as List? ?? [])
          .map((a) => Alternative.fromJson(a))
          .toList(),
      recipes: (json['recipes'] as List? ?? [])
          .map((r) => Recipe.fromJson(r))
          .toList(),
      nutritionTips: List<String>.from(json['nutrition_tips'] ?? []),
      detailedNutrition: json['detailed_nutrition'] != null
          ? DetailedNutrition.fromJson(json['detailed_nutrition'])
          : null,
      ingredientIntelligence: json['ingredient_intelligence'] != null
          ? IngredientIntelligence.fromJson(json['ingredient_intelligence'])
          : null,
      timestamp: json['timestamp'] ?? DateTime.now().toIso8601String(),
    );
  }
}

// ---------------------------------------------------------------------------
// Ingredient Intelligence models
// ---------------------------------------------------------------------------

class IngredientIntelligence {
  final String? productName;
  final int totalIngredients;
  final int ingredientsIdentified;
  final int ingredientsUnknown;
  final String overallConcern;
  final double transparencyScore;
  final int sourcesCited;
  final String summary;
  final List<IngredientWarning> warnings;
  final List<DecodedIngredient> decodedIngredients;
  final String disclaimer;

  IngredientIntelligence({
    this.productName,
    required this.totalIngredients,
    required this.ingredientsIdentified,
    required this.ingredientsUnknown,
    required this.overallConcern,
    required this.transparencyScore,
    required this.sourcesCited,
    required this.summary,
    required this.warnings,
    required this.decodedIngredients,
    required this.disclaimer,
  });

  factory IngredientIntelligence.fromJson(Map<String, dynamic> json) {
    return IngredientIntelligence(
      productName: json['product_name'],
      totalIngredients: json['total_ingredients'] ?? 0,
      ingredientsIdentified: json['ingredients_identified'] ?? 0,
      ingredientsUnknown: json['ingredients_unknown'] ?? 0,
      overallConcern: json['overall_concern'] ?? 'none',
      transparencyScore: (json['transparency_score'] ?? 0).toDouble(),
      sourcesCited: json['sources_cited'] ?? 0,
      summary: json['summary'] ?? '',
      warnings: (json['warnings'] as List? ?? [])
          .map((w) => IngredientWarning.fromJson(w))
          .toList(),
      decodedIngredients: (json['decoded_ingredients'] as List? ?? [])
          .map((i) => DecodedIngredient.fromJson(i))
          .toList(),
      disclaimer: json['disclaimer'] ?? '',
    );
  }
}

class IngredientWarning {
  final String ingredient;
  final String concern;

  IngredientWarning({required this.ingredient, required this.concern});

  factory IngredientWarning.fromJson(Map<String, dynamic> json) {
    return IngredientWarning(
      ingredient: json['ingredient'] ?? '',
      concern: json['concern'] ?? '',
    );
  }
}

class DecodedIngredient {
  final String name;
  final int position;
  final bool known;
  final String? category;
  final String? concernLevel;
  final String? concernSummary;
  final List<Map<String, dynamic>> regulatoryStatus;
  final List<String> healthEffects;
  final List<Map<String, dynamic>> sources;
  final String? adi;
  final String? eNumber;
  final String plainExplanation;
  final List<String> subIngredients;

  DecodedIngredient({
    required this.name,
    required this.position,
    required this.known,
    this.category,
    this.concernLevel,
    this.concernSummary,
    this.regulatoryStatus = const [],
    this.healthEffects = const [],
    this.sources = const [],
    this.adi,
    this.eNumber,
    this.plainExplanation = '',
    this.subIngredients = const [],
  });

  factory DecodedIngredient.fromJson(Map<String, dynamic> json) {
    return DecodedIngredient(
      name: json['name'] ?? '',
      position: json['position'] ?? 0,
      known: json['known'] ?? false,
      category: json['category'],
      concernLevel: json['concern_level'],
      concernSummary: json['concern_summary'],
      regulatoryStatus: (json['regulatory_status'] as List? ?? [])
          .map((r) => Map<String, dynamic>.from(r))
          .toList(),
      healthEffects: List<String>.from(json['health_effects'] ?? []),
      sources: (json['sources'] as List? ?? [])
          .map((s) => Map<String, dynamic>.from(s))
          .toList(),
      adi: json['adi'],
      eNumber: json['e_number'],
      plainExplanation: json['plain_explanation'] ?? '',
      subIngredients: List<String>.from(json['sub_ingredients'] ?? []),
    );
  }
}

class Alternative {
  final String name;
  final String reason;

  Alternative({required this.name, required this.reason});

  factory Alternative.fromJson(Map<String, dynamic> json) {
    return Alternative(name: json['name'] ?? '', reason: json['reason'] ?? '');
  }
}

class Recipe {
  final String title;
  final String url;
  final String source;

  Recipe({required this.title, required this.url, required this.source});

  factory Recipe.fromJson(Map<String, dynamic> json) {
    return Recipe(
      title: json['title'] ?? '',
      url: json['url'] ?? '',
      source: json['source'] ?? '',
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
  final int? dataSources;
  final String? dataConfidence;
  final double? dataVariance;

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
    this.dataSources,
    this.dataConfidence,
    this.dataVariance,
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
      dataSources: json['data_sources'],
      dataConfidence: json['data_confidence'],
      dataVariance: json['data_variance']?.toDouble(),
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
      dietaryRestrictions: List<String>.from(
        json['dietary_restrictions'] ?? [],
      ),
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
