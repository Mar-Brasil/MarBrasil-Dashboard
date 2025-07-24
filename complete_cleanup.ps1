# Script de Limpeza Completa para Android Studio
Write-Host "=== LIMPEZA COMPLETA DO ANDROID STUDIO ===" -ForegroundColor Yellow
Write-Host "Este script vai limpar TODOS os caches relacionados ao Gradle e Android" -ForegroundColor Red
Write-Host ""

# Confirmar execução
$confirm = Read-Host "Deseja continuar? (S/N)"
if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-Host "Operação cancelada." -ForegroundColor Yellow
    exit
}

Write-Host "Iniciando limpeza..." -ForegroundColor Green

# 1. Parar processos
Write-Host "1. Parando processos Java e Gradle..." -ForegroundColor Cyan
try {
    Stop-Process -Name "java" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "gradle*" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "studio*" -Force -ErrorAction SilentlyContinue
    Write-Host "   Processos parados" -ForegroundColor Green
} catch {
    Write-Host "   Alguns processos já estavam parados" -ForegroundColor Yellow
}

# 2. Limpar cache global do usuário
Write-Host "2. Limpando cache global..." -ForegroundColor Cyan
$gradleHome = "$env:USERPROFILE\.gradle"
$androidHome = "$env:USERPROFILE\.android"

if (Test-Path $gradleHome) {
    Remove-Item -Recurse -Force $gradleHome -ErrorAction SilentlyContinue
    Write-Host "   Cache do Gradle removido" -ForegroundColor Green
}

if (Test-Path $androidHome) {
    Remove-Item -Recurse -Force $androidHome -ErrorAction SilentlyContinue
    Write-Host "   Cache do Android removido" -ForegroundColor Green
}

# 3. Limpar cache do projeto
Write-Host "3. Limpando cache do projeto..." -ForegroundColor Cyan
Set-Location "app_android"

$foldersToRemove = @(".gradle", "build", "app\build", ".idea")
foreach ($folder in $foldersToRemove) {
    if (Test-Path $folder) {
        Remove-Item -Recurse -Force $folder -ErrorAction SilentlyContinue
        Write-Host "   $folder removido" -ForegroundColor Green
    }
}

# 4. Limpar cache temporário do Windows
Write-Host "4. Limpando arquivos temporários..." -ForegroundColor Cyan
$tempPaths = @(
    "$env:TEMP\*gradle*",
    "$env:TEMP\*android*",
    "$env:TEMP\*kotlin*",
    "$env:LOCALAPPDATA\Temp\*gradle*",
    "$env:LOCALAPPDATA\Temp\*android*"
)

foreach ($path in $tempPaths) {
    Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
}
Write-Host "   Arquivos temporários limpos" -ForegroundColor Green

# 5. Recriar wrapper do Gradle
Write-Host "5. Recriando Gradle Wrapper..." -ForegroundColor Cyan
if (Test-Path "gradlew.bat") {
    try {
        .\gradlew.bat wrapper --gradle-version 7.3.3 --distribution-type all
        Write-Host "   Gradle Wrapper recriado" -ForegroundColor Green
    } catch {
        Write-Host "   Erro ao recriar wrapper - será criado na sincronização" -ForegroundColor Yellow
    }
}

Set-Location ".."

Write-Host ""
Write-Host "=== LIMPEZA CONCLUÍDA ===" -ForegroundColor Green
Write-Host ""
Write-Host "PRÓXIMOS PASSOS OBRIGATÓRIOS:" -ForegroundColor Yellow
Write-Host "1. REINICIE O COMPUTADOR" -ForegroundColor Red
Write-Host "2. Abra o Android Studio" -ForegroundColor White
Write-Host "3. File → Settings → Build Tools → Gradle" -ForegroundColor White
Write-Host "4. Gradle JDK: Selecione 'Use Embedded JDK'" -ForegroundColor White
Write-Host "5. Apply → OK" -ForegroundColor White
Write-Host "6. File → Open → Selecione app_android" -ForegroundColor White
Write-Host ""
Write-Host "Se ainda houver erro, execute: File → Invalidate Caches and Restart" -ForegroundColor Cyan
