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

  bool isSearching = false;
  List<Map<String, dynamic>> searchResults = [];
  String? error;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
    if (widget.initialQuery != null && widget.initialQuery!.isNotEmpty) {
      _searchController.text = widget.initialQuery!;
      Future.delayed(const Duration(milliseconds: 500), () => _performSearch(widget.initialQuery!));
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _performSearch(String query) async {
    if (query.trim().isEmpty) {
      setState(() { searchResults = []; error = null; });
      return;
    }
    if (!mounted) return;
    setState(() { isSearching = true; error = null; });
    try {
      final result = await api.searchProducts(query, limit: 20);
      if (!mounted) return;
      setState(() { searchResults = List<Map<String, dynamic>>.from(result['results'] ?? []); isSearching = false; });
    } catch (e) {
      if (!mounted) return;
      setState(() { error = e.toString().replaceAll('Exception: ', ''); isSearching = false; searchResults = []; });
    }
  }

  Future<void> _analyzeProduct(Map<String, dynamic> product) async {
    try {
      final String productName = product['name'] ?? 'Unknown';
      final String? barcode = product['barcode'];
      final dynamic productId = product['id'];
      FoodAnalysis analysis;
      if (barcode != null && barcode.toString().isNotEmpty) {
        analysis = await api.analyzeBarcode(barcode: barcode, userId: userId, detailed: true);
      } else if (productId != null) {
        analysis = await api.analyzeProduct(
          productId: productId is int ? productId : int.tryParse(productId.toString()),
          userId: userId, detailed: true);
      } else {
        analysis = await api.analyzeProduct(productName: productName, userId: userId, detailed: true);
      }
      if (!mounted) return;
      Navigator.push(context, MaterialPageRoute(builder: (_) => ResultScreen(analysis: analysis, productImage: product)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Error: ${e.toString()}'),
        backgroundColor: AppColors.error,
      ));
    }
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
                  const Text('Search Products 🔍', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: Colors.white)),
                  const SizedBox(height: 4),
                  const Text('Find and analyze any food product', style: TextStyle(color: Colors.white70, fontSize: 13)),
                  const SizedBox(height: 14),
                  Container(
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
                    child: TextField(
                      controller: _searchController,
                      decoration: InputDecoration(
                        hintText: 'Search by product name...',
                        hintStyle: const TextStyle(color: AppColors.muted, fontSize: 14),
                        prefixIcon: const Icon(Icons.search, color: AppColors.muted),
                        suffixIcon: _searchController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear, color: AppColors.muted),
                                onPressed: () { _searchController.clear(); _performSearch(''); setState(() {}); },
                              )
                            : null,
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        filled: false,
                      ),
                      onChanged: (value) {
                        setState(() {});
                        Future.delayed(const Duration(milliseconds: 500), () {
                          if (_searchController.text == value) _performSearch(value);
                        });
                      },
                      onSubmitted: _performSearch,
                    ),
                  ),
                ],
              ),
            ),
            Expanded(child: _buildResults()),
          ],
        ),
      ),
    );
  }

  Widget _buildResults() {
    if (isSearching) {
      return const Center(child: CircularProgressIndicator(color: AppColors.rose));
    }
    if (error != null) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.error_outline, size: 56, color: AppColors.error),
          const SizedBox(height: 12),
          Text(error!, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.error)),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: () => _performSearch(_searchController.text), child: const Text('Retry')),
        ]),
      ));
    }
    if (searchResults.isEmpty && _searchController.text.isNotEmpty) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(width: 72, height: 72, decoration: const BoxDecoration(color: AppColors.blush, shape: BoxShape.circle),
            child: const Icon(Icons.search_off_rounded, size: 32, color: AppColors.dark)),
          const SizedBox(height: 16),
          Text('No results for "${_searchController.text}"', textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.dark)),
          const SizedBox(height: 8),
          const Text('Try: Amul Butter, Parle-G, Maggi Noodles', textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.muted, fontSize: 13)),
        ]),
      ));
    }
    if (searchResults.isEmpty) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(width: 80, height: 80, decoration: const BoxDecoration(color: AppColors.blush, shape: BoxShape.circle),
            child: const Icon(Icons.search_rounded, size: 36, color: AppColors.dark)),
          const SizedBox(height: 16),
          const Text('Search for food products', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.dark)),
          const SizedBox(height: 6),
          const Text('Type a product name to get started', style: TextStyle(color: AppColors.muted, fontSize: 14)),
        ]),
      ));
    }
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      itemCount: searchResults.length,
      itemBuilder: (context, index) => _buildProductCard(searchResults[index]),
    );
  }

  Widget _buildProductCard(Map<String, dynamic> product) {
    final String name = product['name'] ?? 'Unknown Product';
    final String? brand = product['brand'];
    final double? calories = product['calories']?.toDouble();
    final String? source = product['source'];

    return GestureDetector(
      onTap: () => _analyzeProduct(product),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 8)],
        ),
        child: Row(
          children: [
            Container(
              width: 52, height: 52,
              decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(14)),
              child: const Icon(Icons.fastfood_rounded, size: 24, color: AppColors.dark),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.dark),
                  maxLines: 2, overflow: TextOverflow.ellipsis),
                if (brand != null) ...[
                  const SizedBox(height: 2),
                  Text(brand, style: const TextStyle(fontSize: 12, color: AppColors.muted)),
                ],
                if (calories != null) ...[
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(color: AppColors.blush, borderRadius: BorderRadius.circular(8)),
                    child: Text('${calories.toStringAsFixed(0)} kcal',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.rose)),
                  ),
                ],
                if (source != null)
                  Text('via $source', style: const TextStyle(fontSize: 10, color: AppColors.muted)),
              ]),
            ),
            const Icon(Icons.chevron_right_rounded, color: AppColors.coral, size: 24),
          ],
        ),
      ),
    );
  }
}
