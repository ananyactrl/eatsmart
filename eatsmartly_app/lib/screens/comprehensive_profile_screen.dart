import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/health_profile.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../theme.dart';
import 'home_screen.dart';

class ComprehensiveProfileScreen extends StatefulWidget {
  const ComprehensiveProfileScreen({Key? key}) : super(key: key);

  @override
  State<ComprehensiveProfileScreen> createState() =>
      _ComprehensiveProfileScreenState();
}

class _ComprehensiveProfileScreenState extends State<ComprehensiveProfileScreen>
    with TickerProviderStateMixin {
  late PageController _pageController;
  late AnimationController _animationController;
  int _currentStep = 0;
  final int _totalSteps = 8;

  final HealthProfile _profile = HealthProfile();
  bool _isLoading = false;

  // Form controllers
  final TextEditingController _nicknameController = TextEditingController();
  final TextEditingController _ageController = TextEditingController();
  final TextEditingController _weightController = TextEditingController();
  final TextEditingController _heightController = TextEditingController();
  final TextEditingController _budgetController = TextEditingController();
  final TextEditingController _cookingTimeController = TextEditingController();
  final TextEditingController _householdController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _nicknameController.addListener(() {
      setState(() => _profile.nickname = _nicknameController.text.trim());
    });
    // Listen to text field changes for real-time calculations
    _ageController.addListener(_updateCalculations);
    _weightController.addListener(_updateCalculations);
    _heightController.addListener(_updateCalculations);
  }

  void _updateCalculations() {
    if (_ageController.text.isNotEmpty &&
        _weightController.text.isNotEmpty &&
        _heightController.text.isNotEmpty &&
        _profile.gender != null) {
      setState(() {
        _profile.age = int.tryParse(_ageController.text);
        _profile.weightKg = double.tryParse(_weightController.text);
        _profile.heightCm = double.tryParse(_heightController.text);
        _profile.calculateTargetCalories();
      });
    }
  }

  void _nextStep() {
    if (_currentStep < _totalSteps - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _saveProfile();
    }
  }

  void _previousStep() {
    if (_currentStep > 0) {
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _isLoading = true);

    try {
      _profile.profileCompleted = true;

      final profileData = _profile.toJson();

      final authService = Provider.of<AuthService>(context, listen: false);
      final success = await authService.saveUserProfile(profileData);

      if (success && mounted) {
        // Also save to backend API for meal planning (non-critical)
        try {
          final api = EatSmartlyAPI();
          await api.saveUserProfile(profileData);
        } catch (e) {
          debugPrint('Backend API save failed (non-critical): $e');
        }

        // Navigate directly to HomeScreen
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const HomeScreen()),
          (route) => false,
        );
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Error saving profile. Please try again.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // Progress bar
            _buildProgressBar(),

            // Main content
            Expanded(
              child: PageView(
                controller: _pageController,
                onPageChanged: (index) {
                  setState(() => _currentStep = index);
                  _animationController.forward(from: 0);
                },
                children: [
                  _buildStep0Nickname(),
                  _buildStep1Body(),
                  _buildStep2Goal(),
                  _buildStep3Health(),
                  _buildStep4Diet(),
                  _buildStep5Cooking(),
                  _buildStep6Household(),
                  _buildStep7Summary(),
                ],
              ),
            ),

            // Navigation buttons
            _buildNavigationButtons(),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressBar() {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Step ${_currentStep + 1} of $_totalSteps',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: AppColors.muted),
              ),
              Text(
                '${((_currentStep + 1) / _totalSteps * 100).round()}%',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.rose),
              ),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: (_currentStep + 1) / _totalSteps,
            backgroundColor: AppColors.blush,
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.rose),
            borderRadius: BorderRadius.circular(4),
          ),
        ],
      ),
    );
  }

  // Step 0: Nickname
  Widget _buildStep0Nickname() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 40),
          Text(
            '👋 Hey there!',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'What should we call you?',
            style: GoogleFonts.inter(fontSize: 16, color: Colors.grey[600]),
          ),
          const SizedBox(height: 40),
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
            child: TextField(
              controller: _nicknameController,
              textCapitalization: TextCapitalization.words,
              style: GoogleFonts.inter(fontSize: 18),
              decoration: InputDecoration(
                border: InputBorder.none,
                hintText: 'Your name or nickname',
                hintStyle: GoogleFonts.inter(color: Colors.grey[400]),
                prefixIcon: const Icon(Icons.person_outline, color: AppColors.rose),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'This is how the app will greet you 😊',
            style: GoogleFonts.inter(fontSize: 13, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  // Step 1: Body Context
  Widget _buildStep1Body() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            '🏃‍♂️ Your Body',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Help us calculate your daily calorie needs',
            style: GoogleFonts.inter(
              fontSize: 16,
              color: Colors.grey[600],
            ),
          ),

          const SizedBox(height: 32),

          // Age and Gender row
          Row(
            children: [
              Expanded(
                child: _buildTextField(
                  controller: _ageController,
                  label: 'Age',
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildDropdown<String>(
                  value: _profile.gender,
                  label: 'Gender',
                  items: const [
                    DropdownMenuItem(value: 'male', child: Text('Male')),
                    DropdownMenuItem(value: 'female', child: Text('Female')),
                    DropdownMenuItem(value: 'other', child: Text('Other')),
                  ],
                  onChanged: (value) {
                    setState(() => _profile.gender = value);
                    _updateCalculations();
                  },
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Weight and Height row
          Row(
            children: [
              Expanded(
                child: _buildTextField(
                  controller: _weightController,
                  label: 'Weight (kg)',
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildTextField(
                  controller: _heightController,
                  label: 'Height (cm)',
                  keyboardType: TextInputType.number,
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Activity Level
          const Text(
            'How active are you?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          _buildActivityLevelOptions(),

          // Live calculations display
          if (_profile.tdeeCalories != null) ...[
            const SizedBox(height: 24),
            _buildCalorieDisplay(),
          ],
        ],
      ),
    );
  }

  Widget _buildActivityLevelOptions() {
    final options = [
      {
        'value': 'sedentary',
        'label': 'Sedentary',
        'desc': 'Little/no exercise, desk job'
      },
      {
        'value': 'light',
        'label': 'Light',
        'desc': 'Light exercise 1-3 days/week'
      },
      {
        'value': 'moderate',
        'label': 'Moderate',
        'desc': 'Moderate exercise 3-5 days/week'
      },
      {
        'value': 'active',
        'label': 'Active',
        'desc': 'Heavy exercise 6-7 days/week'
      },
      {
        'value': 'very_active',
        'label': 'Very Active',
        'desc': 'Very heavy exercise + physical job'
      },
    ];

    return Column(
      children: options
          .map(
            (option) => _buildSelectableCard(
              title: option['label']!,
              subtitle: option['desc']!,
              isSelected: _profile.activityLevel == option['value'],
              onTap: () {
                setState(() {
                  _profile.activityLevel = option['value'];
                  _updateCalculations();
                });
              },
            ),
          )
          .toList(),
    );
  }

  Widget _buildCalorieDisplay() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.blush,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.coral.withOpacity(0.4)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Your Daily Calorie Need:'),
              Text(
                '${_profile.tdeeCalories?.toInt()} kcal',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.rose),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'BMR: ${_profile.bmrCalories?.toInt()} kcal × Activity = ${_profile.tdeeCalories?.toInt()} kcal',
            style: const TextStyle(fontSize: 12, color: AppColors.muted),
          ),
        ],
      ),
    );
  }

  // Step 2: Health Goal
  Widget _buildStep2Goal() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            '🎯 Your Goal',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'What do you want to achieve?',
            style: GoogleFonts.inter(fontSize: 16, color: Colors.grey[600]),
          ),

          const SizedBox(height: 32),

          _buildGoalOptions(),

          // Live macro display
          if (_profile.targetCalories != null) ...[
            const SizedBox(height: 24),
            _buildMacroDisplay(),
          ],
        ],
      ),
    );
  }

  Widget _buildGoalOptions() {
    final goals = [
      {
        'value': 'maintain',
        'label': 'Maintain Weight',
        'desc': 'Keep current weight, improve health'
      },
      {
        'value': 'lose_weight',
        'label': 'Lose Fat',
        'desc': '300 cal deficit, high protein'
      },
      {
        'value': 'build_muscle',
        'label': 'Build Muscle',
        'desc': '200 cal surplus, strength focused'
      },
      {
        'value': 'gain_weight',
        'label': 'Gain Weight',
        'desc': '400 cal surplus, overall mass'
      },
      {
        'value': 'manage_condition',
        'label': 'Manage Health Condition',
        'desc': 'Tailored for specific health needs'
      },
    ];

    return Column(
      children: goals
          .map(
            (goal) => _buildSelectableCard(
              title: goal['label']!,
              subtitle: goal['desc']!,
              isSelected: _profile.healthGoal == goal['value'],
              onTap: () {
                setState(() {
                  _profile.healthGoal = goal['value'];
                  _profile.calculateTargetCalories();
                });
              },
            ),
          )
          .toList(),
    );
  }

  Widget _buildMacroDisplay() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.blush,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.coral.withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Daily Targets:', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.dark)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildMacroStat(
                  'Calories', '${_profile.targetCalories?.toInt()}', 'kcal'),
              _buildMacroStat(
                  'Protein', '${_profile.targetProteinG?.toInt()}', 'g'),
              _buildMacroStat(
                  'Carbs', '${_profile.targetCarbsG?.toInt()}', 'g'),
              _buildMacroStat('Fat', '${_profile.targetFatG?.toInt()}', 'g'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMacroStat(String label, String value, String unit) {
    return Column(
      children: [
        Text(value,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        Text('$unit $label',
            style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }

  // Step 3: Health Conditions
  Widget _buildStep3Health() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            '🏥 Health Context',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'This helps us flag ingredients that could affect your conditions',
            style: GoogleFonts.inter(fontSize: 16, color: Colors.grey[600]),
          ),

          const SizedBox(height: 32),

          // Health Conditions
          const Text(
            'Do you have any of these conditions?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          _buildHealthConditionsOptions(),

          const SizedBox(height: 24),

          // Allergies
          const Text(
            'Any food allergies?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          _buildAllergyOptions(),
        ],
      ),
    );
  }

  Widget _buildHealthConditionsOptions() {
    final conditions = [
      'diabetes',
      'pcos',
      'hypertension',
      'hypothyroid',
      'hyperthyroid',
      'ibs',
      'ckd',
      'gerd',
      'celiac',
      'heart_disease',
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: conditions
          .map(
            (condition) => FilterChip(
              label: Text(condition.toUpperCase()),
              selected: _profile.healthConditions.contains(condition),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _profile.healthConditions.add(condition);
                  } else {
                    _profile.healthConditions.remove(condition);
                  }
                });
              },
              selectedColor: AppColors.blush,
            ),
          )
          .toList(),
    );
  }

  Widget _buildAllergyOptions() {
    final allergies = [
      'dairy',
      'nuts',
      'peanuts',
      'shellfish',
      'fish',
      'eggs',
      'soy',
      'gluten',
      'sesame',
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: allergies
          .map(
            (allergy) => FilterChip(
              label: Text(allergy.capitalize()),
              selected: _profile.allergies.contains(allergy),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _profile.allergies.add(allergy);
                  } else {
                    _profile.allergies.remove(allergy);
                  }
                });
              },
              selectedColor: AppColors.blush,
            ),
          )
          .toList(),
    );
  }

  // Step 4: Diet & Allergies
  Widget _buildStep4Diet() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            '🥗 Diet Type',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'What can you eat?',
            style: GoogleFonts.inter(fontSize: 16, color: Colors.grey[600]),
          ),
          const SizedBox(height: 32),
          _buildDietTypeOptions(),
          const SizedBox(height: 24),
          const Text(
            'Favorite cuisines?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          _buildCuisineOptions(),
        ],
      ),
    );
  }

  Widget _buildDietTypeOptions() {
    final diets = [
      {'value': 'omnivore', 'label': 'Omnivore', 'desc': 'Eat everything'},
      {
        'value': 'vegetarian',
        'label': 'Vegetarian',
        'desc': 'No meat, fish, poultry'
      },
      {'value': 'vegan', 'label': 'Vegan', 'desc': 'No animal products'},
      {
        'value': 'eggetarian',
        'label': 'Eggetarian',
        'desc': 'Vegetarian + eggs'
      },
      {
        'value': 'pescatarian',
        'label': 'Pescatarian',
        'desc': 'Vegetarian + fish'
      },
    ];

    return Column(
      children: diets
          .map(
            (diet) => _buildSelectableCard(
              title: diet['label']!,
              subtitle: diet['desc']!,
              isSelected: _profile.dietaryType == diet['value'],
              onTap: () {
                setState(() => _profile.dietaryType = diet['value']);
              },
            ),
          )
          .toList(),
    );
  }

  Widget _buildCuisineOptions() {
    final cuisines = [
      'south_indian',
      'north_indian',
      'italian',
      'chinese',
      'continental',
      'mexican',
      'thai',
      'japanese',
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: cuisines
          .map(
            (cuisine) => FilterChip(
              label: Text(cuisine.replaceAll('_', ' ').capitalize()),
              selected: _profile.cuisinePreferences.contains(cuisine),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _profile.cuisinePreferences.add(cuisine);
                  } else {
                    _profile.cuisinePreferences.remove(cuisine);
                  }
                });
              },
              selectedColor: AppColors.blush,
            ),
          )
          .toList(),
    );
  }

  // Step 5: Cooking Life
  Widget _buildStep5Cooking() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            '🍳 Cooking Life',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Your constraints shape what we recommend',
            style: GoogleFonts.inter(fontSize: 16, color: Colors.grey[600]),
          ),

          const SizedBox(height: 32),

          // Cooking skill
          const Text(
            'Cooking skill level?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          _buildCookingSkillOptions(),

          const SizedBox(height: 24),

          // Time and budget row
          Row(
            children: [
              Expanded(
                child: _buildTextField(
                  controller: _budgetController,
                  label: 'Budget per meal (₹)',
                  keyboardType: TextInputType.number,
                  onChanged: (value) {
                    _profile.budgetPerMealInr = int.tryParse(value);
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildTextField(
                  controller: _cookingTimeController,
                  label: 'Max cooking time (min)',
                  keyboardType: TextInputType.number,
                  onChanged: (value) {
                    _profile.maxCookingTimeMinutes = int.tryParse(value);
                  },
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Kitchen equipment
          const Text(
            'Kitchen equipment you have?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          _buildKitchenEquipmentOptions(),
        ],
      ),
    );
  }

  Widget _buildCookingSkillOptions() {
    final skills = [
      {
        'value': 'beginner',
        'label': 'Beginner',
        'desc': 'Basic cooking skills'
      },
      {
        'value': 'intermediate',
        'label': 'Intermediate',
        'desc': 'Can follow recipes well'
      },
      {
        'value': 'advanced',
        'label': 'Advanced',
        'desc': 'Confident with complex dishes'
      },
    ];

    return Column(
      children: skills
          .map(
            (skill) => _buildSelectableCard(
              title: skill['label']!,
              subtitle: skill['desc']!,
              isSelected: _profile.cookingSkill == skill['value'],
              onTap: () {
                setState(() => _profile.cookingSkill = skill['value']);
              },
            ),
          )
          .toList(),
    );
  }

  Widget _buildKitchenEquipmentOptions() {
    final equipment = [
      'oven',
      'microwave',
      'pressure_cooker',
      'air_fryer',
      'food_processor',
      'blender',
      'steamer',
      'grill',
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: equipment
          .map(
            (item) => FilterChip(
              label: Text(item.replaceAll('_', ' ').capitalize()),
              selected: _profile.kitchenEquipment.contains(item),
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _profile.kitchenEquipment.add(item);
                  } else {
                    _profile.kitchenEquipment.remove(item);
                  }
                });
              },
              selectedColor: AppColors.blush,
            ),
          )
          .toList(),
    );
  }

  // Step 6: Household
  Widget _buildStep6Household() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            '👨‍👩‍👧‍👦 Household',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Who are you cooking for?',
            style: GoogleFonts.inter(fontSize: 16, color: Colors.grey[600]),
          ),
          const SizedBox(height: 32),
          _buildTextField(
            controller: _householdController,
            label: 'Household size (number of people)',
            keyboardType: TextInputType.number,
            onChanged: (value) {
              _profile.householdSize = int.tryParse(value);
            },
          ),
          const SizedBox(height: 24),
          SwitchListTile(
            title: const Text('Cooking for kids?'),
            subtitle: const Text('Helps us suggest kid-friendly ingredients'),
            value: _profile.cookingForKids,
            onChanged: (value) {
              setState(() => _profile.cookingForKids = value);
            },
            activeColor: AppColors.rose,
          ),
        ],
      ),
    );
  }

  // Step 7: Summary
  Widget _buildStep7Summary() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            '✅ All Set!',
            style: GoogleFonts.youngSerif(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: AppColors.rose,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Your personalized nutrition profile is ready',
            style: GoogleFonts.inter(fontSize: 16, color: Colors.grey[600]),
          ),

          const SizedBox(height: 32),

          // Summary cards
          _buildSummaryCard('Daily Targets', [
            'Calories: ${_profile.targetCalories?.toInt()} kcal',
            'Protein: ${_profile.targetProteinG?.toInt()}g',
            'Goal: ${_profile.healthGoal?.capitalize()}',
          ]),

          _buildSummaryCard('Health Context', [
            if (_profile.healthConditions.isNotEmpty)
              'Conditions: ${_profile.healthConditions.join(', ')}',
            if (_profile.allergies.isNotEmpty)
              'Allergies: ${_profile.allergies.join(', ')}',
            'Diet: ${_profile.dietaryType?.capitalize()}',
          ]),

          _buildSummaryCard('Cooking Preferences', [
            'Skill: ${_profile.cookingSkill?.capitalize()}',
            'Budget: ₹${_profile.budgetPerMealInr}/meal',
            'Max time: ${_profile.maxCookingTimeMinutes} min',
            'Household: ${_profile.householdSize} people',
          ]),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(String title, List<String> items) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          ...items.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(item, style: TextStyle(color: Colors.grey[600])),
              )),
        ],
      ),
    );
  }

  // Helper widgets
  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    TextInputType? keyboardType,
    Function(String)? onChanged,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      onChanged: onChanged,
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }

  Widget _buildDropdown<T>({
    required T? value,
    required String label,
    required List<DropdownMenuItem<T>> items,
    required Function(T?) onChanged,
  }) {
    return DropdownButtonFormField<T>(
      value: value,
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
      items: items,
      onChanged: onChanged,
    );
  }

  Widget _buildSelectableCard({
    required String title,
    required String subtitle,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.blush : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? AppColors.rose : AppColors.blush,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: isSelected ? AppColors.rose : AppColors.dark,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 14, color: AppColors.muted),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNavigationButtons() {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          if (_currentStep > 0)
            Expanded(
              child: OutlinedButton(
                onPressed: _previousStep,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('Back'),
              ),
            ),
          if (_currentStep > 0) const SizedBox(width: 12),
          Expanded(
            flex: _currentStep > 0 ? 2 : 1,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _nextStep,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.rose,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : Text(_currentStep == _totalSteps - 1
                      ? 'Complete Setup'
                      : 'Next'),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    _animationController.dispose();
    _nicknameController.dispose();
    _ageController.dispose();
    _weightController.dispose();
    _heightController.dispose();
    _budgetController.dispose();
    _cookingTimeController.dispose();
    _householdController.dispose();
    super.dispose();
  }
}

// Extension for string capitalization
extension StringCasingExtension on String {
  String capitalize() {
    return '${this[0].toUpperCase()}${substring(1)}';
  }
}
