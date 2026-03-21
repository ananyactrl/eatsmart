import 'package:flutter/material.dart';
import '../models/food_analysis.dart';
import '../theme.dart';
import '../widgets/ingredient_intelligence_card.dart';

class ResultScreen extends StatelessWidget {
  final FoodAnalysis analysis;
  final Map<String, dynamic>? productImage;

  const ResultScreen({
    Key? key,
    required this.analysis,
    this.productImage,
  }) : super(key: key);

  Color _getVerdictColor() {
    switch (analysis.verdict.toLowerCase()) {
      case 'safe':
        return AppColors.success;
      case 'caution':
        return AppColors.warning;
      case 'avoid':
        return AppColors.error;
      default:
        return AppColors.info;
    }
  }

  IconData _getVerdictIcon() {
    switch (analysis.verdict.toLowerCase()) {
      case 'safe':
        return Icons.check_circle;
      case 'caution':
        return Icons.warning;
      case 'avoid':
        return Icons.cancel;
      default:
        return Icons.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    final verdictColor = _getVerdictColor();
    final isPasta = (analysis.foodName ?? '').toLowerCase().contains('pasta');

    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        title: const Text('Analysis Result'),
        elevation: 0,
        backgroundColor: const Color(0xFFFFC1CC),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () {
              // TODO: Share functionality
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Product image for pasta
            if (isPasta)
              Container(
                width: double.infinity,
                height: 180,
                color: const Color(0xFFFFC1CC),
                child: ClipRRect(
                  child: Image.asset(
                    'asset/kitchen poster for pasta lover minimal illustration art line art.jpeg',
                    fit: BoxFit.cover,
                    errorBuilder: (c, e, s) => Container(
                      color: const Color(0xFFFFEFF1),
                      child: const Icon(
                        Icons.fastfood,
                        size: 80,
                        color: Color(0xFFFFC1CC),
                      ),
                    ),
                  ),
                ),
              ),

            // Hero header with gradient
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    const Color(0xFFFFC1CC).withOpacity(0.3),
                    const Color(0xFFFFEFF1).withOpacity(0.2),
                  ],
                ),
              ),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Product name and brand
                    Text(
                      analysis.foodName ?? 'Unknown Food',
                      style: const TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF4C0004),
                        height: 1.2,
                      ),
                    ),
                    if (analysis.brand != null) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFC1CC).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          analysis.brand!,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFFAFA231),
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),

                    // Health Score Circular Indicator
                    Center(
                      child: _buildHealthScoreCircle(analysis.healthScore),
                    ),

                    const SizedBox(height: 16),

                    // Verdict badge
                    Center(
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 24,
                          vertical: 12,
                        ),
                        decoration: BoxDecoration(
                          color: verdictColor,
                          borderRadius: BorderRadius.circular(25),
                          boxShadow: [
                            BoxShadow(
                              color: verdictColor.withOpacity(0.3),
                              blurRadius: 12,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              _getVerdictIcon(),
                              color: Colors.white,
                              size: 24,
                            ),
                            const SizedBox(width: 12),
                            Text(
                              analysis.verdict.toUpperCase(),
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                                letterSpacing: 1.2,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Alerts
            if (analysis.alerts.isNotEmpty) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: _buildSection(
                  '⚠️ Alerts',
                  analysis.alerts,
                  AppColors.error,
                  Icons.error,
                ),
              ),
            ],

            // Warnings
            if (analysis.warnings.isNotEmpty) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: _buildSection(
                  '⚡ Warnings',
                  analysis.warnings,
                  AppColors.warning,
                  Icons.warning_amber,
                ),
              ),
            ],

            // Suggestions
            if (analysis.suggestions.isNotEmpty) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: _buildSection(
                  '💡 Suggestions',
                  analysis.suggestions,
                  AppColors.info,
                  Icons.lightbulb,
                ),
              ),
            ],

            // Nutrition Tips
            if (analysis.nutritionTips.isNotEmpty) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: _buildSection(
                  '🍎 Nutrition Tips',
                  analysis.nutritionTips,
                  AppColors.success,
                  Icons.tips_and_updates,
                ),
              ),
            ],

            // Ingredient Intelligence
            if (analysis.ingredientIntelligence != null) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: IngredientIntelligenceCard(
                  intelligence: analysis.ingredientIntelligence!,
                ),
              ),
            ],

            // Alternatives
            if (analysis.alternatives.isNotEmpty) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: _buildAlternativesSection(),
              ),
            ],

            // Detailed Nutrition with Visual Elements
            if (analysis.detailedNutrition != null) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child:
                    _buildEnhancedNutritionSection(analysis.detailedNutrition!),
              ),
            ],

            // Recipes
            if (analysis.recipes.isNotEmpty) ...[
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: _buildRecipesSection(),
              ),
            ],

            const SizedBox(height: 24),

            // Scan another button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.qr_code_scanner, size: 24),
                  label: const Text(
                    'Scan Another Product',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: 4,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildHealthScoreCircle(double score) {
    final color = score >= 70
        ? AppColors.success
        : score >= 40
            ? AppColors.warning
            : AppColors.error;

    return Container(
      width: 140,
      height: 140,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 120,
            height: 120,
            child: CircularProgressIndicator(
              value: score / 100,
              strokeWidth: 12,
              backgroundColor: color.withOpacity(0.2),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                score.toStringAsFixed(0),
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              Text(
                '/100',
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textLight,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEnhancedNutritionSection(DetailedNutrition nutrition) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.restaurant_menu,
                    color: AppColors.primary, size: 28),
                const SizedBox(width: 12),
                const Text(
                  'Nutrition Facts',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            // Data source badge
            if (nutrition.dataSources != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border:
                          Border.all(color: AppColors.primary.withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.verified,
                            size: 14, color: AppColors.primary),
                        const SizedBox(width: 4),
                        Text(
                          '${nutrition.dataSources}/4 sources',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (nutrition.dataConfidence != null) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _getConfidenceColor(nutrition.dataConfidence!)
                            .withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color:
                                _getConfidenceColor(nutrition.dataConfidence!)
                                    .withOpacity(0.3)),
                      ),
                      child: Text(
                        nutrition.dataConfidence!,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: _getConfidenceColor(nutrition.dataConfidence!),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ],
            if (nutrition.servingSize != null) ...[
              const SizedBox(height: 8),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.surfaceVariant,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'Per ${nutrition.servingSize}${nutrition.servingUnit ?? "g"}',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
            ],
            const SizedBox(height: 20),

            // Macronutrients with visual bars
            if (nutrition.calories != null)
              _buildNutrientBar(
                'Calories',
                nutrition.calories!,
                2000,
                'kcal',
                AppColors.primary,
              ),
            if (nutrition.proteinG != null)
              _buildNutrientBar(
                'Protein',
                nutrition.proteinG!,
                50,
                'g',
                AppColors.success,
              ),
            if (nutrition.carbsG != null)
              _buildNutrientBar(
                'Carbohydrates',
                nutrition.carbsG!,
                300,
                'g',
                AppColors.primary,
              ),
            if (nutrition.fatG != null)
              _buildNutrientBar(
                'Fat',
                nutrition.fatG!,
                70,
                'g',
                AppColors.warning,
              ),

            const Divider(height: 32),

            // Micronutrients grid
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                if (nutrition.sugarG != null)
                  _buildNutrientChip(
                      'Sugar', '${nutrition.sugarG}g', AppColors.error),
                if (nutrition.fiberG != null)
                  _buildNutrientChip(
                      'Fiber', '${nutrition.fiberG}g', AppColors.success),
                if (nutrition.saturatedFatG != null)
                  _buildNutrientChip('Sat. Fat', '${nutrition.saturatedFatG}g',
                      AppColors.warning),
                if (nutrition.sodiumMg != null)
                  _buildNutrientChip(
                      'Sodium', '${nutrition.sodiumMg}mg', AppColors.info),
              ],
            ),

            if (nutrition.allergens != null &&
                nutrition.allergens!.isNotEmpty) ...[
              const Divider(height: 32),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.error.withOpacity(0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.warning, color: AppColors.error, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Contains Allergens',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.error,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: nutrition.allergens!
                          .map(
                            (allergen) => Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: AppColors.error.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                allergen,
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.error,
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildNutrientBar(
    String label,
    double value,
    double dailyValue,
    String unit,
    Color color,
  ) {
    final percentage = (value / dailyValue * 100).clamp(0, 100);

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              Text(
                '$value$unit',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Stack(
            children: [
              Container(
                height: 8,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              FractionallySizedBox(
                widthFactor: percentage / 100,
                child: Container(
                  height: 8,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [color.withOpacity(0.7), color],
                    ),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '${percentage.toStringAsFixed(0)}% of daily value',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.textLight,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNutrientChip(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textLight,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecipesSection() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: const [
                Icon(Icons.menu_book, color: AppColors.primary, size: 28),
                SizedBox(width: 12),
                Text(
                  'Recipe Ideas',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...analysis.recipes.map((recipe) => Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        AppColors.surfaceVariant,
                        AppColors.surfaceVariant.withOpacity(0.5),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.restaurant,
                          color: AppColors.primary, size: 24),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              recipe.title,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              recipe.source,
                              style: TextStyle(
                                fontSize: 13,
                                color: AppColors.textLight,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios,
                          size: 16, color: AppColors.primary),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(
    String title,
    List<String> items,
    Color color,
    IconData icon,
  ) {
    return Card(
      color: Colors.white,
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
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: color, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...items.asMap().entries.map((entry) {
              int index = entry.key;
              String item = entry.value;
              return Padding(
                padding:
                    EdgeInsets.only(bottom: index == items.length - 1 ? 0 : 12),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      margin: const EdgeInsets.only(top: 6),
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        item,
                        style: const TextStyle(
                          fontSize: 15,
                          height: 1.4,
                          color: Color(0xFF333333),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildAlternativesSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: const [
                Icon(Icons.swap_horiz, color: AppColors.primary, size: 24),
                SizedBox(width: 8),
                Text(
                  '🔄 Healthier Alternatives',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...analysis.alternatives.map((alt) => Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceVariant,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.arrow_forward,
                        color: AppColors.primary,
                        size: 20,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              alt.name,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              alt.reason,
                              style: TextStyle(
                                fontSize: 14,
                                color: AppColors.textLight,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Color _getConfidenceColor(String confidence) {
    switch (confidence.toLowerCase()) {
      case 'high':
        return AppColors.success;
      case 'medium':
        return AppColors.warning;
      case 'low':
        return AppColors.error;
      default:
        return AppColors.info;
    }
  }
}
