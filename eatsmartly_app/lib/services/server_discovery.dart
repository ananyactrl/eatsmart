import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Auto-discovery service for the backend server
class ServerDiscovery {
  static const List<int> commonPorts = [8000, 8001, 8002, 8003, 8080, 3000];
  static const Duration timeout = Duration(seconds: 2);

  static Future<String?> discoverServer() async {
    // 1. Try saved ngrok URL first (fastest, most reliable)
    final prefs = await SharedPreferences.getInstance();
    final savedNgrok = prefs.getString('ngrok_url');
    if (savedNgrok != null && savedNgrok.isNotEmpty) {
      final result = await _tryUrls([savedNgrok]);
      if (result != null) return result;
    }

    // 2. Try localhost (emulator)
    final localhostUrl = await _tryUrls([
      'http://10.0.2.2:8000',
      'http://localhost:8000',
      'http://127.0.0.1:8000',
    ]);
    if (localhostUrl != null) return localhostUrl;

    // 3. Try common local IPs
    final localIps = await _getCommonLocalIps();
    final localUrls = localIps
        .expand((ip) => commonPorts.map((port) => 'http://$ip:$port'))
        .toList();
    return await _tryUrls(localUrls);
  }

  /// Save a ngrok URL for future use
  static Future<void> saveNgrokUrl(String url) async {
    String cleaned = url.trim();
    if (!cleaned.startsWith('http')) cleaned = 'https://$cleaned';
    if (cleaned.endsWith('/')) cleaned = cleaned.substring(0, cleaned.length - 1);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('ngrok_url', cleaned);
  }

  /// Get saved ngrok URL
  static Future<String?> getSavedNgrokUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('ngrok_url');
  }

  static Future<List<String>> _getCommonLocalIps() async {
    final List<String> ips = [];
    try {
      for (var interface in await NetworkInterface.list()) {
        for (var addr in interface.addresses) {
          if (addr.type == InternetAddressType.IPv4 && !addr.isLoopback) {
            final parts = addr.address.split('.');
            if (parts.length == 4) {
              final subnet = '${parts[0]}.${parts[1]}.${parts[2]}';
              ips.addAll(['$subnet.1', '$subnet.2', '$subnet.5', '$subnet.10', '$subnet.100']);
            }
          }
        }
      }
    } catch (e) {
      print('Could not get network interfaces: $e');
    }
    return ips;
  }

  static Future<String?> _tryUrls(List<String> urls) async {
    for (final url in urls) {
      try {
        final response = await http
            .get(Uri.parse('$url/health'), headers: {'ngrok-skip-browser-warning': 'true'})
            .timeout(timeout, onTimeout: () => throw TimeoutException(''));
        if (response.statusCode == 200) {
          print('✅ Found server at: $url');
          return url;
        }
      } catch (e) {
        continue;
      }
    }
    return null;
  }

  static Future<Map<String, dynamic>?> getServerInfo(String baseUrl) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/server-info')).timeout(timeout);
      if (response.statusCode == 200) return json.decode(response.body);
    } catch (e) {
      print('Could not get server info: $e');
    }
    return null;
  }

  static String getConnectionInstructions(String? foundUrl) {
    if (foundUrl != null) return '✅ Server found at: $foundUrl\n\nConnected successfully!';
    return '❌ Could not find server.\n\nEnter your ngrok URL in Profile → Server Settings.';
  }
}
