import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'product_detail_screen.dart';
import 'product_list_screen.dart';
import 'scanner_screen.dart';
import '../widgets/bottom_nav.dart';
import 'contact_nutritionist_screen.dart';
import 'profile_form_screen.dart';

class ProfileDetailsScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  const ProfileDetailsScreen({Key? key, required this.profile})
      : super(key: key);

  @override
  State<ProfileDetailsScreen> createState() => _ProfileDetailsScreenState();
}

class _ProfileDetailsScreenState extends State<ProfileDetailsScreen> {
  final TextEditingController _proteinController = TextEditingController();
  final TextEditingController _targetWeightController = TextEditingController();
  double _dailyCalories = 2000;
  String _nutrientFocus = 'Protein';

  @override
  void initState() {
    super.initState();
    // Set some sensible defaults using provided profile
    final profile = widget.profile;
    if ((profile['focus'] ?? '').toString().toLowerCase().contains('weight')) {
      _proteinController.text = '1.8'; // g/kg sample
    } else {
      _proteinController.text = '1.2';
    }
    _targetWeightController.text = profile['weight'] ?? '';
  }

  @override
  void dispose() {
    _proteinController.dispose();
    _targetWeightController.dispose();
    super.dispose();
  }

  List<Map<String, String>> suggestedItemsFor(String focus) {
    switch (focus) {
      case 'Protein':
        return [
          {'name': 'Millet Noodles', 'note': 'Rich in protein & omega-3'},
          {'name': 'Greek Yogurt', 'note': 'High protein, low fat'},
          {'name': 'Chicken Breast', 'note': 'Lean protein source'},
          {'name': 'Lentils', 'note': 'Plant protein & fiber'},
        ];
      case 'Fat':
        return [
          {'name': 'Avocado Toast', 'note': 'Healthy monounsaturated fats'},
          {'name': 'Salmon Bowl', 'note': 'Good fats & protein'},
          {'name': 'Olive Oil Salad', 'note': 'Mediterranean fats'},
        ];
      case 'Carbs':
        return [
          {'name': 'Quinoa Salad', 'note': 'Complex carbs & protein'},
          {'name': 'Sweet Potato', 'note': 'Slow-release carbs'},
          {'name': 'Oatmeal', 'note': 'Fiber-rich breakfast'},
        ];
      case 'Vitamins':
        return [
          {'name': 'Mixed Berries', 'note': 'Vitamin C & antioxidants'},
          {'name': 'Spinach Salad', 'note': 'Iron & Vitamin K'},
          {'name': 'Citrus Bowl', 'note': 'Vitamin C boost'},
        ];
      default:
        return [
          {'name': 'Eggs', 'note': 'Complete protein'},
          {'name': 'Chicken', 'note': 'Lean protein'},
        ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = widget.profile;
    final allergies = List<String>.from(profile['allergies'] ?? []);
    final focus = profile['focus'] ?? '';

    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
        title: Text('Personalize plan',
            style: GoogleFonts.youngSerif(color: Colors.black87)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Summary',
                style: GoogleFonts.youngSerif(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Card(
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Name: ${profile['first_name'] ?? ''}'),
                    const SizedBox(height: 6),
                    Text('Age: ${profile['age'] ?? ''}'),
                    const SizedBox(height: 6),
                    Text('Gender: ${profile['gender'] ?? ''}'),
                    const SizedBox(height: 6),
                    Text('Focus: $focus'),
                    const SizedBox(height: 6),
                    Text('Allergies: ${allergies.join(', ')}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),
            Text('Nutrition targets',
                style: GoogleFonts.youngSerif(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            TextField(
              controller: _proteinController,
              keyboardType: TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                labelText: 'Protein (g/kg)',
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _targetWeightController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Target weight (kg)',
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 12),
            Text('Daily calories: ${_dailyCalories.toInt()}',
                style: const TextStyle(fontWeight: FontWeight.w500)),
            Slider(
              value: _dailyCalories,
              min: 1200,
              max: 3500,
              divisions: 23,
              label: _dailyCalories.toInt().toString(),
              onChanged: (v) => setState(() => _dailyCalories = v),
            ),
            const SizedBox(height: 14),
            // Nutrient focus selector row
            Row(
              children: [
                const Text('Focus on: ',
                    style: TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(width: 8),
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children:
                          ['Protein', 'Fat', 'Carbs', 'Vitamins'].map((opt) {
                        final selected = _nutrientFocus == opt;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: ChoiceChip(
                            label: Text(opt),
                            selected: selected,
                            onSelected: (_) =>
                                setState(() => _nutrientFocus = opt),
                            selectedColor: const Color(0xFFFFC1CC),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('$_nutrientFocus rich meals',
                style: GoogleFonts.youngSerif(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            SizedBox(
              height: 140,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: suggestedItemsFor(_nutrientFocus).length,
                itemBuilder: (context, index) {
                  final item = suggestedItemsFor(_nutrientFocus)[index];
                  return Container(
                    width: 220,
                    margin: const EdgeInsets.only(right: 12),
                    child: Card(
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      child: Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: Row(
                          children: [
                            Container(
                              width: 72,
                              height: 72,
                              decoration: BoxDecoration(
                                color: const Color(0xFFFFF3F4),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Center(
                                  child: Icon(Icons.fastfood,
                                      size: 36, color: Colors.black54)),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(item['name']!,
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w600)),
                                  const SizedBox(height: 6),
                                  Text(item['note']!,
                                      style: const TextStyle(
                                          fontSize: 12, color: Colors.black54)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 18),
            Text('Notes & restrictions',
                style: GoogleFonts.youngSerif(
                    fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            if (allergies.isNotEmpty)
              Wrap(
                  spacing: 8,
                  children: allergies
                      .map((a) =>
                          Chip(label: Text(a), backgroundColor: Colors.white))
                      .toList()),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  // Save (demo) then show a product detail for the selected nutrient
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Plan saved (demo)')));
                  final items = suggestedItemsFor(_nutrientFocus);
                  final first = items.isNotEmpty
                      ? items[0]
                      : {'name': 'Protein Mix', 'note': 'High protein'};
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => const ProductListScreen()),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFFC1CC),
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text('Save plan'),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
      bottomNavigationBar: AppBottomNav(
        currentIndex: 4,
        onTapOverride: (i) {
          switch (i) {
            case 0:
              Navigator.pushReplacement(context,
                  MaterialPageRoute(builder: (_) => const ProductListScreen()));
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
