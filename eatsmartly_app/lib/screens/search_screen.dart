import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/food_analysis.dart';
import '../theme.dart';
import 'result_screen.dart';

class SearchScreen extends StatefulWidget {
  final String? initialQuery;

  const SearchScreen({Key? key, this.initialQuery}) : super(key: key);

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final EatSmartlyAPI api = EatSmartlyAPI();
  final String userId = 'test_user';
  late TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
    // If an initial query is provided, auto-search for it
    if (widget.initialQuery != null && widget.initialQuery!.isNotEmpty) {
      _searchController.text = widget.initialQuery!;
      Future.delayed(const Duration(milliseconds: 500), () {
        _performSearch(widget.initialQuery!);
      });
    }
  }

  bool isSearching = false;
  List<Map<String, dynamic>> searchResults = [];
  String? error;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _performSearch(String query) async {
    if (query.trim().isEmpty) {
      setState(() {
        searchResults = [];
        error = null;
      });
      return;
    }

    if (!mounted) return;
    setState(() {
      isSearching = true;
      error = null;
    });

    try {
      // Use new comprehensive search that includes local database
      final result = await api.searchProducts(query, limit: 20);

      if (!mounted) return;
      setState(() {
        searchResults =
            List<Map<String, dynamic>>.from(result['results'] ?? []);
        isSearching = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = e.toString().replaceAll('Exception: ', '');
        isSearching = false;
        searchResults = [];
      });
    }
  }

  Future<void> _analyzeProduct(Map<String, dynamic> product) async {
    try {
      final String productName = product['name'] ?? 'Unknown';
      final String? barcode = product['barcode'];
      final dynamic productId = product['id'];

      FoodAnalysis analysis;

      // Try to analyze using barcode first
      if (barcode != null && barcode.toString().isNotEmpty) {
        analysis = await api.analyzeBarcode(
            barcode: barcode, userId: userId, detailed: true);
      } else if (productId != null) {
        // Use product ID (can be string or int)
        analysis = await api.analyzeProduct(
            productId: productId is int
                ? productId
                : int.tryParse(productId.toString()),
            userId: userId,
            detailed: true);
      } else {
        // Use product name
        analysis = await api.analyzeProduct(
            productName: productName, userId: userId, detailed: true);
      }

      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) =>
              ResultScreen(analysis: analysis, productImage: product),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error loading product details: ${e.toString()}'),
          backgroundColor: const Color(0xFFE53935),
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        title: const Text('Search Results'),
        elevation: 0,
        backgroundColor: const Color(0xFFFFC1CC),
      ),
      body: Column(
        children: [
          // Search bar with pink theme
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFFFC1CC),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: TextField(
              controller: _searchController,
              style: const TextStyle(color: Colors.black87),
              decoration: InputDecoration(
                hintText: 'Search by product name',
                hintStyle: TextStyle(color: Colors.black.withOpacity(0.5)),
                prefixIcon: const Icon(Icons.search, color: Colors.black54),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, color: Colors.black54),
                        onPressed: () {
                          _searchController.clear();
                          _performSearch('');
                        },
                      )
                    : null,
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(30),
                  borderSide: BorderSide.none,
                ),
              ),
              onChanged: (value) {
                setState(() {});
                Future.delayed(const Duration(milliseconds: 500), () {
                  if (_searchController.text == value) {
                    _performSearch(value);
                  }
                });
              },
              onSubmitted: _performSearch,
            ),
          ),

          // Search results
          Expanded(
            child: _buildSearchResults(),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchResults() {
    if (isSearching) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: AppColors.primary),
            const SizedBox(height: 16),
            Text(
              'Searching...',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 16,
              ),
            ),
          ],
        ),
      );
    }

    if (error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.error_outline, size: 64, color: AppColors.error),
              const SizedBox(height: 16),
              Text(
                error!,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.error,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => _performSearch(_searchController.text),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (searchResults.isEmpty && _searchController.text.isNotEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.search_off, size: 64, color: AppColors.textLight),
              const SizedBox(height: 16),
              Text(
                'No products found for "${_searchController.text}"',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Try searching for common products like:\n• Amul Butter\n• Parle-G\n• Maggi Noodles',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.textLight,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (searchResults.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.restaurant_menu, size: 64, color: AppColors.primary),
              const SizedBox(height: 16),
              Text(
                'Search for food products',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Type a product name to get started',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: searchResults.length,
      itemBuilder: (context, index) {
        final product = searchResults[index];
        return _buildProductCard(product);
      },
    );
  }

  Widget _buildProductCard(Map<String, dynamic> product) {
    final String name = product['name'] ?? 'Unknown Product';
    final String? brand = product['brand'];
    final double? calories = product['calories']?.toDouble();
    final String? source = product['source'];

    // Check if it's a pasta product - include all pasta types
    final String nameLower = name.toLowerCase();
    final String brandLower = brand?.toLowerCase() ?? '';
    final bool isPasta = nameLower.contains('pasta') ||
        nameLower.contains('spaghetti') ||
        nameLower.contains('penne') ||
        nameLower.contains('fusilli') ||
        nameLower.contains('rigate') ||
        nameLower.contains('noodles') ||
        nameLower.contains('macaroni') ||
        brandLower.contains('pasta') ||
        brandLower.contains('barilla') ||
        brandLower.contains('fortune');

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: Colors.white,
      child: InkWell(
        onTap: () => _analyzeProduct(product),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Product icon/image box
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: const Color(0xFFFFC1CC),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: const Color(0xFFFFEFF1),
                    width: 2,
                  ),
                ),
                child: isPasta
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: Image.asset(
                          'asset/kitchen poster for pasta lover minimal illustration art line art.jpeg',
                          fit: BoxFit.cover,
                          errorBuilder: (c, e, s) => Icon(
                            Icons.fastfood,
                            color: Colors.white,
                            size: 28,
                          ),
                        ),
                      )
                    : Icon(
                        Icons.fastfood,
                        color: Colors.white,
                        size: 28,
                      ),
              ),
              const SizedBox(width: 16),

              // Product info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF4C0004),
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (brand != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        brand,
                        style: const TextStyle(
                          fontSize: 13,
                          color: Color(0xFFAFA231),
                        ),
                      ),
                    ],
                    const SizedBox(height: 6),
                    if (calories != null)
                      Text(
                        '${calories.toStringAsFixed(0)} cal',
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF4C0004),
                        ),
                      ),
                    if (source != null)
                      Text(
                        'From: $source',
                        style: const TextStyle(
                          fontSize: 11,
                          color: Colors.grey,
                        ),
                      ),
                  ],
                ),
              ),
              // Right arrow indicator
              Icon(
                Icons.chevron_right,
                color: const Color(0xFFAFA231),
                size: 28,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
