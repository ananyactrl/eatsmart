@echo off
echo.
echo ========================================
echo   FIND YOUR PC'S IP ADDRESS
echo ========================================
echo.

REM Get the IPv4 address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    set IP=%%a
    REM Remove leading spaces
    for /f "tokens=*" %%b in ("!IP!") do set IP=%%b
)

echo Finding your network IP address...
echo.

REM Show all IPv4 addresses
ipconfig | findstr /C:"IPv4 Address"

echo.
echo ========================================
echo   CONFIGURATION INSTRUCTIONS
echo ========================================
echo.
echo 1. Copy one of the IP addresses above (e.g., 192.168.1.5)
echo.
echo 2. Update Flutter app configuration:
echo    File: eatsmartly_app/lib/services/api_service.dart
echo    Line 12: static const String baseUrl = 'http://YOUR_IP:8000';
echo    Replace YOUR_IP with the IP address you copied
echo.
echo 3. Make sure your phone and PC are on the SAME WiFi network
echo.
echo 4. Start the backend server using start_server.bat
echo.
echo 5. Test in browser: http://YOUR_IP:8000/docs
echo.
echo ========================================
pause