import 'package:flutter/material.dart';
import '../theme.dart';
import 'product_detail_screen.dart';
import 'search_screen.dart';

class ProductListScreen extends StatefulWidget {
  const ProductListScreen({Key? key}) : super(key: key);

  @override
  State<ProductListScreen> createState() => _ProductListScreenState();
}

class _ProductListScreenState extends State<ProductListScreen> {
  late TextEditingController _searchController;
  String _selectedCategory = 'All';

  final List<String> _categories = ['All', 'Pasta', 'Snacks', 'Flour', 'Drinks', 'Chocolate'];

  final List<Map<String, String>> _products = [
    {'name': 'Millet Noodles', 'note': 'Wholesome millet noodles', 'image': 'asset/milet.jpeg', 'price': '₹40', 'category': 'Pasta'},
    {'name': 'Chef Urbano', 'note': 'Multigrain Pasta', 'image': 'asset/WhatsApp Image 2026-02-07 at 22.15.10.jpeg', 'price': '₹100', 'category': 'Pasta'},
    {'name': 'Millet Instant Noodles', 'note': 'Millet Instant Noodles', 'image': 'asset/WhatsApp Image 2026-02-07 at 22.15.22.jpeg', 'price': '₹40', 'category': 'Pasta'},
    {'name': 'Mixed Snack', 'note': 'High-protein snack', 'image': 'asset/milet.jpeg', 'price': '₹19.50', 'category': 'Snacks'},
    {'name': 'Gala Multigrain Cookies', 'note': 'Multigrain baked cookies', 'image': 'asset/WhatsApp Image 2026-02-07 at 22.29.04.jpeg', 'price': '₹85', 'category': 'Snacks'},
    {'name': 'Jowar Bakhri', 'note': 'Traditional jowar flatbread', 'image': 'asset/WhatsApp Image 2026-02-07 at 22.29.19.jpeg', 'price': '₹25', 'category': 'Flour'},
    {'name': 'Wicked Good Fusilli', 'note': 'Artisan fusilli pasta', 'image': 'asset/WhatsApp Image 2026-02-07 at 22.29.31.jpeg', 'price': '₹120', 'category': 'Pasta'},
  ];

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<Map<String, String>> get _filtered {
    return _products.where((p) {
      final matchCat = _selectedCategory == 'All' || p['category'] == _selectedCategory;
      final q = _searchController.text.toLowerCase();
      final matchQ = q.isEmpty || (p['name']?.toLowerCase().contains(q) ?? false);
      return matchCat && matchQ;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(color: AppColors.rose, borderRadius: BorderRadius.circular(24)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Smart Products 🛒', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: Colors.white)),
                  const SizedBox(height: 4),
                  const Text('Healthy picks, analyzed for you', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 14),
                  // Search bar
                  GestureDetector(
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SearchScreen())),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
                      child: Row(
                        children: const [
                          Icon(Icons.search, color: AppColors.muted, size: 20),
                          SizedBox(width: 10),
                          Text('Search any product...', style: TextStyle(color: AppColors.muted, fontSize: 14)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Category chips
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: _categories.map((cat) {
                        final isSelected = _selectedCategory == cat;
                        return GestureDetector(
                          onTap: () => setState(() => _selectedCategory = cat),
                          child: Container(
                            margin: const EdgeInsets.only(right: 8),
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                            decoration: BoxDecoration(
                              color: isSelected ? Colors.white : Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(cat, style: TextStyle(
                              color: isSelected ? AppColors.rose : Colors.white,
                              fontWeight: FontWeight.w600, fontSize: 13,
                            )),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            // Product list
            Expanded(
              child: _filtered.isEmpty
                  ? const Center(child: Text('No products found', style: TextStyle(color: AppColors.muted)))
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                      itemCount: _filtered.length,
                      itemBuilder: (context, index) => _buildProductCard(_filtered[index]),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProductCard(Map<String, String> p) {
    return GestureDetector(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ProductDetailScreen(item: p))),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        height: 100,
        decoration: BoxDecoration(color: AppColors.white, borderRadius: BorderRadius.circular(18),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 8)]),
        child: Row(
          children: [
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(p['name']!, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.dark),
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 4),
                    Text(p['note']!, style: const TextStyle(color: AppColors.muted, fontSize: 12), maxLines: 1),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(8)),
                      child: Text(p['price']!, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.rose, fontSize: 12)),
                    ),
                  ],
                ),
              ),
            ),
            ClipRRect(
              borderRadius: const BorderRadius.only(topRight: Radius.circular(18), bottomRight: Radius.circular(18)),
              child: Image.asset(p['image']!, width: 100, height: 100, fit: BoxFit.cover,
                errorBuilder: (c, e, s) => Container(width: 100, height: 100, color: AppColors.blush,
                  child: const Icon(Icons.image_not_supported, color: AppColors.muted))),
            ),
          ],
        ),
      ),
    );
  }
}
