import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme.dart';
import 'login_screen.dart';

class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({Key? key}) : super(key: key);
  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen>
    with SingleTickerProviderStateMixin {
  Timer? _timer;
  late AnimationController _anim;
  late Animation<double> _fade;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 900));
    _fade = CurvedAnimation(parent: _anim, curve: Curves.easeOut);
    _anim.forward();
    _timer = Timer(const Duration(seconds: 3), () {
      Navigator.pushReplacement(context,
        MaterialPageRoute(builder: (_) => const LoginScreen()));
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _anim.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fade,
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Spacer(),
                // Big hero card
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: AppColors.rose,
                    borderRadius: BorderRadius.circular(32),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.25),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text('🌿 nutrition made simple',
                          style: GoogleFonts.poppins(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                      ),
                      const SizedBox(height: 24),
                      Text('eat\nsmart,\nlive well.',
                        style: GoogleFonts.poppins(
                          fontSize: 44, fontWeight: FontWeight.w800,
                          color: Colors.white, height: 1.05)),
                      const SizedBox(height: 16),
                      Text('Know exactly what\'s in your food.\nPersonalised for you.',
                        style: GoogleFonts.poppins(
                          fontSize: 15, color: Colors.white.withOpacity(0.85), height: 1.5)),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                // Two small stat cards
                Row(children: [
                  Expanded(child: _miniCard('🥗', 'Smart\nAnalysis', AppColors.cardMint)),
                  const SizedBox(width: 12),
                  Expanded(child: _miniCard('🎯', 'Personal\nGoals', AppColors.cardLavender)),
                  const SizedBox(width: 12),
                  Expanded(child: _miniCard('📊', 'Track\nNutrition', AppColors.cardPeach)),
                ]),
                const Spacer(),
                Center(
                  child: Column(children: [
                    SizedBox(
                      width: 8,
                      height: 8,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.rose.withOpacity(0.5)),
                    ),
                    const SizedBox(height: 12),
                    Text('loading your experience...',
                      style: GoogleFonts.poppins(color: AppColors.muted, fontSize: 12)),
                  ]),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _miniCard(String emoji, String label, Color bg) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(20)),
      child: Column(children: [
        Text(emoji, style: const TextStyle(fontSize: 22)),
        const SizedBox(height: 6),
        Text(label, textAlign: TextAlign.center,
          style: GoogleFonts.poppins(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.dark)),
      ]),
    );
  }
}
