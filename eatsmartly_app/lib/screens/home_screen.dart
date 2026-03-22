import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'meal_planner_screen.dart';
import 'scanner_screen.dart';
import 'search_screen.dart';
import '../services/auth_service.dart';
import '../theme.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    const DashboardPage(),
    const MealPlannerScreen(),
    const NutritionTrackingPage(),
    const CommunityPage(),
    const ProfilePage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: _pages[_selectedIndex],
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          boxShadow: [BoxShadow(color: AppColors.coral.withOpacity(0.15), blurRadius: 20, offset: const Offset(0, -4))],
        ),
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _navItem(0, Icons.home_rounded, Icons.home_outlined, 'Home'),
                _navItem(1, Icons.restaurant_menu_rounded, Icons.restaurant_menu_outlined, 'Meals'),
                _navItem(2, Icons.bar_chart_rounded, Icons.bar_chart_outlined, 'Nutrition'),
                _navItem(3, Icons.people_rounded, Icons.people_outline_rounded, 'Community'),
                _navItem(4, Icons.person_rounded, Icons.person_outline_rounded, 'Profile'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _navItem(int index, IconData active, IconData inactive, String label) {
    final isSelected = _selectedIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _selectedIndex = index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.blush : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(isSelected ? active : inactive,
              color: isSelected ? AppColors.rose : AppColors.muted, size: 24),
          const SizedBox(height: 2),
          Text(label, style: GoogleFonts.poppins(
              fontSize: 10,
              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w400,
              color: isSelected ? AppColors.rose : AppColors.muted)),
        ]),
      ),
    );
  }
}
