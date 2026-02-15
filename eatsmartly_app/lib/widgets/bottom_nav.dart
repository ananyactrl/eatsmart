import 'package:flutter/material.dart';

class AppBottomNav extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int>? onTapOverride;
  const AppBottomNav({Key? key, this.currentIndex = 0, this.onTapOverride})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: currentIndex,
      type: BottomNavigationBarType.fixed,
      selectedItemColor: Colors.black,
      unselectedItemColor: Colors.black54,
      onTap: (i) {
        if (onTapOverride != null) return onTapOverride!(i);
      },
      items: const [
        BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
        BottomNavigationBarItem(icon: Icon(Icons.restaurant), label: 'Food'),
        BottomNavigationBarItem(
            icon: Icon(Icons.health_and_safety), label: 'Nutritionists'),
        BottomNavigationBarItem(
            icon: Icon(Icons.favorite_border), label: 'Saved'),
        BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
      ],
    );
  }
}
