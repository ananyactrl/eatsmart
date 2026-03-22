# EatSmartly Flutter App Setup Script

Write-Host "🎨 EatSmartly Flutter App Setup" -ForegroundColor Green
Write-Host "=" * 50

# Check Flutter
Write-Host "`n📌 Checking Flutter installation..." -ForegroundColor Cyan
try {
    $flutterVersion = flutter --version 2>&1 | Select-String "Flutter"
    Write-Host "✅ $flutterVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Flutter not found. Please install Flutter first." -ForegroundColor Red
    Write-Host "   Visit: https://docs.flutter.dev/get-started/install/windows" -ForegroundColor Yellow
    exit 1
}

# Navigate to app directory
Set-Location $PSScriptRoot

# Get dependencies
Write-Host "`n📦 Installing Flutter dependencies..." -ForegroundColor Cyan
flutter pub get

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check for connected devices
Write-Host "`n📱 Checking for connected devices..." -ForegroundColor Cyan
$devices = flutter devices 2>&1

if ($devices -match "No devices") {
    Write-Host "⚠️  No devices connected" -ForegroundColor Yellow
    Write-Host "   Connect an Android device or start an emulator" -ForegroundColor Yellow
} else {
    Write-Host "✅ Devices found:" -ForegroundColor Green
    flutter devices
}

# Summary
Write-Host "`n" + ("=" * 50)
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n📋 Next steps:"
Write-Host "1. Make sure backend is running:" -ForegroundColor Cyan
Write-Host "   cd ..\eatsmartly-backend" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor White

Write-Host "`n2. Update API endpoint in lib\services\api_service.dart:" -ForegroundColor Cyan
Write-Host "   For physical device: http://YOUR_PC_IP:8000" -ForegroundColor White
Write-Host "   For emulator: http://10.0.2.2:8000" -ForegroundColor White

Write-Host "`n3. Run the app:" -ForegroundColor Cyan
Write-Host "   flutter run" -ForegroundColor White
Write-Host "   OR press F5 in VS Code" -ForegroundColor White

Write-Host "`n📚 Documentation: See README.md" -ForegroundColor Yellow
Write-Host "`n✨ Your app uses these beautiful colors:" -ForegroundColor Green
Write-Host "   🎨 Champagne #F5E6D1" -ForegroundColor White
Write-Host "   🎨 Light Red #FFC8CB" -ForegroundColor White
Write-Host "   🎨 Rose Gold #B46C72" -ForegroundColor White
Write-Host "   🎨 Puce Red #6E2E34" -ForegroundColor White
Write-Host "   🎨 Rackley #5E7B9B" -ForegroundColor White

Write-Host "`n🚀 Happy coding!" -ForegroundColor Green
