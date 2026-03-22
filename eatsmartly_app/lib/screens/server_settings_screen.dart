import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../services/server_discovery.dart';
import '../theme.dart';

class ServerSettingsScreen extends StatefulWidget {
  const ServerSettingsScreen({Key? key}) : super(key: key);

  @override
  State<ServerSettingsScreen> createState() => _ServerSettingsScreenState();
}

class _ServerSettingsScreenState extends State<ServerSettingsScreen> {
  final TextEditingController _urlController = TextEditingController();
  bool _isDiscovering = false;
  bool _isTesting = false;
  String? _discoveryMessage;
  String? _testResult;

  @override
  void initState() {
    super.initState();
    _loadCurrentUrl();
  }

  void _loadCurrentUrl() {
    setState(() {
      _urlController.text = EatSmartlyAPI.getCurrentBaseUrl();
    });
  }

  Future<void> _autoDiscover() async {
    setState(() {
      _isDiscovering = true;
      _discoveryMessage = null;
      _testResult = null;
    });

    try {
      final foundUrl = await ServerDiscovery.discoverServer();

      setState(() {
        _isDiscovering = false;
        if (foundUrl != null) {
          _urlController.text = foundUrl;
          _discoveryMessage = '✅ Server found at: $foundUrl';
          // Auto-save discovered URL
          _saveUrl();
        } else {
          _discoveryMessage =
              '❌ Could not find server.\n\nMake sure:\n• Backend server is running\n• Phone and PC on same WiFi\n• Port 8000 is accessible';
        }
      });
    } catch (e) {
      setState(() {
        _isDiscovering = false;
        _discoveryMessage = '❌ Discovery failed: $e';
      });
    }
  }

  Future<void> _testConnection() async {
    setState(() {
      _isTesting = true;
      _testResult = null;
    });

    try {
      // Temporarily set URL for testing
      await EatSmartlyAPI.setBaseUrl(_urlController.text);

      final isConnected = await EatSmartlyAPI.testConnection();

      setState(() {
        _isTesting = false;
        if (isConnected) {
          _testResult = '✅ Connection successful!';
        } else {
          _testResult =
              '❌ Cannot connect to server.\n\nPlease check:\n• Server is running\n• URL is correct\n• Network connectivity';
        }
      });
    } catch (e) {
      setState(() {
        _isTesting = false;
        _testResult = '❌ Connection failed: $e';
      });
    }
  }

  Future<void> _saveUrl() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a server URL')),
      );
      return;
    }

    await EatSmartlyAPI.setBaseUrl(url);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('✅ Server URL saved: $url')),
      );
    }
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.cream,
      appBar: AppBar(
        title: const Text('Server Settings'),
        backgroundColor: AppColors.rose,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Info banner
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFE3F2FD),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.info_outline, color: Colors.blue),
                      SizedBox(width: 8),
                      Text(
                        'Server Configuration',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Configure the backend server connection. You can auto-discover the server on your network or enter the URL manually.',
                    style: TextStyle(fontSize: 13),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Auto-discover button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isDiscovering ? null : _autoDiscover,
                icon: _isDiscovering
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.search),
                label: Text(_isDiscovering
                    ? 'Searching for server...'
                    : '🔍 Auto-Discover Server'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.coral,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),

            if (_discoveryMessage != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _discoveryMessage!.startsWith('✅')
                      ? Colors.green.shade50
                      : Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _discoveryMessage!.startsWith('✅')
                        ? Colors.green
                        : Colors.red,
                  ),
                ),
                child: Text(
                  _discoveryMessage!,
                  style: const TextStyle(fontSize: 13),
                ),
              ),
            ],

            const SizedBox(height: 24),
            const Divider(),
            const SizedBox(height: 24),

            // Manual URL input
            const Text(
              'Manual Configuration',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _urlController,
              decoration: InputDecoration(
                labelText: 'Server URL',
                hintText: 'https://fawn-bespoke-unglacially.ngrok-free.dev',
                prefixIcon: const Icon(Icons.link),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.copy),
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: _urlController.text));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('URL copied to clipboard')),
                    );
                  },
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: Colors.white,
              ),
            ),
            const SizedBox(height: 12),

            // Common presets
            const Text(
              'Quick Presets:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildPresetChip('Android Emulator', 'http://10.0.2.2:8000'),
                _buildPresetChip('Localhost', 'http://localhost:8000'),
                _buildPresetChip('192.168.1.2', 'http://192.168.1.2:8000'),
              ],
            ),

            const SizedBox(height: 16),

            // Ngrok option
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.purple.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.purple.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.public, size: 16, color: Colors.purple.shade700),
                      const SizedBox(width: 8),
                      Text(
                        '🌐 Using Ngrok? (Recommended)',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                          color: Colors.purple.shade900,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Ngrok URL format: https://your-code.ngrok-free.app',
                    style: TextStyle(fontSize: 11),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    '✅ Works on ANY network (WiFi, hotspot, mobile data)\n'
                    '✅ No IP configuration needed\n'
                    '⚠️  URL changes each ngrok restart',
                    style: TextStyle(fontSize: 10, height: 1.4),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Action buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isTesting ? null : _testConnection,
                    icon: _isTesting
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.network_check),
                    label: const Text('Test'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _saveUrl,
                    icon: const Icon(Icons.save),
                    label: const Text('Save'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.rose,
                      foregroundColor: Colors.black87,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
              ],
            ),

            if (_testResult != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _testResult!.startsWith('✅')
                      ? Colors.green.shade50
                      : Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _testResult!.startsWith('✅')
                        ? Colors.green
                        : Colors.red,
                  ),
                ),
                child: Text(
                  _testResult!,
                  style: const TextStyle(fontSize: 13),
                ),
              ),
            ],

            const SizedBox(height: 24),
            const Divider(),
            const SizedBox(height: 24),

            // Help section
            _buildHelpSection(),
          ],
        ),
      ),
    );
  }

  Widget _buildPresetChip(String label, String url) {
    return ActionChip(
      label: Text(label, style: const TextStyle(fontSize: 12)),
      onPressed: () {
        setState(() {
          _urlController.text = url;
        });
      },
      backgroundColor: AppColors.cream,
      side: const BorderSide(color: AppColors.rose),
    );
  }

  Widget _buildHelpSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.help_outline, size: 20),
              SizedBox(width: 8),
              Text(
                'Setup Instructions',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            '📍 LOCAL NETWORK (WiFi):\n'
            '1. Start backend: start_server.bat\n'
            '2. Find PC IP: ipconfig\n'
            '3. Format: http://YOUR_IP:8000\n'
            '4. Or use Auto-Discover!\n\n'
            '🌐 NGROK (ANY NETWORK - RECOMMENDED):\n'
            '1. Start ngrok: ngrok http 8000\n'
            '2. Copy the https URL shown\n'
            '3. Paste URL here and save\n'
            '✅ Works on hotspot/mobile data!\n'
            '⚠️  URL changes each ngrok restart',
            style: TextStyle(fontSize: 13, height: 1.5),
          ),
          const SizedBox(height: 12),
          const Text(
            '💡 Pro Tip: Ngrok solves ALL network issues!',
            style: TextStyle(
              fontSize: 12,
              fontStyle: FontStyle.italic,
              color: Colors.purple,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
