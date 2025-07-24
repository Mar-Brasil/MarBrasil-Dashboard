# Script simples para limpar cache do Android
Write-Host "Limpando cache do projeto Android..." -ForegroundColor Yellow

Set-Location "app_android"

# Remove cache do Gradle
if (Test-Path ".gradle") {
    Remove-Item -Recurse -Force ".gradle"
    Write-Host "Cache do Gradle removido" -ForegroundColor Green
}

if (Test-Path "app\build") {
    Remove-Item -Recurse -Force "app\build"
    Write-Host "Build do app removido" -ForegroundColor Green
}

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Build raiz removido" -ForegroundColor Green
}

# Remove cache do Android Studio
if (Test-Path ".idea") {
    Remove-Item -Recurse -Force ".idea"
    Write-Host "Cache do Android Studio removido" -ForegroundColor Green
}

Write-Host "Limpeza concluida!" -ForegroundColor Green
Write-Host "Agora abra o projeto no Android Studio" -ForegroundColor Cyan

Set-Location ".."
