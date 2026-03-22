@echo off
echo Starting EatSmartly Backend Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please make sure .env file exists in this directory
    pause
    exit /b 1
)

REM Start the server
echo.
echo Starting FastAPI server on http://0.0.0.0:8000
echo.
echo Your backend will be accessible at:
echo - From this PC: http://localhost:8000
echo - From your phone: http://YOUR_PC_IP:8000
echo.
echo To find your PC's IP address, run: ipconfig
echo Look for "IPv4 Address" under your WiFi/Ethernet adapter
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the FastAPI server using uvicorn (listening on all interfaces)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause