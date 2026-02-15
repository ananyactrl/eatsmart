import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import '../services/ocr_service.dart';
import '../services/ocr_parser.dart';
import '../models/food_analysis.dart';
import '../theme.dart';
import 'result_screen.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({Key? key}) : super(key: key);

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final EatSmartlyAPI api = EatSmartlyAPI();
  final String userId = 'test_user'; // Replace with actual user ID from auth

  MobileScannerController cameraController = MobileScannerController();
  bool isProcessing = false;
  String? error;
  String statusMessage = 'Analyzing product...';
  int progressStep = 0;
  bool isOcrProcessing = false;

  @override
  void dispose() {
    cameraController.dispose();
    super.dispose();
  }

  Future<void> _analyzeBarcode(String barcode) async {
    if (isProcessing) return;

    if (!mounted) return;
    setState(() {
      isProcessing = true;
      error = null;
      statusMessage = 'Scanning barcode: $barcode';
      progressStep = 1;
    });

    // Update progress messages
    _updateProgress(2, 'Searching Open Food Facts India...');
    await Future.delayed(const Duration(milliseconds: 500));

    _updateProgress(3, 'Checking global food databases...');
    await Future.delayed(const Duration(milliseconds: 500));

    _updateProgress(4, 'Querying 4 nutrition sources...');
    await Future.delayed(const Duration(milliseconds: 500));

    try {
      _updateProgress(
          4, 'Processing data from backend...\nThis may take 30-60 seconds');

      final result = await api.analyzeBarcode(
          barcode: barcode, userId: userId, detailed: true);

      _updateProgress(5, 'Analysis complete! ✓');
      await Future.delayed(const Duration(milliseconds: 500));

      if (mounted) {
        // Navigate to results screen
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ResultScreen(analysis: result),
          ),
        ).then((_) {
          // Reset state when coming back
          if (mounted) {
            setState(() {
              isProcessing = false;
              progressStep = 0;
              statusMessage = 'Analyzing product...';
            });
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          error = e.toString().replaceAll('Exception: ', '');
          isProcessing = false;
          progressStep = 0;
        });
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(error ?? 'Unknown error'),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 5),
            action: SnackBarAction(
              label: 'Retry',
              textColor: Colors.white,
              onPressed: () => _analyzeBarcode(barcode),
            ),
          ),
        );
      }
    }
  }

  void _updateProgress(int step, String message) {
    if (!mounted) return;
    setState(() {
      progressStep = step;
      statusMessage = message;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E1),
      appBar: AppBar(
        backgroundColor: const Color(0xFFFFC1CC),
        title: Text('Scan Barcode',
            style: GoogleFonts.youngSerif(
                fontSize: 18, fontWeight: FontWeight.w700)),
      ),
      body: Stack(
        children: [
          // Camera view
          MobileScanner(
            controller: cameraController,
            onDetect: (capture) {
              final List<Barcode> barcodes = capture.barcodes;
              if (barcodes.isNotEmpty && !isProcessing) {
                final barcode = barcodes.first.rawValue;
                if (barcode != null && barcode.isNotEmpty) {
                  _analyzeBarcode(barcode);
                }
              }
            },
          ),

          // Scanning overlay
          CustomPaint(
            painter: ScannerOverlayPainter(),
            child: Container(),
          ),

          // Instructions
          Positioned(
            top: 40,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              child: Card(
                color: const Color(0xFFFFC1CC), // pastel pink
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'Position the barcode within the frame',
                    textAlign: TextAlign.center,
                    style: GoogleFonts.youngSerif(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ),
          ),

          // Loading indicator
          if (isProcessing)
            Container(
              color: Colors.black45,
              child: Center(
                child: Card(
                  color: Colors.white,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        CircularProgressIndicator(
                          color: const Color(0xFFFFC1CC), // pastel pink
                          value: progressStep / 5,
                        ),
                        const SizedBox(height: 14),
                        Text(
                          statusMessage,
                          textAlign: TextAlign.center,
                          style: GoogleFonts.youngSerif(
                            color: const Color(0xFF4C0004),
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Step $progressStep of 5',
                          style: GoogleFonts.youngSerif(
                            color: const Color(0xFFAFA231),
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'This may take up to 60 seconds',
                          style: GoogleFonts.youngSerif(
                            color: const Color(0xFF5A5A5A),
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),

          // Bottom controls
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // Toggle flash
                FloatingActionButton(
                  heroTag: 'flash',
                  backgroundColor: const Color(0xFFFFC1CC), // pastel pink
                  onPressed: () => cameraController.toggleTorch(),
                  child: const Icon(Icons.flash_on, color: Colors.white),
                ),

                // Flip camera
                FloatingActionButton(
                  heroTag: 'flip',
                  backgroundColor: const Color(0xFFFFC1CC),
                  onPressed: () => cameraController.switchCamera(),
                  child: const Icon(Icons.flip_camera_ios, color: Colors.white),
                ),

                // OCR capture
                FloatingActionButton(
                  heroTag: 'ocr',
                  backgroundColor: const Color(0xFFFFC1CC),
                  onPressed: isOcrProcessing
                      ? null
                      : () async {
                          try {
                            setState(() {
                              isOcrProcessing = true;
                              statusMessage = 'Capturing image for OCR...';
                            });

                            // Use dynamic call to avoid analyzer issues across
                            // mobile_scanner versions while still invoking
                            // the runtime method when available.
                            final xfile = await (cameraController as dynamic)
                                .takePicture();
                            if (xfile == null)
                              throw Exception('Failed to capture image');

                            setState(() {
                              statusMessage = 'Running on-device OCR...';
                            });

                            final recognized =
                                await recognizeTextFromFile(xfile.path);

                            setState(() {
                              statusMessage = 'Parsing nutrition values...';
                            });

                            final result =
                                parseNutritionFromRecognizedText(recognized);

                            // Build a minimal FoodAnalysis to show results
                            final analysis = FoodAnalysis(
                              barcode: 'ocr',
                              foodName: null,
                              brand: null,
                              verdict: 'unknown',
                              riskLevel: 'unknown',
                              healthScore: 0,
                              alerts: [],
                              warnings: [],
                              suggestions: [],
                              alternatives: [],
                              recipes: [],
                              nutritionTips: [],
                              detailedNutrition: result.nutrition,
                              timestamp: DateTime.now().toIso8601String(),
                            );

                            if (!result.confident && mounted) {
                              // Offer guided capture flow when confidence is low
                              final takeMore = await showDialog<bool>(
                                context: context,
                                builder: (context) => AlertDialog(
                                  title: const Text('Partial recognition'),
                                  content: Text(
                                      'We could only detect ${result.foundCount} key values.\nWould you like to take a few more photos (nutrition table, ingredients, front) to improve accuracy?'),
                                  actions: [
                                    TextButton(
                                      onPressed: () =>
                                          Navigator.of(context).pop(true),
                                      child: const Text('Take more photos'),
                                    ),
                                    TextButton(
                                      onPressed: () =>
                                          Navigator.of(context).pop(false),
                                      child: const Text('Continue anyway'),
                                    ),
                                  ],
                                ),
                              );

                              if (takeMore == true) {
                                // Let user continue capturing; just return to scanner.
                                if (mounted) setState(() {});
                                return;
                              }
                            }

                            if (mounted) {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                      ResultScreen(analysis: analysis),
                                ),
                              );
                            }
                          } catch (e) {
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text(e.toString())),
                              );
                            }
                          } finally {
                            if (mounted)
                              setState(() => isOcrProcessing = false);
                          }
                        },
                  child: isOcrProcessing
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Icon(Icons.text_snippet, color: Colors.white),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Custom painter for scanner overlay
class ScannerOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black54
      ..style = PaintingStyle.fill;

    final scanArea = Rect.fromCenter(
      center: Offset(size.width / 2, size.height / 2),
      width: size.width * 0.7,
      height: size.height * 0.4,
    );

    // Draw dark overlay with transparent scan area
    final path = Path()
      ..addRect(Rect.fromLTWH(0, 0, size.width, size.height))
      ..addRRect(RRect.fromRectAndRadius(scanArea, const Radius.circular(16)))
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(path, paint);

    // Draw corner brackets
    final bracketPaint = Paint()
      ..color = const Color(0xFFFFC1CC)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4;

    const bracketLength = 30.0;

    // Top-left
    canvas.drawLine(
      Offset(scanArea.left, scanArea.top + bracketLength),
      Offset(scanArea.left, scanArea.top),
      bracketPaint,
    );
    canvas.drawLine(
      Offset(scanArea.left, scanArea.top),
      Offset(scanArea.left + bracketLength, scanArea.top),
      bracketPaint,
    );

    // Top-right
    canvas.drawLine(
      Offset(scanArea.right - bracketLength, scanArea.top),
      Offset(scanArea.right, scanArea.top),
      bracketPaint,
    );
    canvas.drawLine(
      Offset(scanArea.right, scanArea.top),
      Offset(scanArea.right, scanArea.top + bracketLength),
      bracketPaint,
    );

    // Bottom-left
    canvas.drawLine(
      Offset(scanArea.left, scanArea.bottom - bracketLength),
      Offset(scanArea.left, scanArea.bottom),
      bracketPaint,
    );
    canvas.drawLine(
      Offset(scanArea.left, scanArea.bottom),
      Offset(scanArea.left + bracketLength, scanArea.bottom),
      bracketPaint,
    );

    // Bottom-right
    canvas.drawLine(
      Offset(scanArea.right - bracketLength, scanArea.bottom),
      Offset(scanArea.right, scanArea.bottom),
      bracketPaint,
    );
    canvas.drawLine(
      Offset(scanArea.right, scanArea.bottom - bracketLength),
      Offset(scanArea.right, scanArea.bottom),
      bracketPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
