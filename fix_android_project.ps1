# Script para corrigir problemas do projeto Android
Write-Host "🔧 Corrigindo projeto Android..." -ForegroundColor Yellow

# Navega para o diretório do projeto
Set-Location "app_android"

# Remove cache do Gradle
Write-Host "🗑️  Limpando cache do Gradle..." -ForegroundColor Yellow
if (Test-Path ".gradle") {
    Remove-Item -Recurse -Force ".gradle"
}

if (Test-Path "app\build") {
    Remove-Item -Recurse -Force "app\build"
}

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

# Remove arquivos de cache do Android Studio
Write-Host "🗑️  Limpando cache do Android Studio..." -ForegroundColor Yellow
if (Test-Path ".idea") {
    Remove-Item -Recurse -Force ".idea"
}

if (Test-Path "*.iml") {
    Remove-Item -Force "*.iml"
}

if (Test-Path "app\*.iml") {
    Remove-Item -Force "app\*.iml"
}

# Limpa arquivos desnecessários
Write-Host "🧹 Limpeza concluída!" -ForegroundColor Green

Write-Host "✅ Projeto Android corrigido!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Abra o Android Studio" -ForegroundColor White
Write-Host "2. Selecione 'Open an existing Android Studio project'" -ForegroundColor White
Write-Host "3. Navegue até a pasta 'app_android'" -ForegroundColor White
Write-Host "4. Aguarde a sincronização do Gradle" -ForegroundColor White
Write-Host "5. Se houver erros, clique em 'Sync Project with Gradle Files'" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Se ainda houver problemas:" -ForegroundColor Yellow
Write-Host "- File > Invalidate Caches and Restart" -ForegroundColor White
Write-Host "- Build > Clean Project" -ForegroundColor White
Write-Host "- Build > Rebuild Project" -ForegroundColor White

Set-Location ".."
