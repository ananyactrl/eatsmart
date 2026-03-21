import 'package:flutter/material.dart';
import '../models/food_analysis.dart';
import '../theme.dart';

/// Ingredient Intelligence Card — shows decoded ingredient breakdown
/// with expandable details, concern-level badges, source citations,
/// and transparency score. Follows the "Don't trust us. Trust the sources." ethos.
class IngredientIntelligenceCard extends StatefulWidget {
  final IngredientIntelligence intelligence;

  const IngredientIntelligenceCard({Key? key, required this.intelligence})
      : super(key: key);

  @override
  State<IngredientIntelligenceCard> createState() =>
      _IngredientIntelligenceCardState();
}

class _IngredientIntelligenceCardState
    extends State<IngredientIntelligenceCard> {
  int? _expandedIndex;

  IngredientIntelligence get intel => widget.intelligence;

  // ---------------------------------------------------------------------------
  // Concern level helpers
  // ---------------------------------------------------------------------------

  Color _concernColor(String? level) {
    switch (level?.toLowerCase()) {
      case 'high':
        return const Color(0xFFE53935);
      case 'controversial':
        return const Color(0xFFFF6F00);
      case 'moderate':
        return const Color(0xFFFF9800);
      case 'low':
        return const Color(0xFF66BB6A);
      case 'none':
      default:
        return const Color(0xFF4CAF50);
    }
  }

  IconData _concernIcon(String? level) {
    switch (level?.toLowerCase()) {
      case 'high':
        return Icons.dangerous;
      case 'controversial':
        return Icons.help_outline;
      case 'moderate':
        return Icons.warning_amber;
      case 'low':
        return Icons.info_outline;
      case 'none':
      default:
        return Icons.check_circle_outline;
    }
  }

  String _concernLabel(String? level) {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'HIGH CONCERN';
      case 'controversial':
        return 'DEBATED';
      case 'moderate':
        return 'MODERATE';
      case 'low':
        return 'LOW';
      case 'none':
      default:
        return 'SAFE';
    }
  }

  String _categoryEmoji(String? category) {
    switch (category?.toLowerCase()) {
      case 'preservative':
        return '🧴';
      case 'colorant':
        return '🎨';
      case 'sweetener':
        return '🍬';
      case 'emulsifier':
        return '🔗';
      case 'stabilizer':
        return '⚓';
      case 'thickener':
        return '🫗';
      case 'flavor_enhancer':
        return '👅';
      case 'antioxidant':
        return '🛡️';
      case 'acidity_regulator':
        return '⚗️';
      case 'sugar':
        return '🍯';
      case 'fat_oil':
        return '🫒';
      case 'grain_flour':
        return '🌾';
      case 'vitamin_mineral':
        return '💊';
      case 'anti_caking':
        return '🧱';
      case 'humectant':
        return '💧';
      case 'natural':
        return '🌿';
      default:
        return '🔬';
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          _buildHeader(),

          // Stats row
          _buildStatsRow(),

          // Overall concern badge
          _buildOverallConcern(),

          // Warnings (if any)
          if (intel.warnings.isNotEmpty) _buildWarningsList(),

          // Decoded ingredients list
          _buildIngredientsList(),

          // Disclaimer
          _buildDisclaimer(),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Header with transparency score
  // ---------------------------------------------------------------------------

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primary.withOpacity(0.08),
            AppColors.primary.withOpacity(0.02),
          ],
        ),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Row(
        children: [
          // Icon
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.science, color: AppColors.primary, size: 28),
          ),
          const SizedBox(width: 14),

          // Title + subtitle
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Ingredient Intelligence',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Decoded from public regulatory sources',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppColors.textLight,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ),

          // Transparency score circle
          _buildTransparencyBadge(),
        ],
      ),
    );
  }

  Widget _buildTransparencyBadge() {
    final score = intel.transparencyScore;
    final color = score >= 80
        ? const Color(0xFF4CAF50)
        : score >= 50
            ? const Color(0xFFFF9800)
            : const Color(0xFFE53935);

    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.25),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 48,
            height: 48,
            child: CircularProgressIndicator(
              value: score / 100,
              strokeWidth: 4,
              backgroundColor: color.withOpacity(0.15),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${score.toStringAsFixed(0)}%',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              Text(
                'ID\'d',
                style: TextStyle(
                  fontSize: 8,
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

  // ---------------------------------------------------------------------------
  // Stats row
  // ---------------------------------------------------------------------------

  Widget _buildStatsRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          _buildStatChip(
            Icons.checklist,
            '${intel.ingredientsIdentified}/${intel.totalIngredients}',
            'identified',
            AppColors.primary,
          ),
          const SizedBox(width: 8),
          _buildStatChip(
            Icons.source,
            '${intel.sourcesCited}',
            'sources',
            AppColors.secondary,
          ),
          if (intel.ingredientsUnknown > 0) ...[
            const SizedBox(width: 8),
            _buildStatChip(
              Icons.help_outline,
              '${intel.ingredientsUnknown}',
              'unknown',
              const Color(0xFFFF9800),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatChip(
      IconData icon, String value, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 4),
            Flexible(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: 10,
                      color: color.withOpacity(0.8),
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Overall concern
  // ---------------------------------------------------------------------------

  Widget _buildOverallConcern() {
    final color = _concernColor(intel.overallConcern);
    final icon = _concernIcon(intel.overallConcern);
    final label = _concernLabel(intel.overallConcern);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 10),
            Text(
              'Overall: $label',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const Spacer(),
            if (intel.summary.isNotEmpty)
              Flexible(
                child: Text(
                  intel.summary,
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.textLight,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.right,
                ),
              ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Warnings
  // ---------------------------------------------------------------------------

  Widget _buildWarningsList() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFFE53935).withOpacity(0.06),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFFE53935).withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.warning, color: Color(0xFFE53935), size: 18),
                SizedBox(width: 6),
                Text(
                  'Flagged Ingredients',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFE53935),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ...intel.warnings.map(
              (w) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('• ', style: TextStyle(color: Color(0xFFE53935))),
                    Expanded(
                      child: RichText(
                        text: TextSpan(
                          style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
                          children: [
                            TextSpan(
                              text: '${w.ingredient}: ',
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            TextSpan(text: w.concern),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Decoded ingredients list (expandable)
  // ---------------------------------------------------------------------------

  Widget _buildIngredientsList() {
    final ingredients = List<DecodedIngredient>.from(intel.decodedIngredients);
    // Sort by position (most by weight first)
    ingredients.sort((a, b) => a.position.compareTo(b.position));

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.list_alt, size: 18, color: AppColors.primary),
              const SizedBox(width: 6),
              const Text(
                'All Ingredients',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const Spacer(),
              Text(
                'Tap to expand',
                style: TextStyle(
                  fontSize: 11,
                  color: AppColors.textLight,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...ingredients.asMap().entries.map((entry) {
            final idx = entry.key;
            final ing = entry.value;
            final isExpanded = _expandedIndex == idx;
            return _buildIngredientTile(ing, idx, isExpanded);
          }),
        ],
      ),
    );
  }

  Widget _buildIngredientTile(
      DecodedIngredient ing, int index, bool isExpanded) {
    final color = _concernColor(ing.concernLevel);
    final emoji = _categoryEmoji(ing.category);

    return GestureDetector(
      onTap: () {
        setState(() {
          _expandedIndex = isExpanded ? null : index;
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 6),
        decoration: BoxDecoration(
          color: isExpanded
              ? color.withOpacity(0.06)
              : AppColors.surfaceVariant.withOpacity(0.5),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isExpanded ? color.withOpacity(0.3) : Colors.transparent,
          ),
        ),
        child: Column(
          children: [
            // Collapsed row
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  // Position number
                  Container(
                    width: 24,
                    height: 24,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '${ing.position}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Category emoji
                  Text(emoji, style: const TextStyle(fontSize: 16)),
                  const SizedBox(width: 8),

                  // Name
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          ing.name,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        if (ing.eNumber != null)
                          Text(
                            ing.eNumber!,
                            style: TextStyle(
                              fontSize: 11,
                              color: AppColors.textLight,
                            ),
                          ),
                      ],
                    ),
                  ),

                  // Concern badge
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 7,
                          height: 7,
                          decoration: BoxDecoration(
                            color: color,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          _concernLabel(ing.concernLevel),
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(width: 4),
                  Icon(
                    isExpanded
                        ? Icons.keyboard_arrow_up
                        : Icons.keyboard_arrow_down,
                    size: 20,
                    color: AppColors.textLight,
                  ),
                ],
              ),
            ),

            // Expanded details
            if (isExpanded) _buildExpandedDetails(ing),
          ],
        ),
      ),
    );
  }

  Widget _buildExpandedDetails(DecodedIngredient ing) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Divider(height: 0),
          const SizedBox(height: 10),

          // Plain explanation
          if (ing.plainExplanation.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                ing.plainExplanation,
                style: const TextStyle(
                  fontSize: 13,
                  height: 1.4,
                  color: AppColors.textPrimary,
                ),
              ),
            ),

          // Health effects
          if (ing.healthEffects.isNotEmpty) ...[
            const SizedBox(height: 8),
            const Text(
              'Health Effects',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: ing.healthEffects
                  .map((e) => Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFF9800).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          e,
                          style: const TextStyle(
                            fontSize: 11,
                            color: Color(0xFFE65100),
                          ),
                        ),
                      ))
                  .toList(),
            ),
          ],

          // ADI
          if (ing.adi != null) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.scale, size: 14, color: AppColors.textLight),
                const SizedBox(width: 4),
                Text(
                  'ADI: ${ing.adi}',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppColors.textLight,
                  ),
                ),
              ],
            ),
          ],

          // Regulatory status
          if (ing.regulatoryStatus.isNotEmpty) ...[
            const SizedBox(height: 8),
            const Text(
              'Regulatory Status',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 4),
            ...ing.regulatoryStatus
                .take(3) // Show top 3 regulators
                .map((rs) => Padding(
                      padding: const EdgeInsets.only(bottom: 3),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              rs['body']?.toString() ?? '',
                              style: const TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primary,
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              rs['status']?.toString() ?? '',
                              style: TextStyle(
                                fontSize: 11,
                                color: AppColors.textLight,
                              ),
                            ),
                          ),
                          if (rs['max_limit'] != null)
                            Text(
                              rs['max_limit'].toString(),
                              style: TextStyle(
                                fontSize: 10,
                                color: AppColors.textLight,
                              ),
                            ),
                        ],
                      ),
                    )),
          ],

          // Sources
          if (ing.sources.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.verified, size: 12, color: AppColors.secondary),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    'Sources: ${ing.sources.map((s) => s['body'] ?? s['source'] ?? '').where((s) => s.isNotEmpty).join(', ')}',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: AppColors.secondary,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],

          // "Not in knowledge base" indicator
          if (!ing.known) ...[
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFFF9800).withOpacity(0.08),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(
                    color: const Color(0xFFFF9800).withOpacity(0.2)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.auto_awesome, size: 12, color: Color(0xFFFF9800)),
                  SizedBox(width: 4),
                  Text(
                    'Info retrieved via RAG search',
                    style: TextStyle(
                      fontSize: 10,
                      color: Color(0xFFE65100),
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Disclaimer
  // ---------------------------------------------------------------------------

  Widget _buildDisclaimer() {
    if (intel.disclaimer.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: AppColors.textLight.withOpacity(0.06),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.info_outline, size: 14, color: AppColors.textLight),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                intel.disclaimer,
                style: TextStyle(
                  fontSize: 10,
                  color: AppColors.textLight,
                  height: 1.3,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
