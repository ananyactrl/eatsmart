import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'product_detail_screen.dart';
import 'scanner_screen.dart';
import '../widgets/bottom_nav.dart';
import 'contact_nutritionist_screen.dart';
import 'profile_form_screen.dart';

Widget _categoryChip(String label) {
  return Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(20),
    ),
    child: Row(
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: const Color(0xFFFFEFF1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(Icons.circle, size: 16, color: Colors.pinkAccent),
        ),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(color: Colors.black87)),
      ],
    ),
  );
}

class ProductListScreen extends StatelessWidget {
  const ProductListScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final products = [
      {
        'name': 'Millet Noodles',
        'note': 'Wholesome millet noodles',
        'image': 'asset/milet.jpeg',
        'price': '\u20B9 40'
      },
      {
        'name': 'Chef Urbano',
        'note': 'Multigrain Pasta',
        'image': 'asset/WhatsApp Image 2026-02-07 at 22.15.10.jpeg',
        'price': '\u20B9 100'
      },
      {
        'name': 'Millet',
        'note': 'Millet Instant Noodles',
        'image': 'asset/WhatsApp Image 2026-02-07 at 22.15.22.jpeg',
        'price': '\u20B9 40'
      },
      {
        'name': 'Mixed Snack',
        'note': 'High-protein snack',
        'image': 'asset/milet.jpeg',
        'price': '\u20B9 19.50'
      },
      {
        'name': 'Gala Multigrain Cookies',
        'note': 'Multigrain baked cookies',
        'image': 'asset/WhatsApp Image 2026-02-07 at 22.29.04.jpeg',
        'price': '\u20B9 85'
      },
      {
        'name': 'Millete Amma Jowar Bakhri',
        'note': 'Traditional jowar flatbread',
        'image': 'asset/WhatsApp Image 2026-02-07 at 22.29.19.jpeg',
        'price': '\u20B9 25'
      },
      {
        'name': 'Wicked Good Fusilli Pasta',
        'note': 'Artisan fusilli pasta',
        'image': 'asset/WhatsApp Image 2026-02-07 at 22.29.31.jpeg',
        'price': '\u20B9 120'
      }
    ];

    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              // Header with search and categories
              Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: const Color(0xFFFFC1CC),
                  borderRadius: BorderRadius.circular(16),
                ),
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: TextField(
                              decoration: InputDecoration(
                                prefixIcon: const Icon(Icons.search,
                                    color: Colors.black54),
                                hintText: 'Search product name',
                                border: InputBorder.none,
                                contentPadding:
                                    const EdgeInsets.symmetric(vertical: 14),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white70,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          padding: const EdgeInsets.all(8),
                          child: const Icon(Icons.more_horiz,
                              color: Colors.black54),
                        )
                      ],
                    ),
                    const SizedBox(height: 12),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          _categoryChip('Pasta'),
                          const SizedBox(width: 8),
                          _categoryChip('Chocolate'),
                          const SizedBox(width: 8),
                          _categoryChip('Flour'),
                          const SizedBox(width: 8),
                          _categoryChip('Snacks'),
                          const SizedBox(width: 8),
                          _categoryChip('Drinks'),
                        ],
                      ),
                    )
                  ],
                ),
              ),
              const SizedBox(height: 12),
              // Product list
              Expanded(
                child: ListView.separated(
                  itemCount: products.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final p = products[index];
                    return GestureDetector(
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => ProductDetailScreen(
                                item: Map<String, String>.from(p))),
                      ),
                      child: Container(
                        height: 110,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Padding(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 14.0, vertical: 10),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(p['name']!,
                                        style: GoogleFonts.youngSerif(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w700)),
                                    const SizedBox(height: 6),
                                    Text(p['note']!,
                                        style: const TextStyle(
                                            color: Colors.black54)),
                                    const SizedBox(height: 8),
                                    Text(p['price']!,
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w700)),
                                  ],
                                ),
                              ),
                            ),
                            ClipRRect(
                              borderRadius: const BorderRadius.only(
                                  topRight: Radius.circular(14),
                                  bottomRight: Radius.circular(14)),
                              child: Image.asset(
                                p['image']!,
                                width: 110,
                                height: 110,
                                fit: BoxFit.cover,
                                errorBuilder: (c, e, s) => Container(
                                  width: 110,
                                  height: 110,
                                  color: const Color(0xFFFFEFF1),
                                  child: const Icon(Icons.image_not_supported,
                                      color: Colors.black26),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: AppBottomNav(
        currentIndex: 0,
        onTapOverride: (i) {
          switch (i) {
            case 0:
              // already home - do nothing
              break;
            case 1:
              Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const ScannerScreen()));
              break;
            case 2:
              Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const ContactNutritionistScreen()));
              break;
            case 4:
              Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const ProfileFormScreen()));
              break;
            default:
              Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const ProductListScreen()));
          }
        },
      ),
    );
  }
}
