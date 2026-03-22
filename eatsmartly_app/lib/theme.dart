import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  // Primary palette
  static const Color rose = Color(0xFFE27575);       // #e27575 - main accent
  static const Color blush = Color(0xFFFAE5E7);      // #fae5e7 - soft bg
  static const Color coral = Color(0xFFECA6A4);      // #eca6a4 - mid tone
  static const Color cream = Color(0xFFFFF8F0);      // warm white bg
  static const Color softYellow = Color(0xFFFFF3CD); // warm yellow tint

  // Supporting
  static const Color dark = Color(0xFF2A1A1A);       // near-black for text
  static const Color muted = Color(0xFF8A6A6A);      // muted rose-brown
  static const Color white = Colors.white;
  static const Color success = Color(0xFF6DBF8A);
  static const Color warning = Color(0xFFF5A623);
  static const Color error = Color(0xFFE27575);

  // Card backgrounds
  static const Color cardRose = Color(0xFFFAE5E7);
  static const Color cardCoral = Color(0xFFF5C5C3);
  static const Color cardMint = Color(0xFFD4EDE1);
  static const Color cardLavender = Color(0xFFE8E0F5);
  static const Color cardPeach = Color(0xFFFDE8D8);

  // Aliases for backward compatibility
  static const Color primary = rose;
  static const Color secondary = coral;
  static const Color textPrimary = dark;
  static const Color textSecondary = muted;
  static const Color textLight = Color(0xFFB09090);
  static const Color info = Color(0xFF5B9BD5);
  static const Color surfaceVariant = Color(0xFFF5F0F0);
}

class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      fontFamily: GoogleFonts.poppins().fontFamily,
      colorScheme: const ColorScheme.light(
        primary: AppColors.rose,
        secondary: AppColors.coral,
        surface: AppColors.white,
        background: AppColors.cream,
        error: AppColors.error,
        onPrimary: Colors.white,
        onSecondary: Colors.white,
        onSurface: AppColors.dark,
        onBackground: AppColors.dark,
      ),
      scaffoldBackgroundColor: AppColors.cream,
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.cream,
        foregroundColor: AppColors.dark,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.poppins(
          fontSize: 20,
          fontWeight: FontWeight.w700,
          color: AppColors.dark,
        ),
      ),
      cardTheme: CardTheme(
        color: AppColors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.rose,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          elevation: 0,
          textStyle: GoogleFonts.poppins(fontWeight: FontWeight.w600, fontSize: 15),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.blush,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.rose, width: 1.5),
        ),
        hintStyle: GoogleFonts.poppins(color: AppColors.muted, fontSize: 14),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      ),
    );
  }
}
