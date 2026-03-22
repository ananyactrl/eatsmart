import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../services/api_service.dart';
import '../theme.dart';
import 'result_screen.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({Key? key}) : super(key: key);

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final EatSmartlyAPI api = EatSmartlyAPI();
  final String userId = 'test_user';

  MobileScannerController cameraController = MobileScannerController();
  bool isProcessing = false;
  String statusMessage = 'Analyzing product...';
  int progressStep = 0;

  @override
  void dispose() {
    cameraController.dispose();
    super.dispose();
  }

  Future<void> _analyzeBarcode(String barcode) async {
    if (isProcessing) return;
    if (!mounted) return;
    setState(() { isProcessing = true; statusMessage = 'Scanning barcode...'; progressStep = 1; });

    _updateProgress(2, 'Searching food databases...');
    await Future.delayed(const Duration(milliseconds: 500));
    _updateProgress(3, 'Checking nutrition sources...');
    await Future.delayed(const Duration(milliseconds: 500));
    _updateProgress(4, 'Processing data...');
    await Future.delayed(const Duration(milliseconds: 500));

    try {
      _updateProgress(4, 'Analyzing ingredients...\nThis may take 30-60 seconds');
      final result = await api.analyzeBarcode(barcode: barcode, userId: userId, detailed: true);
      _updateProgress(5, 'Done ✓');
      await Future.delayed(const Duration(milliseconds: 300));
      if (mounted) {
        Navigator.push(context, MaterialPageRoute(builder: (_) => ResultScreen(analysis: result)))
            .then((_) {
          if (mounted) setState(() { isProcessing = false; progressStep = 0; statusMessage = 'Analyzing product...'; });
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() { isProcessing = false; progressStep = 0; });
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(e.toString().replaceAll('Exception: ', '')),
          backgroundColor: AppColors.error,
          action: SnackBarAction(label: 'Retry', textColor: Colors.white, onPressed: () => _analyzeBarcode(barcode)),
        ));
      }
    }
  }

  void _updateProgress(int step, String message) {
    if (!mounted) return;
    setState(() { progressStep = step; statusMessage = message; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera
          MobileScanner(
            controller: cameraController,
            onDetect: (capture) {
              final barcodes = capture.barcodes;
              if (barcodes.isNotEmpty && !isProcessing) {
                final barcode = barcodes.first.rawValue;
                if (barcode != null && barcode.isNotEmpty) _analyzeBarcode(barcode);
              }
            },
          ),

          // Overlay
          CustomPaint(painter: ScannerOverlayPainter(), child: Container()),

          // Top instruction card
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            left: 16, right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              decoration: BoxDecoration(
                color: AppColors.rose,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: const [
                  Icon(Icons.qr_code_scanner, color: Colors.white, size: 22),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text('Point camera at a barcode', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                  ),
                ],
              ),
            ),
          ),

          // Processing overlay
          if (isProcessing)
            Container(
              color: Colors.black54,
              child: Center(
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 40),
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24)),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SizedBox(
                        width: 64, height: 64,
                        child: CircularProgressIndicator(
                          value: progressStep / 5,
                          strokeWidth: 6,
                          backgroundColor: AppColors.blush,
                          valueColor: const AlwaysStoppedAnimation<Color>(AppColors.rose),
                        ),
                      ),
                      const SizedBox(height: 20),
                      Text(statusMessage, textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.dark)),
                      const SizedBox(height: 8),
                      Text('Step $progressStep of 5', style: const TextStyle(fontSize: 12, color: AppColors.muted)),
                    ],
                  ),
                ),
              ),
            ),

          // Bottom controls
          Positioned(
            bottom: 40, left: 0, right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _cameraButton(Icons.flash_on, () => cameraController.toggleTorch()),
                _cameraButton(Icons.flip_camera_ios, () => cameraController.switchCamera()),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _cameraButton(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 56, height: 56,
        decoration: BoxDecoration(color: AppColors.rose, shape: BoxShape.circle),
        child: Icon(icon, color: Colors.white, size: 24),
      ),
    );
  }
}

class ScannerOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = Colors.black54..style = PaintingStyle.fill;
    final scanArea = Rect.fromCenter(
      center: Offset(size.width / 2, size.height / 2),
      width: size.width * 0.7, height: size.height * 0.35,
    );
    final path = Path()
      ..addRect(Rect.fromLTWH(0, 0, size.width, size.height))
      ..addRRect(RRect.fromRectAndRadius(scanArea, const Radius.circular(20)))
      ..fillType = PathFillType.evenOdd;
    canvas.drawPath(path, paint);

    final bracketPaint = Paint()..color = AppColors.rose..style = PaintingStyle.stroke..strokeWidth = 3;
    const bl = 28.0;
    // corners
    for (final corner in [
      [scanArea.left, scanArea.top, 1.0, 1.0],
      [scanArea.right, scanArea.top, -1.0, 1.0],
      [scanArea.left, scanArea.bottom, 1.0, -1.0],
      [scanArea.right, scanArea.bottom, -1.0, -1.0],
    ]) {
      final x = corner[0]; final y = corner[1]; final dx = corner[2]; final dy = corner[3];
      canvas.drawLine(Offset(x, y), Offset(x + dx * bl, y), bracketPaint);
      canvas.drawLine(Offset(x, y), Offset(x, y + dy * bl), bracketPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
