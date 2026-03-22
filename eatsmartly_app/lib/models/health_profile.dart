class HealthProfile {
  // Layer 0: Identity
  String? nickname; // What should we call you?

  // Layer 1: Body Context
  int? age;
  String? gender;
  double? weightKg;
  double? heightCm;
  String? activityLevel;
  String? healthGoal;

  // Calculated values
  double? bmrCalories;
  double? tdeeCalories;
  double? targetCalories;
  double? targetProteinG;
  double? targetCarbsG;
  double? targetFatG;

  // Layer 2: Health Context
  List<String> healthConditions = [];
  List<String> allergies = [];
  List<String> dietaryRestrictions = [];
  List<String> medications = [];

  // Layer 3: Life Context
  String? dietaryType;
  List<String> cuisinePreferences = [];
  String? cookingSkill;
  int? maxCookingTimeMinutes;
  int? budgetPerMealInr;
  int? householdSize;
  bool cookingForKids = false;
  List<String> kitchenEquipment = [];

  // Profile metadata
  bool profileCompleted = false;

  HealthProfile();

  // BMR calculation using Mifflin-St Jeor equation
  double? calculateBMR() {
    if (age == null || gender == null || weightKg == null || heightCm == null) {
      return null;
    }

    double bmr;
    if (gender == 'male') {
      bmr = (10 * weightKg!) + (6.25 * heightCm!) - (5 * age!) + 5;
    } else {
      bmr = (10 * weightKg!) + (6.25 * heightCm!) - (5 * age!) - 161;
    }

    bmrCalories = bmr;
    return bmr;
  }

  // TDEE calculation based on activity level
  double? calculateTDEE() {
    double? bmr = calculateBMR();
    if (bmr == null || activityLevel == null) return null;

    double multiplier;
    switch (activityLevel) {
      case 'sedentary':
        multiplier = 1.2;
        break;
      case 'light':
        multiplier = 1.375;
        break;
      case 'moderate':
        multiplier = 1.55;
        break;
      case 'active':
        multiplier = 1.725;
        break;
      case 'very_active':
        multiplier = 1.9;
        break;
      default:
        multiplier = 1.55;
    }

    tdeeCalories = bmr * multiplier;
    return tdeeCalories;
  }

  // Target calories based on health goal
  double? calculateTargetCalories() {
    double? tdee = calculateTDEE();
    if (tdee == null || healthGoal == null) return null;

    double adjustedCalories;
    switch (healthGoal) {
      case 'lose_weight':
      case 'lose_fat':
        adjustedCalories = tdee - 300;
        break;
      case 'build_muscle':
      case 'gain_muscle':
        adjustedCalories = tdee + 200;
        break;
      case 'gain_weight':
      case 'bulk':
        adjustedCalories = tdee + 400;
        break;
      default: // maintain, recomp, manage_condition
        adjustedCalories = tdee;
    }

    targetCalories = adjustedCalories;

    // Calculate macros
    calculateMacros();

    return targetCalories;
  }

  // Calculate target macronutrients
  void calculateMacros() {
    if (targetCalories == null || weightKg == null || healthGoal == null) return;

    // Protein calculation (priority nutrient)
    double proteinMultiplier;
    switch (healthGoal) {
      case 'lose_weight':
      case 'lose_fat':
        proteinMultiplier = 2.2;
        break;
      case 'build_muscle':
      case 'gain_muscle':
        proteinMultiplier = 2.0;
        break;
      case 'gain_weight':
      case 'bulk':
        proteinMultiplier = 1.8;
        break;
      default:
        proteinMultiplier = 1.6;
    }

    targetProteinG = weightKg! * proteinMultiplier;

    // Fat: 25% of calories
    targetFatG = targetCalories! * 0.25 / 9;

    // Carbs: Fill remaining calories
    double proteinCalories = targetProteinG! * 4;
    double fatCalories = targetFatG! * 9;
    targetCarbsG = (targetCalories! - proteinCalories - fatCalories) / 4;
  }

  Map<String, dynamic> toJson() {
    return {
      'nickname': nickname,
      'age': age,
      'gender': gender,
      'weight_kg': weightKg,
      'height_cm': heightCm,
      'activity_level': activityLevel,
      'health_goal': healthGoal,
      'bmr_calories': bmrCalories,
      'tdee_calories': tdeeCalories,
      'target_calories': targetCalories,
      'target_protein_g': targetProteinG,
      'target_carbs_g': targetCarbsG,
      'target_fat_g': targetFatG,
      'health_conditions': healthConditions,
      'allergies': allergies,
      'dietary_restrictions': dietaryRestrictions,
      'medications': medications,
      'dietary_type': dietaryType,
      'cuisine_preferences': cuisinePreferences,
      'cooking_skill': cookingSkill,
      'max_cooking_time_minutes': maxCookingTimeMinutes,
      'budget_per_meal_inr': budgetPerMealInr,
      'household_size': householdSize,
      'cooking_for_kids': cookingForKids,
      'kitchen_equipment': kitchenEquipment,
      'profile_completed': profileCompleted,
    };
  }

  factory HealthProfile.fromJson(Map<String, dynamic> json) {
    final profile = HealthProfile();
    profile.nickname = json['nickname'];
    profile.age = json['age'];
    profile.gender = json['gender'];
    profile.weightKg = json['weight_kg']?.toDouble();
    profile.heightCm = json['height_cm']?.toDouble();
    profile.activityLevel = json['activity_level'];
    profile.healthGoal = json['health_goal'];
    profile.bmrCalories = json['bmr_calories']?.toDouble();
    profile.tdeeCalories = json['tdee_calories']?.toDouble();
    profile.targetCalories = json['target_calories']?.toDouble();
    profile.targetProteinG = json['target_protein_g']?.toDouble();
    profile.targetCarbsG = json['target_carbs_g']?.toDouble();
    profile.targetFatG = json['target_fat_g']?.toDouble();
    profile.healthConditions = List<String>.from(json['health_conditions'] ?? []);
    profile.allergies = List<String>.from(json['allergies'] ?? []);
    profile.dietaryRestrictions = List<String>.from(json['dietary_restrictions'] ?? []);
    profile.medications = List<String>.from(json['medications'] ?? []);
    profile.dietaryType = json['dietary_type'];
    profile.cuisinePreferences = List<String>.from(json['cuisine_preferences'] ?? []);
    profile.cookingSkill = json['cooking_skill'];
    profile.maxCookingTimeMinutes = json['max_cooking_time_minutes'];
    profile.budgetPerMealInr = json['budget_per_meal_inr'];
    profile.householdSize = json['household_size'];
    profile.cookingForKids = json['cooking_for_kids'] ?? false;
    profile.kitchenEquipment = List<String>.from(json['kitchen_equipment'] ?? []);
    profile.profileCompleted = json['profile_completed'] ?? false;
    return profile;
  }
}