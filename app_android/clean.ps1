Write-Host "Limpando caches do Gradle..." -ForegroundColor Cyan

# Parar o daemon do Gradle
./gradlew --stop 2>&1 | Out-Null

# Remover pastas de cache
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\caches"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\daemon"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\workers"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.gradle\configuration-cache"

# Remover pastas do projeto
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue ".gradle"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "app\build"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "build"

Write-Host "Limpeza concluída!" -ForegroundColor Green
Write-Host "Por favor, reinicie o Android Studio e sincronize o projeto novamente." -ForegroundColor Yellow
