@echo off
echo ==========================================
echo J.A.C.K. MOBILE BUILD SYSTEM
echo ==========================================
cd mobile
echo [1/3] Fetching dependencies...
call flutter pub get
echo [2/3] Building Release APK...
call flutter build apk --release
echo [3/3] Deploying APK to project root...
copy build\app\outputs\flutter-apk\app-release.apk ..\jack_remote_control.apk /Y
echo ==========================================
echo BUILD COMPLETE: jack_remote_control.apk
echo ==========================================
pause
