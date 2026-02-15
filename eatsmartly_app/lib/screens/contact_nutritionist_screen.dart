import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class ContactNutritionistScreen extends StatelessWidget {
  const ContactNutritionistScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(18.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Nutritionist header + primary action
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFC1CC),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Text('Contact our Nutritionist',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.youngSerif(
                                fontSize: 18, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 6),
                        const Text('Get personalised advice and meal plans',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.black87)),
                      ],
                    ),
                    const SizedBox(height: 4),
                    GridView.count(
                      crossAxisCount: 2,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 0.85,
                      children: [
                        _nutritionistTile(context, 'Dr. Emma', 'asset/i2.png'),
                        _nutritionistTile(context, 'Dr. Rane', 'asset/i3.png'),
                        _nutritionistTile(context, 'Dr. Mike', 'asset/i5.png'),
                        _nutritionistTile(
                            context, 'Dr. Sam', 'asset/image.png'),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              Text('Choose how you want to connect',
                  style: GoogleFonts.youngSerif(
                      fontSize: 16, fontWeight: FontWeight.w600)),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _contactOption(Icons.chat, 'Chat'),
                  _contactOption(Icons.call, 'Call'),
                  _contactOption(Icons.video_call, 'Video'),
                  _contactOption(Icons.mail_outline, 'Email'),
                ],
              ),
              const SizedBox(height: 18),
              Text('Select a convenient time',
                  style: GoogleFonts.youngSerif(
                      fontSize: 16, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  'Today 10:00',
                  'Today 14:00',
                  'Tomorrow 09:00',
                  'Tomorrow 18:00'
                ]
                    .map((t) => ChoiceChip(
                        label: Text(t), selected: false, onSelected: (_) {}))
                    .toList(),
              ),
              const SizedBox(height: 18),
              Text('Tell us briefly about your goals',
                  style: GoogleFonts.youngSerif(
                      fontSize: 16, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              TextField(
                minLines: 3,
                maxLines: 5,
                decoration: InputDecoration(
                  hintText:
                      'e.g., I want to gain muscle, reduce sugar intake...',
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide.none),
                ),
              ),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                        content: Text('Request submitted (demo)')));
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFFC1CC),
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                  ),
                  child: Text('Request Consultation',
                      style:
                          GoogleFonts.youngSerif(fontWeight: FontWeight.w600)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

Widget _contactOption(IconData icon, String label) {
  return Column(
    children: [
      Container(
        width: 64,
        height: 64,
        decoration: BoxDecoration(
            color: Colors.white, borderRadius: BorderRadius.circular(16)),
        child: Icon(icon, color: Colors.pinkAccent, size: 30),
      ),
      const SizedBox(height: 8),
      Text(label, style: const TextStyle(color: Colors.black87)),
    ],
  );
}

Widget _nutritionistCard(BuildContext context, String name, String imageUrl) {
  return GestureDetector(
    onTap: () {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Selected $name (demo)')));
    },
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 88,
          height: 88,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            color: Colors.white,
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.network(
              imageUrl + '?auto=format&fit=crop&w=300&q=60',
              fit: BoxFit.cover,
              errorBuilder: (c, e, s) =>
                  const Icon(Icons.person, size: 40, color: Colors.black26),
            ),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
            width: 88,
            child: Text(name,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12))),
      ],
    ),
  );
}

Widget _nutritionistTile(BuildContext context, String name, String imageUrl) {
  return GestureDetector(
    onTap: () => ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text('Selected $name (demo)'))),
    child: Column(
      children: [
        Container(
          height: 140,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black12,
                blurRadius: 6,
                offset: Offset(0, 3),
              )
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: imageUrl.startsWith('asset/')
                ? Image.asset(
                    imageUrl,
                    width: double.infinity,
                    height: double.infinity,
                    fit: BoxFit.cover,
                    errorBuilder: (c, e, s) => const Icon(Icons.person,
                        size: 48, color: Colors.black26),
                  )
                : Image.network(
                    imageUrl + '?auto=format&fit=crop&w=800&q=70',
                    width: double.infinity,
                    height: double.infinity,
                    fit: BoxFit.cover,
                    errorBuilder: (c, e, s) => const Icon(Icons.person,
                        size: 48, color: Colors.black26),
                  ),
          ),
        ),
        const SizedBox(height: 8),
        Text(name,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
      ],
    ),
  );
}
