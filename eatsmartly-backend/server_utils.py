"""
Server configuration and connection utilities
Handles auto-detection of free ports and network configuration
"""
import socket
import sys
import platform
import json
from typing import Optional, Tuple


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """
    Find a free port starting from start_port

    Args:
        start_port: Port to start searching from
        max_attempts: Maximum number of ports to try

    Returns:
        Free port number
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            # Port is in use, try next one
            continue

    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")


def get_local_ip() -> str:
    """
    Get the local IP address of this machine

    Returns:
        Local IP address as string
    """
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to a public DNS server (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def get_all_network_ips() -> list[str]:
    """
    Get all network IP addresses

    Returns:
        List of IP addresses
    """
    hostname = socket.gethostname()
    try:
        ips = socket.gethostbyname_ex(hostname)[2]
        # Filter out localhost
        return [ip for ip in ips if not ip.startswith("127.")]
    except Exception:
        return [get_local_ip()]


def print_server_info(host: str, port: int):
    """
    Print colorful server connection information

    Args:
        host: Host server is running on
        port: Port server is running on
    """
    local_ip = get_local_ip()
    all_ips = get_all_network_ips()

    print("\n" + "="*70)
    print("  🚀 EATSMARTLY BACKEND SERVER STARTED SUCCESSFULLY! 🚀")
    print("="*70)
    print(f"\n📍 Server is running on port: {port}")
    print(f"💻 Host: {host}")

    print("\n🌐 ACCESS METHODS:")
    print("-" * 70)
    print(f"  1. From this PC:")
    print(f"     → http://localhost:{port}/docs")
    print(f"     → http://127.0.0.1:{port}/docs")

    print(f"\n  2. From your phone/tablet (same WiFi):")
    if all_ips:
        for ip in all_ips:
            print(f"     → http://{ip}:{port}/docs")
    else:
        print(f"     → http://{local_ip}:{port}/docs")

    print(f"\n  3. From Android Emulator:")
    print(f"     → http://10.0.2.2:{port}/docs")

    print("\n📱 FLUTTER APP CONFIGURATION:")
    print("-" * 70)
    print(f"  File: eatsmartly_app/lib/services/api_service.dart")
    print(f"  Line 12: Update to:")
    print(f"  static const String baseUrl = 'http://{local_ip}:{port}';")

    print("\n✅ QUICK TEST:")
    print("-" * 70)
    print(f"  Open in browser: http://localhost:{port}/docs")
    print(f"  You should see FastAPI documentation")

    print("\n" + "="*70)
    print("  Press Ctrl+C to stop the server")
    print("="*70 + "\n")

    # Save connection info to file
    save_connection_info(local_ip, port)


def save_connection_info(ip: str, port: int):
    """
    Save connection info to a JSON file for Flutter app to read

    Args:
        ip: Server IP address
        port: Server port
    """
    config = {
        "server_ip": ip,
        "server_port": port,
        "base_url": f"http://{ip}:{port}",
        "docs_url": f"http://{ip}:{port}/docs",
        "timestamp": socket.gethostname()
    }

    try:
        with open("server_config.json", "w") as f:
            json.dump(config, f, indent=2)
        print(f"💾 Connection info saved to: server_config.json")
    except Exception as e:
        print(f"⚠️  Could not save config file: {e}")


def check_port_available(port: int) -> bool:
    """
    Check if a port is available

    Args:
        port: Port number to check

    Returns:
        True if port is free, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', port))
        sock.close()
        return True
    except OSError:
        return False


if __name__ == "__main__":
    # Test the utilities
    print("Testing network utilities...")
    print(f"Local IP: {get_local_ip()}")
    print(f"All IPs: {get_all_network_ips()}")
    print(f"Free port: {find_free_port()}")
    print(f"Port 8000 available: {check_port_available(8000)}")
