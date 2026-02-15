import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'profile_details_screen.dart';

class ProfileFormScreen extends StatefulWidget {
  const ProfileFormScreen({Key? key}) : super(key: key);

  @override
  State<ProfileFormScreen> createState() => _ProfileFormScreenState();
}

class _ProfileFormScreenState extends State<ProfileFormScreen> {
  final _firstNameController = TextEditingController();
  final _ageController = TextEditingController();
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();

  String _gender = 'Male';
  final List<String> _allergyOptions = [
    'Peanuts',
    'Dairy',
    'Gluten',
    'Eggs',
    'Shellfish'
  ];
  final Set<String> _selectedAllergies = {};

  final List<String> _foodOptions = [
    'Fruits',
    'Vegetarian',
    'Seafood',
    'Fast Food',
    'Dairy'
  ];
  final Set<String> _selectedFoods = {};

  final List<String> _focusOptions = [
    'Weight gain',
    'Healthy skin',
    'Glow',
    'Hair growth',
    'Weight loss'
  ];
  String? _focus;

  @override
  void dispose() {
    _firstNameController.dispose();
    _ageController.dispose();
    _weightController.dispose();
    _heightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top illustration
            Center(
              child: Container(
                width: double.infinity,
                height: 180,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: const BoxDecoration(
                  image: DecorationImage(
                    image: AssetImage('lib/screens/download (36).jpeg'),
                    fit: BoxFit.contain,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 6),
            Text('Tell us about yourself',
                style: GoogleFonts.youngSerif(
                    fontSize: 20, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),

            // First name
            TextField(
              controller: _firstNameController,
              decoration: InputDecoration(
                labelText: 'First name',
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 12),

            // Age and gender row
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ageController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Age',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _gender,
                    decoration: InputDecoration(
                      labelText: 'Gender',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none),
                    ),
                    items: ['Male', 'Female', 'Other']
                        .map((g) => DropdownMenuItem(value: g, child: Text(g)))
                        .toList(),
                    onChanged: (v) => setState(() => _gender = v ?? 'Male'),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),
            // Weight & Height
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _weightController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Weight (kg)',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _heightController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Height (cm)',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none),
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 18),
            Text('Any allergies?',
                style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _allergyOptions.map((opt) {
                final selected = _selectedAllergies.contains(opt);
                return FilterChip(
                  label: Text(opt),
                  selected: selected,
                  onSelected: (v) => setState(() => v
                      ? _selectedAllergies.add(opt)
                      : _selectedAllergies.remove(opt)),
                  selectedColor: const Color(0xFFFFC1CC),
                );
              }).toList(),
            ),

            const SizedBox(height: 18),
            Text('Favorite foods (pick any)',
                style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _foodOptions.map((opt) {
                final selected = _selectedFoods.contains(opt);
                return FilterChip(
                  label: Text(opt),
                  selected: selected,
                  onSelected: (v) => setState(() =>
                      v ? _selectedFoods.add(opt) : _selectedFoods.remove(opt)),
                  selectedColor: const Color(0xFFFFC1CC),
                );
              }).toList(),
            ),

            const SizedBox(height: 18),
            Text('What are you focusing on?',
                style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _focusOptions.map((opt) {
                final selected = _focus == opt;
                return ChoiceChip(
                  label: Text(opt),
                  selected: selected,
                  onSelected: (_) => setState(() => _focus = opt),
                  selectedColor: const Color(0xFFFFC1CC),
                );
              }).toList(),
            ),

            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  // Collect data and proceed to details screen
                  final profile = {
                    'first_name': _firstNameController.text,
                    'age': _ageController.text,
                    'gender': _gender,
                    'weight': _weightController.text,
                    'height': _heightController.text,
                    'allergies': _selectedAllergies.toList(),
                    'favorite_foods': _selectedFoods.toList(),
                    'focus': _focus,
                  };
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => ProfileDetailsScreen(profile: profile)),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFFC1CC),
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text('Save & Continue'),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
