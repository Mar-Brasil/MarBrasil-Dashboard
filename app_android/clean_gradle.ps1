Write-Host "Cleaning Gradle caches..." -ForegroundColor Cyan

# Stop any running Gradle daemons
gradlew --stop 2>&1 | Out-Null

# Remove Gradle caches
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\caches"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\daemon"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\workers"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\configuration-cache"

# Remove project build directories
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue ".gradle"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "app\build"

Write-Host "Gradle caches cleaned successfully!" -ForegroundColor Green
Write-Host "Please restart Android Studio and sync the project again." -ForegroundColor Yellow
