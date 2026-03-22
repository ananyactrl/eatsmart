import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:http/http.dart' as http;

/// Auto-discovery service for the backend server
/// Tries to find the backend server on the local network
class ServerDiscovery {
  /// Common ports to try
  static const List<int> commonPorts = [8000, 8001, 8002, 8003, 8080, 3000];

  /// Timeout for each discovery attempt
  static const Duration timeout = Duration(seconds: 2);

  /// Try to discover server on local network
  /// Returns the base URL if found, null otherwise
  static Future<String?> discoverServer() async {
    // 1. Try localhost first (for emulator)
    final localhostUrl = await _tryUrls([
      'http://10.0.2.2:8000', // Android emulator
      'http://localhost:8000',
      'http://127.0.0.1:8000',
    ]);
    if (localhostUrl != null) return localhostUrl;

    // 2. Try common local IPs
    final localIps = await _getCommonLocalIps();
    final localUrls = localIps
        .expand((ip) => commonPorts.map((port) => 'http://$ip:$port'))
        .toList();

    return await _tryUrls(localUrls);
  }

  /// Get common local IP patterns to try
  static Future<List<String>> _getCommonLocalIps() async {
    final List<String> ips = [];

    // Try to get device's local IP subnet
    try {
      for (var interface in await NetworkInterface.list()) {
        for (var addr in interface.addresses) {
          if (addr.type == InternetAddressType.IPv4 && !addr.isLoopback) {
            // Get subnet (e.g., 192.168.1.x)
            final parts = addr.address.split('.');
            if (parts.length == 4) {
              final subnet = '${parts[0]}.${parts[1]}.${parts[2]}';
              // Try common router/server IPs
              ips.addAll([
                '$subnet.1',
                '$subnet.2',
                '$subnet.5',
                '$subnet.10',
                '$subnet.100',
              ]);
            }
          }
        }
      }
    } catch (e) {
      print('Could not get network interfaces: $e');
    }

    return ips;
  }

  /// Try a list of URLs and return the first one that responds
  static Future<String?> _tryUrls(List<String> urls) async {
    for (final url in urls) {
      try {
        final response = await http
            .get(Uri.parse('$url/health'))
            .timeout(timeout, onTimeout: () => throw TimeoutException(''));

        if (response.statusCode == 200) {
          print('✅ Found server at: $url');
          return url;
        }
      } catch (e) {
        // Silently continue to next URL
        continue;
      }
    }
    return null;
  }

  /// Get server info from a known URL
  static Future<Map<String, dynamic>?> getServerInfo(String baseUrl) async {
    try {
      final response =
          await http.get(Uri.parse('$baseUrl/server-info')).timeout(timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('Could not get server info: $e');
    }
    return null;
  }

  /// Show connection instructions to user
  static String getConnectionInstructions(String? foundUrl) {
    if (foundUrl != null) {
      return '''
✅ Server found at: $foundUrl

Connected successfully!
''';
    } else {
      return '''
❌ Could not find server automatically.

Manual Setup Required:
1. Start backend server: run start_server.bat
2. Find your PC's IP address: run ipconfig
3. Update api_service.dart line 12 with your IP
4. Ensure phone and PC on same WiFi

Example (Local Network):
static const String baseUrl = 'http://192.168.1.2:8000';

Or use Ngrok (Recommended):
static const String baseUrl = 'https://your-code.ngrok-free.app';
''';
    }
  }
}
