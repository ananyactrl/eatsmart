import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/api_service.dart';

class MealPlannerScreen extends StatefulWidget {
  const MealPlannerScreen({Key? key}) : super(key: key);

  @override
  State<MealPlannerScreen> createState() => _MealPlannerScreenState();
}

class _MealPlannerScreenState extends State<MealPlannerScreen> {
  final EatSmartlyAPI api = EatSmartlyAPI();
  late TextEditingController _ingredientsController;

  bool _isLoading = false;
  Map<String, dynamic>? _mealPlanResult;
  String? _error;

  // Mode toggle
  bool _isChatMode = false;

  // Chat fields
  final List<Map<String, String>> _chatMessages = [];
  final TextEditingController _chatInputController = TextEditingController();
  final ScrollController _chatScrollController = ScrollController();

  // Form fields
  final List<String> _availableIngredients = [];
  final TextEditingController _ingredientInputController =
      TextEditingController();

  String _selectedMealType =
      'balanced'; // balanced, high_protein, weight_loss, muscle_gain
  int _numMeals = 5;
  int _cookingTimeLimit = 30;
  final List<String> _dietaryRestrictions = [];
  final List<String> _cuisinePreferences = [];

  @override
  void initState() {
    super.initState();
    _ingredientsController = TextEditingController();
  }

  @override
  void dispose() {
    _ingredientsController.dispose();
    _ingredientInputController.dispose();
    _chatInputController.dispose();
    _chatScrollController.dispose();
    super.dispose();
  }

  void _addIngredient(String ingredient) {
    if (ingredient.trim().isNotEmpty &&
        !_availableIngredients.contains(ingredient.trim())) {
      setState(() {
        _availableIngredients.add(ingredient.trim());
        _ingredientInputController.clear();
      });
    }
  }

  void _removeIngredient(String ingredient) {
    setState(() {
      _availableIngredients.remove(ingredient);
    });
  }

  Future<void> _generateMealPlan() async {
    if (_availableIngredients.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please add at least one ingredient'),
          backgroundColor: Color(0xFFE53935),
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
      _mealPlanResult = null;
    });

    try {
      final result = await api.generateMealPlan(
        availableIngredients: _availableIngredients,
        nutritionalGoals: _getNutritionalGoals(),
        dietaryRestrictions:
            _dietaryRestrictions.isEmpty ? null : _dietaryRestrictions,
        cuisinePreferences:
            _cuisinePreferences.isEmpty ? null : _cuisinePreferences,
        mealType: _selectedMealType,
        numMeals: _numMeals,
        cookingTimeLimit: _cookingTimeLimit,
      );

      setState(() {
        _mealPlanResult = result;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $_error'),
            backgroundColor: const Color(0xFFE53935),
          ),
        );
      }
    }
  }

  Map<String, dynamic> _getNutritionalGoals() {
    switch (_selectedMealType) {
      case 'high_protein':
        return {'protein_g': 50, 'calories': 2500};
      case 'weight_loss':
        return {'protein_g': 40, 'calories': 1800};
      case 'muscle_gain':
        return {'protein_g': 60, 'calories': 3000};
      default:
        return {'protein_g': 30, 'calories': 2000};
    }
  }

  Future<void> _sendChatMessage() async {
    final message = _chatInputController.text.trim();
    if (message.isEmpty) return;

    setState(() {
      _chatMessages.add({'sender': 'user', 'text': message});
      _chatInputController.clear();
      _isLoading = true;
    });

    // Scroll to bottom
    Future.delayed(const Duration(milliseconds: 100), () {
      _chatScrollController.animateTo(
        _chatScrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    });

    try {
      // Parse user message to extract meal planning intent
      final lowerMessage = message.toLowerCase();

      // Extract ingredients mentioned in message
      final extractedIngredients = _extractIngredientsFromText(message);

      // Determine meal type from keywords
      String mealType = 'balanced';
      if (lowerMessage.contains('protein')) mealType = 'high_protein';
      if (lowerMessage.contains('weight loss') ||
          lowerMessage.contains('diet')) {
        mealType = 'weight_loss';
      }
      if (lowerMessage.contains('muscle') || lowerMessage.contains('build')) {
        mealType = 'muscle_gain';
      }

      // If ingredients found, generate meal plan
      if (extractedIngredients.isNotEmpty) {
        final result = await api.generateMealPlan(
          availableIngredients: extractedIngredients,
          nutritionalGoals: mealType == 'balanced'
              ? {'protein_g': 30, 'calories': 2000}
              : mealType == 'high_protein'
                  ? {'protein_g': 50, 'calories': 2500}
                  : mealType == 'weight_loss'
                      ? {'protein_g': 40, 'calories': 1800}
                      : {'protein_g': 60, 'calories': 3000},
          mealType: mealType,
          numMeals: 5,
          cookingTimeLimit: 30,
        );

        setState(() {
          _mealPlanResult = result;
          _chatMessages.add({
            'sender': 'bot',
            'text':
                '✅ Generated ${mealType.replaceAll('_', ' ')} meal plan with ${result['meals'].length} meals!'
          });
          _isLoading = false;
        });
      } else {
        setState(() {
          _chatMessages.add({
            'sender': 'bot',
            'text':
                'I can help you plan your meals! 🍽️\n\nTry mentioning:\n• Ingredients you have (e.g., "I have chicken, rice, and broccoli")\n• Your goal (high protein, weight loss, muscle gain, or balanced)\n• Cooking time preference\n\nExample: "I have chicken and rice, I want a high protein meal"'
          });
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _chatMessages.add({
          'sender': 'bot',
          'text': '❌ Error: ${e.toString().replaceAll('Exception: ', '')}'
        });
        _isLoading = false;
      });
    }

    Future.delayed(const Duration(milliseconds: 100), () {
      if (mounted) {
        _chatScrollController.animateTo(
          _chatScrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  List<String> _extractIngredientsFromText(String text) {
    // Simple ingredient extraction - can be enhanced
    final commonIngredients = [
      'chicken',
      'beef',
      'pork',
      'fish',
      'salmon',
      'tuna',
      'shrimp',
      'egg',
      'eggs',
      'rice',
      'pasta',
      'bread',
      'wheat',
      'oats',
      'quinoa',
      'broccoli',
      'carrot',
      'spinach',
      'lettuce',
      'tomato',
      'onion',
      'garlic',
      'pepper',
      'apple',
      'banana',
      'orange',
      'strawberry',
      'blueberry',
      'milk',
      'cheese',
      'yogurt',
      'butter',
      'oil',
      'olive',
      'beans',
      'lentils',
      'chickpeas',
      'nuts',
      'almond',
      'peanut',
    ];

    final found = <String>[];
    final lowerText = text.toLowerCase();

    for (final ingredient in commonIngredients) {
      if (lowerText.contains(ingredient)) {
        found.add(ingredient);
      }
    }

    return found;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        title: const Text('AI Meal Planner'),
        elevation: 0,
        backgroundColor: const Color(0xFFFFC1CC),
        centerTitle: true,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(50),
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: _buildModeToggle(),
          ),
        ),
      ),
      body: _mealPlanResult != null && !_isChatMode
          ? _buildMealPlanResult()
          : (_isChatMode ? _buildChatMode() : _buildInputForm()),
    );
  }

  Widget _buildModeToggle() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () {
                setState(() => _isChatMode = false);
              },
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: !_isChatMode
                      ? const Color(0xFFFFC1CC)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Center(
                  child: Text(
                    '📋 Form',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () {
                setState(() => _isChatMode = true);
              },
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: _isChatMode
                      ? const Color(0xFFFFC1CC)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Center(
                  child: Text(
                    '💬 Chat',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChatMode() {
    return Column(
      children: [
        Expanded(
          child: _chatMessages.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text(
                        '🤖 Chat with AI Meal Planner',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF4C0004),
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 24),
                        child: Text(
                          'Tell me what ingredients you have and your meal preferences. I\'ll create a personalized meal plan for you!',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey),
                        ),
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        'Example queries:',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('• "I have chicken, rice, and broccoli"'),
                            Text('• "High protein meal with salmon"'),
                            Text('• "Weight loss meal with eggs and veggies"'),
                            Text('• "I want a balanced curry with lentils"'),
                          ],
                        ),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  controller: _chatScrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _chatMessages.length,
                  itemBuilder: (context, index) {
                    final msg = _chatMessages[index];
                    final isUser = msg['sender'] == 'user';
                    return _buildChatBubble(msg['text'] ?? '', isUser);
                  },
                ),
        ),
        if (_mealPlanResult != null && _mealPlanResult?['success'] == true)
          Padding(
            padding: const EdgeInsets.all(12),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  setState(() => _mealPlanResult = null);
                },
                icon: const Icon(Icons.arrow_back),
                label: const Text('View Full Plan'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFAFA231),
                ),
              ),
            ),
          ),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 8,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _chatInputController,
                  enabled: !_isLoading,
                  decoration: InputDecoration(
                    hintText: 'Ask me about meal planning...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                  ),
                  onSubmitted: (_) => _sendChatMessage(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                onPressed: _isLoading ? null : _sendChatMessage,
                icon: _isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send, color: Color(0xFFFFC1CC)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildChatBubble(String text, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFFFFC1CC) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: isUser
              ? null
              : Border.all(color: const Color(0xFFFFC1CC), width: 1),
        ),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        child: Text(
          text,
          style: TextStyle(
            color: isUser ? const Color(0xFF4C0004) : Colors.black87,
            fontSize: 13,
            height: 1.4,
          ),
        ),
      ),
    );
  }

  Widget _buildInputForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Ingredients section
          _buildSectionHeader('🥘 Available Ingredients'),
          const SizedBox(height: 12),
          _buildIngredientsInput(),
          const SizedBox(height: 12),
          _buildIngredientsList(),
          const SizedBox(height: 24),

          // Meal Type section
          _buildSectionHeader('🎯 Meal Type'),
          const SizedBox(height: 12),
          _buildMealTypeSelector(),
          const SizedBox(height: 24),

          // Number of meals
          _buildSectionHeader('📊 Number of Meals'),
          const SizedBox(height: 12),
          _buildSlider(
            'Meals: $_numMeals',
            _numMeals.toDouble(),
            1,
            10,
            (value) {
              setState(() => _numMeals = value.toInt());
            },
          ),
          const SizedBox(height: 24),

          // Cooking time
          _buildSectionHeader('⏱️ Max Cooking Time'),
          const SizedBox(height: 12),
          _buildSlider(
            'Time: $_cookingTimeLimit minutes',
            _cookingTimeLimit.toDouble(),
            5,
            120,
            (value) {
              setState(() => _cookingTimeLimit = value.toInt());
            },
          ),
          const SizedBox(height: 24),

          // Generate button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _isLoading ? null : _generateMealPlan,
              icon: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.auto_awesome),
              label: Text(_isLoading ? 'Generating...' : 'Generate Meal Plan'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFFC1CC),
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIngredientsInput() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFFC1CC), width: 2),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _ingredientInputController,
              decoration: const InputDecoration(
                hintText: 'Enter ingredient (e.g., chicken, rice)',
                border: InputBorder.none,
              ),
              onSubmitted: (value) {
                _addIngredient(value);
              },
            ),
          ),
          IconButton(
            icon: const Icon(Icons.add_circle, color: Color(0xFFFFC1CC)),
            onPressed: () {
              _addIngredient(_ingredientInputController.text);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildIngredientsList() {
    if (_availableIngredients.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.5),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Text(
          'No ingredients added yet. Add some to get started!',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey),
        ),
      );
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _availableIngredients
          .map(
            (ingredient) => Chip(
              label: Text(ingredient),
              deleteIcon: const Icon(Icons.close),
              onDeleted: () => _removeIngredient(ingredient),
              backgroundColor: const Color(0xFFFFC1CC),
              labelStyle: const TextStyle(color: Color(0xFF4C0004)),
            ),
          )
          .toList(),
    );
  }

  Widget _buildMealTypeSelector() {
    return Column(
      children: [
        _buildSelectableButton(
            'balanced', '⚖️ Balanced', 'Balanced macronutrients'),
        const SizedBox(height: 8),
        _buildSelectableButton('high_protein', '💪 High Protein',
            'Maximum protein for muscle building'),
        const SizedBox(height: 8),
        _buildSelectableButton(
            'weight_loss', '⬇️ Weight Loss', 'Low calorie, high protein'),
        const SizedBox(height: 8),
        _buildSelectableButton(
            'muscle_gain', '🏋️ Muscle Gain', 'High calories and protein'),
      ],
    );
  }

  Widget _buildSelectableButton(String value, String title, String subtitle) {
    final isSelected = _selectedMealType == value;
    return GestureDetector(
      onTap: () {
        setState(() => _selectedMealType = value);
      },
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFFFC1CC) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: const Color(0xFFFFC1CC),
            width: 2,
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color:
                          isSelected ? const Color(0xFF4C0004) : Colors.black87,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ),
            ),
            if (isSelected)
              const Icon(Icons.check_circle, color: Color(0xFF4C0004)),
          ],
        ),
      ),
    );
  }

  Widget _buildSlider(String label, double value, double min, double max,
      Function(double) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          divisions: (max - min).toInt(),
          label: value.toInt().toString(),
          activeColor: const Color(0xFFFFC1CC),
          onChanged: onChanged,
        ),
      ],
    );
  }

  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.bold,
        color: Color(0xFF4C0004),
      ),
    );
  }

  Widget _buildMealPlanResult() {
    final success = _mealPlanResult?['success'] ?? false;

    if (!success) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: AppColors.error),
            const SizedBox(height: 16),
            Text(
              'Error generating meal plan',
              style: TextStyle(color: AppColors.error, fontSize: 16),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () {
                setState(() => _mealPlanResult = null);
              },
              icon: const Icon(Icons.arrow_back),
              label: const Text('Try Again'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFFFC1CC),
              ),
            ),
          ],
        ),
      );
    }

    final meals = _mealPlanResult?['meals'] ?? [];
    final dailyNutrition = _mealPlanResult?['daily_nutrition'] ?? {};
    final shoppingList = _mealPlanResult?['shopping_list'] ?? [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Meal type badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFFFC1CC),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              '🎯 ${_selectedMealType.replaceAll('_', ' ').toUpperCase()}',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Color(0xFF4C0004),
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Daily nutrition summary
          if (dailyNutrition.isNotEmpty) _buildNutritionSummary(dailyNutrition),
          const SizedBox(height: 20),

          // Meals list
          _buildSectionHeader('🍽️ Meal Suggestions'),
          const SizedBox(height: 12),
          ...List.generate(
            meals.length,
            (index) =>
                _buildMealCard(meals[index] as Map<String, dynamic>, index + 1),
          ),
          const SizedBox(height: 20),

          // Shopping list
          if (shoppingList.isNotEmpty) ...[
            _buildSectionHeader('🛒 Shopping List'),
            const SizedBox(height: 12),
            _buildShoppingList(List<String>.from(shoppingList)),
            const SizedBox(height: 20),
          ],

          // Back button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () {
                setState(() => _mealPlanResult = null);
              },
              icon: const Icon(Icons.arrow_back),
              label: const Text('Generate Another Plan'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFAFA231),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNutritionSummary(Map<String, dynamic> nutrition) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFFC1CC), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '📊 Daily Nutrition Target',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNutritionItem('${nutrition['calories'] ?? 'N/A'}',
                  'Calories', Icons.local_fire_department),
              _buildNutritionItem(
                  '${nutrition['protein_g'] ?? 'N/A'}g', 'Protein', Icons.egg),
              _buildNutritionItem('${nutrition['carbs_g'] ?? 'N/A'}g', 'Carbs',
                  Icons.rice_bowl),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNutritionItem(String value, String label, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: const Color(0xFFAFA231), size: 24),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      ],
    );
  }

  Widget _buildMealCard(Map<String, dynamic> meal, int mealNumber) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFC1CC),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Center(
                    child: Text(
                      'M$mealNumber',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF4C0004),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        meal['name'] ?? 'Meal $mealNumber',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                          color: Color(0xFF4C0004),
                        ),
                      ),
                      Text(
                        meal['cuisine'] ?? 'Healthy cuisine',
                        style:
                            const TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              meal['description'] ?? 'A delicious and nutritious meal',
              style: const TextStyle(fontSize: 13, height: 1.4),
            ),
            // Show API recipe data if available
            if (meal['api_recipe'] != null) ...[
              const SizedBox(height: 12),
              _buildRecipeDetails(meal['api_recipe']),
            ],
            if (meal['nutrition'] != null) ...[
              const SizedBox(height: 12),
              _buildMealNutrition(meal['nutrition']),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRecipeDetails(Map<String, dynamic> recipe) {
    final ingredients = recipe['ingredients'] as List<dynamic>?;
    final cookTime = recipe['cook_time_minutes'];
    final prepTime = recipe['prep_time_minutes'];

    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF0F5),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFFFB6D9), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '📖 Recipe from API Ninjas',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: Color(0xFFAFA231),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              if (prepTime != null) ...[
                const Icon(Icons.timer, size: 14, color: Color(0xFFAFA231)),
                const SizedBox(width: 4),
                Text('Prep: ${prepTime}m',
                    style: const TextStyle(fontSize: 11)),
                const SizedBox(width: 12),
              ],
              if (cookTime != null) ...[
                const Icon(Icons.local_fire_department,
                    size: 14, color: Color(0xFFAFA231)),
                const SizedBox(width: 4),
                Text('Cook: ${cookTime}m',
                    style: const TextStyle(fontSize: 11)),
              ],
            ],
          ),
          if (ingredients != null && ingredients.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              'Ingredients (${ingredients.length})',
              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            Wrap(
              spacing: 4,
              runSpacing: 4,
              children: ingredients
                  .take(5)
                  .map(
                    (ing) => Text(
                      '• ${ing.toString().split(',').first}',
                      style: const TextStyle(fontSize: 10),
                    ),
                  )
                  .toList(),
            ),
            if (ingredients.length > 5)
              Text(
                '+ ${ingredients.length - 5} more',
                style: const TextStyle(fontSize: 9, color: Colors.grey),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildMealNutrition(Map<String, dynamic> nutrition) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildNutritionTag(
              '${nutrition['calories'] ?? 0} cal', Icons.whatshot),
          _buildNutritionTag(
              '${nutrition['protein_g'] ?? 0}g protein', Icons.egg),
          _buildNutritionTag(
              '${nutrition['carbs_g'] ?? 0}g carbs', Icons.rice_bowl),
        ],
      ),
    );
  }

  Widget _buildNutritionTag(String text, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 14, color: const Color(0xFFAFA231)),
        const SizedBox(width: 4),
        Text(text, style: const TextStyle(fontSize: 11)),
      ],
    );
  }

  Widget _buildShoppingList(List<String> items) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFAFA231), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Items to buy (${items.length})',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: items
                .map(
                  (item) => Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF8E1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      item,
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}
