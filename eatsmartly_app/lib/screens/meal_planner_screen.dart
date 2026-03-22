import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';

class MealPlannerScreen extends StatefulWidget {
  const MealPlannerScreen({Key? key}) : super(key: key);
  @override
  State<MealPlannerScreen> createState() => _MealPlannerScreenState();
}

class _MealPlannerScreenState extends State<MealPlannerScreen> {
  final EatSmartlyAPI api = EatSmartlyAPI();
  late TextEditingController _ingredientsController;
  bool _isLoading = false;
  bool _isFormLoading = false;
  Map<String, dynamic>? _mealPlanResult;
  bool _isChatMode = false;
  final List<Map<String, dynamic>> _chatMessages = [];
  final List<Map<String, dynamic>> _chatHistory = [];
  final TextEditingController _chatInputController = TextEditingController();
  final ScrollController _chatScrollController = ScrollController();
  String _userName = '';
  final List<String> _availableIngredients = [];
  final TextEditingController _ingredientInputController = TextEditingController();
  String _selectedMealType = 'balanced';
  int _numMeals = 5;
  int _cookingTimeLimit = 30;
  final List<String> _dietaryRestrictions = [];
  final List<String> _cuisinePreferences = [];

  @override
  void initState() {
    super.initState();
    _ingredientsController = TextEditingController();
    _loadUserName();
  }

  Future<void> _loadUserName() async {
    final authService = Provider.of<AuthService>(context, listen: false);
    final profile = await authService.getUserProfile();
    if (mounted) {
      setState(() {
        _userName = profile?['nickname'] ?? profile?['full_name'] ??
            authService.currentUser?.displayName ??
            authService.currentUser?.email?.split('@')[0] ?? '';
      });
    }
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
    if (ingredient.trim().isNotEmpty && !_availableIngredients.contains(ingredient.trim())) {
      setState(() { _availableIngredients.add(ingredient.trim()); _ingredientInputController.clear(); });
    }
  }

  void _removeIngredient(String ingredient) => setState(() => _availableIngredients.remove(ingredient));

  Future<void> _generateMealPlan() async {
    if (_availableIngredients.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: const Text('Please add at least one ingredient'), backgroundColor: AppColors.error));
      return;
    }
    setState(() { _isFormLoading = true; _mealPlanResult = null; });
    try {
      final result = await api.generateMealPlan(
        availableIngredients: _availableIngredients, nutritionalGoals: _getNutritionalGoals(),
        dietaryRestrictions: _dietaryRestrictions.isEmpty ? null : _dietaryRestrictions,
        cuisinePreferences: _cuisinePreferences.isEmpty ? null : _cuisinePreferences,
        mealType: _selectedMealType, numMeals: _numMeals, cookingTimeLimit: _cookingTimeLimit,
      );
      setState(() { _mealPlanResult = result; _isFormLoading = false; });
    } catch (e) {
      final discovered = await EatSmartlyAPI.autoRediscover();
      if (discovered) {
        try {
          final result = await api.generateMealPlan(
            availableIngredients: _availableIngredients, nutritionalGoals: _getNutritionalGoals(),
            dietaryRestrictions: _dietaryRestrictions.isEmpty ? null : _dietaryRestrictions,
            cuisinePreferences: _cuisinePreferences.isEmpty ? null : _cuisinePreferences,
            mealType: _selectedMealType, numMeals: _numMeals, cookingTimeLimit: _cookingTimeLimit,
          );
          setState(() { _mealPlanResult = result; _isFormLoading = false; });
          return;
        } catch (_) {}
      }
      setState(() { _isFormLoading = false; });
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cannot connect to server'), backgroundColor: AppColors.error));
    }
  }

  Map<String, dynamic> _getNutritionalGoals() {
    switch (_selectedMealType) {
      case 'high_protein': return {'protein_g': 50, 'calories': 2500};
      case 'weight_loss': return {'protein_g': 40, 'calories': 1800};
      case 'muscle_gain': return {'protein_g': 60, 'calories': 3000};
      default: return {'protein_g': 30, 'calories': 2000};
    }
  }

  Future<void> _sendChatMessage() async {
    final message = _chatInputController.text.trim();
    if (message.isEmpty) return;
    setState(() {
      _chatMessages.add({'sender': 'user', 'text': message});
      _chatMessages.add({'sender': 'bot', 'text': 'Thinking...', 'isTyping': true});
      _chatInputController.clear();
      _isLoading = true;
    });
    _chatHistory.add({'role': 'user', 'parts': [message]});
    _scrollToBottom();
    try {
      final userProfile = await EatSmartlyAPI.getLocalUserProfile();
      final result = await api.mealChat(
        message: message,
        history: _chatHistory.length > 6 ? _chatHistory.sublist(_chatHistory.length - 6) : _chatHistory,
        userProfile: userProfile,
      );
      final responseText = result['response'] ?? 'Sorry, I could not process that.';
      _chatHistory.add({'role': 'model', 'parts': [responseText]});
      setState(() { _chatMessages.removeLast(); _chatMessages.add({'sender': 'bot', 'text': responseText}); _isLoading = false; });
    } catch (e) {
      final discovered = await EatSmartlyAPI.autoRediscover();
      if (discovered) {
        try {
          final userProfile = await EatSmartlyAPI.getLocalUserProfile();
          final result = await api.mealChat(
            message: message,
            history: _chatHistory.length > 6 ? _chatHistory.sublist(_chatHistory.length - 6) : _chatHistory,
            userProfile: userProfile,
          );
          final responseText = result['response'] ?? 'Sorry, I could not process that.';
          _chatHistory.add({'role': 'model', 'parts': [responseText]});
          setState(() { _chatMessages.removeLast(); _chatMessages.add({'sender': 'bot', 'text': responseText}); _isLoading = false; });
          _scrollToBottom();
          return;
        } catch (_) {}
      }
      setState(() {
        _chatMessages.removeLast();
        _chatMessages.add({'sender': 'bot', 'text': 'Cannot connect to server. Please check backend is running.'});
        _isLoading = false;
      });
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (mounted && _chatScrollController.hasClients) {
        _chatScrollController.animateTo(_chatScrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(color: AppColors.rose, borderRadius: BorderRadius.circular(24)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_userName.isNotEmpty ? 'Hey $_userName 🍽️' : 'AI Meal Planner 🍽️',
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: Colors.white)),
                  const SizedBox(height: 4),
                  const Text('Plan meals around what you have', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 16),
                  Container(
                    decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(14)),
                    padding: const EdgeInsets.all(4),
                    child: Row(children: [
                      _modeTab('📋 Form', !_isChatMode, () => setState(() => _isChatMode = false)),
                      _modeTab('💬 Chat', _isChatMode, () => setState(() => _isChatMode = true)),
                    ]),
                  ),
                ],
              ),
            ),
            Expanded(child: _isChatMode ? _buildChatMode() : (_mealPlanResult != null ? _buildMealPlanResult() : _buildInputForm())),
          ],
        ),
      ),
    );
  }

  Widget _modeTab(String label, bool active, VoidCallback onTap) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(color: active ? Colors.white : Colors.transparent, borderRadius: BorderRadius.circular(10)),
          child: Center(child: Text(label, style: TextStyle(fontWeight: FontWeight.w700, color: active ? AppColors.rose : Colors.white, fontSize: 14))),
        ),
      ),
    );
  }

  Widget _buildChatMode() {
    return Column(children: [
      Expanded(child: _chatMessages.isEmpty ? _buildChatEmptyState() : ListView.builder(
        controller: _chatScrollController,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        itemCount: _chatMessages.length,
        itemBuilder: (context, index) {
          final msg = _chatMessages[index];
          return _buildChatBubble(msg['text'] ?? '', msg['sender'] == 'user', msg['isTyping'] == true);
        },
      )),
      _buildChatInput(),
    ]);
  }

  Widget _buildChatEmptyState() {
    return Center(child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Container(width: 80, height: 80, decoration: const BoxDecoration(color: AppColors.blush, shape: BoxShape.circle),
          child: const Center(child: Text('🍳', style: TextStyle(fontSize: 36)))),
        const SizedBox(height: 20),
        Text(_userName.isNotEmpty ? 'What shall we cook today, $_userName?' : 'What shall we cook today?',
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.dark), textAlign: TextAlign.center),
        const SizedBox(height: 8),
        const Text('Tell me your ingredients and preferences', style: TextStyle(color: AppColors.muted, fontSize: 14), textAlign: TextAlign.center),
        const SizedBox(height: 24),
        Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: [
          _suggestionChip('I have chicken & rice'),
          _suggestionChip('High protein with eggs'),
          _suggestionChip('Quick 15-min meal'),
          _suggestionChip('Weight loss ideas'),
        ]),
      ]),
    ));
  }

  Widget _suggestionChip(String text) {
    return GestureDetector(
      onTap: () { _chatInputController.text = text; _sendChatMessage(); },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(20)),
        child: Text(text, style: const TextStyle(color: AppColors.rose, fontSize: 13, fontWeight: FontWeight.w600)),
      ),
    );
  }

  Widget _buildChatInput() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      decoration: BoxDecoration(color: AppColors.white,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 12, offset: const Offset(0, -4))]),
      child: Row(children: [
        Expanded(child: TextField(
          controller: _chatInputController, enabled: !_isLoading,
          decoration: InputDecoration(hintText: 'Ask about meal planning...', filled: true, fillColor: AppColors.blush,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12)),
          onSubmitted: (_) => _sendChatMessage(),
        )),
        const SizedBox(width: 8),
        GestureDetector(
          onTap: _isLoading ? null : _sendChatMessage,
          child: Container(
            width: 44, height: 44,
            decoration: BoxDecoration(color: AppColors.rose, borderRadius: BorderRadius.circular(14)),
            child: _isLoading
                ? const Padding(padding: EdgeInsets.all(10), child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.send_rounded, color: Colors.white, size: 20),
          ),
        ),
      ]),
    );
  }

  Widget _buildChatBubble(String text, bool isUser, [bool isTyping = false]) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isUser ? AppColors.rose : AppColors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16), topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 4), bottomRight: Radius.circular(isUser ? 4 : 16),
          ),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 6, offset: const Offset(0, 2))],
        ),
        child: isTyping
            ? Row(mainAxisSize: MainAxisSize.min, children: [
                Text(text, style: TextStyle(color: isUser ? Colors.white : AppColors.dark, fontSize: 13)),
                const SizedBox(width: 8),
                SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.muted)),
              ])
            : Text(text, style: TextStyle(color: isUser ? Colors.white : AppColors.dark, fontSize: 13, height: 1.4)),
      ),
    );
  }

  Widget _buildInputForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _sectionLabel('🥘 Ingredients'),
        const SizedBox(height: 10),
        Container(
          decoration: BoxDecoration(color: AppColors.white, borderRadius: BorderRadius.circular(16),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 8)]),
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(children: [
            Expanded(child: TextField(
              controller: _ingredientInputController,
              decoration: const InputDecoration(hintText: 'Add ingredient (e.g. chicken, rice)',
                border: InputBorder.none, fillColor: Colors.transparent, filled: false),
              onSubmitted: _addIngredient,
            )),
            GestureDetector(
              onTap: () => _addIngredient(_ingredientInputController.text),
              child: Container(padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: AppColors.rose, borderRadius: BorderRadius.circular(10)),
                child: const Icon(Icons.add, color: Colors.white, size: 18)),
            ),
          ]),
        ),
        if (_availableIngredients.isNotEmpty) ...[
          const SizedBox(height: 10),
          Wrap(spacing: 8, runSpacing: 8, children: _availableIngredients.map((ing) => Chip(
            label: Text(ing, style: const TextStyle(color: AppColors.dark, fontSize: 13)),
            deleteIcon: const Icon(Icons.close, size: 16, color: AppColors.muted),
            onDeleted: () => _removeIngredient(ing),
            backgroundColor: AppColors.blush, side: BorderSide.none,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          )).toList()),
        ],
        const SizedBox(height: 20),
        _sectionLabel('🎯 Meal Type'),
        const SizedBox(height: 10),
        ...[ 
          ['balanced', '⚖️ Balanced', 'Balanced macronutrients'],
          ['high_protein', '💪 High Protein', 'Maximum protein for muscle building'],
          ['weight_loss', '⬇️ Weight Loss', 'Low calorie, high protein'],
          ['muscle_gain', '🏋️ Muscle Gain', 'High calories and protein'],
        ].map((opt) => _mealTypeCard(opt[0], opt[1], opt[2])),
        const SizedBox(height: 20),
        _sectionLabel('📊 Number of Meals: $_numMeals'),
        Slider(value: _numMeals.toDouble(), min: 1, max: 10, divisions: 9, activeColor: AppColors.rose,
          onChanged: (v) => setState(() => _numMeals = v.toInt())),
        _sectionLabel('⏱️ Max Cooking Time: ${_cookingTimeLimit}min'),
        Slider(value: _cookingTimeLimit.toDouble(), min: 5, max: 120, divisions: 23, activeColor: AppColors.coral,
          onChanged: (v) => setState(() => _cookingTimeLimit = v.toInt())),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: _isFormLoading ? null : _generateMealPlan,
            icon: _isFormLoading
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.auto_awesome),
            label: Text(_isFormLoading ? 'Generating...' : 'Generate Meal Plan'),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.rose, foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
          ),
        ),
      ]),
    );
  }

  Widget _sectionLabel(String text) => Text(text, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.dark));

  Widget _mealTypeCard(String value, String title, String subtitle) {
    final isSelected = _selectedMealType == value;
    return GestureDetector(
      onTap: () => setState(() => _selectedMealType = value),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.blush : AppColors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: isSelected ? AppColors.rose : Colors.transparent, width: 1.5),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 6)],
        ),
        child: Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: TextStyle(fontWeight: FontWeight.w700, color: isSelected ? AppColors.rose : AppColors.dark)),
            Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
          ])),
          if (isSelected) const Icon(Icons.check_circle_rounded, color: AppColors.rose, size: 20),
        ]),
      ),
    );
  }

  Widget _buildMealPlanResult() {
    final success = _mealPlanResult?['success'] ?? false;
    if (!success) {
      return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Icon(Icons.error_outline, size: 64, color: AppColors.error),
        const SizedBox(height: 16),
        const Text('Error generating meal plan', style: TextStyle(color: AppColors.error)),
        const SizedBox(height: 16),
        ElevatedButton(onPressed: () => setState(() => _mealPlanResult = null), child: const Text('Try Again')),
      ]));
    }
    final meals = _mealPlanResult?['meals'] ?? [];
    final dailyNutrition = _mealPlanResult?['daily_nutrition'] ?? {};
    final shoppingList = _mealPlanResult?['shopping_list'] ?? [];
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(20)),
          child: Text('🎯 ${_selectedMealType.replaceAll('_', ' ').toUpperCase()}',
            style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.rose, fontSize: 13)),
        ),
        const SizedBox(height: 16),
        if (dailyNutrition.isNotEmpty) _buildNutritionSummary(dailyNutrition),
        const SizedBox(height: 16),
        _sectionLabel('🍽️ Meal Suggestions'),
        const SizedBox(height: 10),
        ...List.generate(meals.length, (i) => _buildMealCard(meals[i] as Map<String, dynamic>, i + 1)),
        if (shoppingList.isNotEmpty) ...[
          const SizedBox(height: 16),
          _sectionLabel('🛒 Shopping List'),
          const SizedBox(height: 10),
          _buildShoppingList(List<String>.from(shoppingList)),
        ],
        const SizedBox(height: 20),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => setState(() => _mealPlanResult = null),
            icon: const Icon(Icons.refresh, color: AppColors.rose),
            label: const Text('Generate Another Plan', style: TextStyle(color: AppColors.rose)),
            style: OutlinedButton.styleFrom(side: const BorderSide(color: AppColors.rose),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
          ),
        ),
      ]),
    );
  }

  Widget _buildNutritionSummary(Map<String, dynamic> nutrition) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppColors.cardMint, borderRadius: BorderRadius.circular(16)),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
        _nutritionStat('${nutrition['calories'] ?? 'N/A'}', 'Calories', '🔥'),
        _nutritionStat('${nutrition['protein_g'] ?? 'N/A'}g', 'Protein', '🥚'),
        _nutritionStat('${nutrition['carbs_g'] ?? 'N/A'}g', 'Carbs', '🍚'),
      ]),
    );
  }

  Widget _nutritionStat(String value, String label, String emoji) {
    return Column(children: [
      Text(emoji, style: const TextStyle(fontSize: 20)),
      const SizedBox(height: 4),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppColors.dark)),
      Text(label, style: const TextStyle(fontSize: 11, color: AppColors.muted)),
    ]);
  }

  Widget _buildMealCard(Map<String, dynamic> meal, int mealNumber) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.white, borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 8)]),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(width: 36, height: 36,
            decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(10)),
            child: Center(child: Text('M$mealNumber', style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.rose, fontSize: 13)))),
          const SizedBox(width: 10),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(meal['name'] ?? 'Meal $mealNumber', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: AppColors.dark)),
            Text(meal['cuisine'] ?? '', style: const TextStyle(fontSize: 12, color: AppColors.muted)),
          ])),
        ]),
        if (meal['description'] != null) ...[
          const SizedBox(height: 8),
          Text(meal['description'], style: const TextStyle(fontSize: 13, color: AppColors.muted, height: 1.4)),
        ],
        if (meal['nutrition'] != null) ...[
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(color: AppColors.cream, borderRadius: BorderRadius.circular(10)),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
              Text('�� ${meal['nutrition']['calories'] ?? 0} cal', style: const TextStyle(fontSize: 12, color: AppColors.muted)),
              Text('🥚 ${meal['nutrition']['protein_g'] ?? 0}g', style: const TextStyle(fontSize: 12, color: AppColors.muted)),
              Text('🍚 ${meal['nutrition']['carbs_g'] ?? 0}g', style: const TextStyle(fontSize: 12, color: AppColors.muted)),
            ]),
          ),
        ],
      ]),
    );
  }

  Widget _buildShoppingList(List<String> items) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.cardPeach, borderRadius: BorderRadius.circular(16)),
      child: Wrap(spacing: 8, runSpacing: 8, children: items.map((item) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(color: AppColors.white, borderRadius: BorderRadius.circular(20)),
        child: Text(item, style: const TextStyle(fontSize: 12, color: AppColors.dark)),
      )).toList()),
    );
  }
}
