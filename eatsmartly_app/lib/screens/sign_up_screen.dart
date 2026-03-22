import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../theme.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({Key? key}) : super(key: key);
  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;
  bool _obscurePass = true;
  bool _obscureConfirm = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  Future<void> _signUp() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    try {
      final auth = Provider.of<AuthService>(context, listen: false);
      await auth.signUpWithEmailPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Account created! Check your email.'),
          backgroundColor: AppColors.success));
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: AppColors.error));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signUpWithGoogle() async {
    setState(() => _isLoading = true);
    try {
      final auth = Provider.of<AuthService>(context, listen: false);
      await auth.signUpWithGoogle();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: AppColors.error));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header card
              Container(
                width: double.infinity,
                margin: const EdgeInsets.all(16),
                padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
                decoration: BoxDecoration(
                  color: AppColors.coral,
                  borderRadius: BorderRadius.circular(28),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    GestureDetector(
                      onTap: () => Navigator.of(context).pop(),
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.25),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.arrow_back, color: Colors.white, size: 20),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text('Create\nAccount',
                      style: GoogleFonts.poppins(
                        fontSize: 34, fontWeight: FontWeight.w800,
                        color: Colors.white, height: 1.1)),
                    const SizedBox(height: 6),
                    Text('Start your smart eating journey',
                      style: GoogleFonts.poppins(
                        fontSize: 14, color: Colors.white.withOpacity(0.85))),
                  ],
                ),
              ),

              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 8),
                      Text('Your details', style: GoogleFonts.poppins(
                        fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.dark)),
                      const SizedBox(height: 20),

                      _inputField(
                        controller: _emailController,
                        hint: 'Email address',
                        icon: Icons.email_outlined,
                        keyboardType: TextInputType.emailAddress,
                        validator: (v) => (v == null || v.isEmpty) ? 'Enter your email' : null,
                      ),
                      const SizedBox(height: 12),
                      _inputField(
                        controller: _passwordController,
                        hint: 'Password',
                        icon: Icons.lock_outline,
                        obscure: _obscurePass,
                        suffix: IconButton(
                          icon: Icon(_obscurePass ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                            color: AppColors.muted, size: 20),
                          onPressed: () => setState(() => _obscurePass = !_obscurePass),
                        ),
                        validator: (v) => (v != null && v.length < 6) ? 'Min 6 characters' : null,
                      ),
                      const SizedBox(height: 12),
                      _inputField(
                        controller: _confirmController,
                        hint: 'Confirm password',
                        icon: Icons.lock_outline,
                        obscure: _obscureConfirm,
                        suffix: IconButton(
                          icon: Icon(_obscureConfirm ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                            color: AppColors.muted, size: 20),
                          onPressed: () => setState(() => _obscureConfirm = !_obscureConfirm),
                        ),
                        validator: (v) => v != _passwordController.text ? 'Passwords don\'t match' : null,
                      ),

                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _signUp,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.rose,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                            elevation: 0,
                          ),
                          child: _isLoading
                            ? const SizedBox(height: 20, width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : Text('Create Account', style: GoogleFonts.poppins(fontWeight: FontWeight.w700, fontSize: 16)),
                        ),
                      ),

                      const SizedBox(height: 16),
                      Row(children: [
                        Expanded(child: Divider(color: AppColors.coral.withOpacity(0.4))),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: Text('or', style: GoogleFonts.poppins(color: AppColors.muted, fontSize: 13)),
                        ),
                        Expanded(child: Divider(color: AppColors.coral.withOpacity(0.4))),
                      ]),
                      const SizedBox(height: 16),

                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          onPressed: _isLoading ? null : _signUpWithGoogle,
                          style: OutlinedButton.styleFrom(
                            foregroundColor: AppColors.dark,
                            side: BorderSide(color: AppColors.coral.withOpacity(0.5)),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                            backgroundColor: AppColors.blush,
                          ),
                          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                            const Icon(Icons.g_mobiledata, color: Colors.red, size: 24),
                            const SizedBox(width: 8),
                            Text('Sign up with Google',
                              style: GoogleFonts.poppins(fontWeight: FontWeight.w600, fontSize: 14)),
                          ]),
                        ),
                      ),

                      const SizedBox(height: 24),
                      Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                        Text('Already have an account? ',
                          style: GoogleFonts.poppins(color: AppColors.muted, fontSize: 14)),
                        GestureDetector(
                          onTap: () => Navigator.of(context).pop(),
                          child: Text('Sign In',
                            style: GoogleFonts.poppins(
                              color: AppColors.rose, fontWeight: FontWeight.w700, fontSize: 14)),
                        ),
                      ]),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _inputField({
    required TextEditingController controller,
    required String hint,
    required IconData icon,
    bool obscure = false,
    Widget? suffix,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      obscureText: obscure,
      keyboardType: keyboardType,
      validator: validator,
      style: GoogleFonts.poppins(fontSize: 14, color: AppColors.dark),
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: Icon(icon, color: AppColors.coral, size: 20),
        suffixIcon: suffix,
        filled: true,
        fillColor: AppColors.blush,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: AppColors.rose, width: 1.5)),
      ),
    );
  }
}
