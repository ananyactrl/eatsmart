import 'package:flutter/material.dart';
import '../theme.dart';

class ProductDetailScreen extends StatelessWidget {
  final Map<String, String> item;
  const ProductDetailScreen({Key? key, required this.item}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final name = item['name'] ?? 'Product';
    final note = item['note'] ?? '';
    final image = item['image'] ?? '';
    final price = item['price'] ?? '₹0';

    final nutrition = {
      'Calories': '220 kcal',
      'Protein': '7 g',
      'Fat': '3 g',
      'Carbs': '40 g',
      'Fiber': '4 g',
    };

    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Hero image card
              Stack(
                children: [
                  Container(
                    height: 280,
                    width: double.infinity,
                    color: AppColors.blush,
                    child: Image.asset(image, fit: BoxFit.cover,
                      errorBuilder: (c, e, s) => const Center(child: Text('🍱', style: TextStyle(fontSize: 80)))),
                  ),
                  Positioned(
                    top: 16, left: 16,
                    child: GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(color: Colors.white, shape: BoxShape.circle,
                          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 8)]),
                        child: const Icon(Icons.arrow_back_rounded, color: AppColors.dark, size: 20),
                      ),
                    ),
                  ),
                ],
              ),

              Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Name + price row
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(name, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppColors.dark)),
                            const SizedBox(height: 4),
                            Text(note, style: const TextStyle(color: AppColors.muted, fontSize: 14)),
                          ],
                        )),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(12)),
                          child: Text(price, style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.rose, fontSize: 16)),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    // About section
                    const Text('About', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.dark)),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(color: AppColors.white, borderRadius: BorderRadius.circular(16),
                        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 8)]),
                      child: const Text(
                        'Made from whole-grain millets — a nutritious alternative to refined wheat. Provides more protein and fiber with a lower glycemic response.',
                        style: TextStyle(color: AppColors.muted, fontSize: 14, height: 1.5),
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Nutrition facts
                    const Text('Nutrition Facts', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.dark)),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(color: AppColors.white, borderRadius: BorderRadius.circular(16),
                        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 8)]),
                      child: Column(
                        children: nutrition.entries.map((e) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Row(
                            children: [
                              Text(e.key, style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.dark)),
                              const Spacer(),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(8)),
                                child: Text(e.value, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.rose, fontSize: 13)),
                              ),
                            ],
                          ),
                        )).toList(),
                      ),
                    ),

                    const SizedBox(height: 24),

                    // Add to bag button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Added to bag'), backgroundColor: AppColors.success)),
                        icon: const Icon(Icons.shopping_bag_outlined),
                        label: const Text('Add to Bag'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.rose, foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
