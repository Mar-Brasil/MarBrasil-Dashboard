# Script para corrigir incompatibilidade de Java
Write-Host "=== Corrigindo Incompatibilidade de Java ===" -ForegroundColor Yellow

# Parar todos os processos do Gradle
Write-Host "1. Parando processos do Gradle..." -ForegroundColor Cyan
Stop-Process -Name "gradle*" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "java" -Force -ErrorAction SilentlyContinue

# Limpar cache global do Gradle
Write-Host "2. Limpando cache global do Gradle..." -ForegroundColor Cyan
$gradleHome = "$env:USERPROFILE\.gradle"
if (Test-Path $gradleHome) {
    Remove-Item -Recurse -Force "$gradleHome\caches" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$gradleHome\daemon" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$gradleHome\wrapper" -ErrorAction SilentlyContinue
    Write-Host "Cache global limpo" -ForegroundColor Green
}

# Entrar no diretório do projeto
Set-Location "app_android"

# Limpar cache local do projeto
Write-Host "3. Limpando cache local do projeto..." -ForegroundColor Cyan
if (Test-Path ".gradle") {
    Remove-Item -Recurse -Force ".gradle"
    Write-Host "Cache local limpo" -ForegroundColor Green
}

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Build limpo" -ForegroundColor Green
}

if (Test-Path "app\build") {
    Remove-Item -Recurse -Force "app\build"
    Write-Host "Build do app limpo" -ForegroundColor Green
}

# Verificar versão do Java
Write-Host "4. Verificando versão do Java..." -ForegroundColor Cyan
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    Write-Host "Java encontrado: $javaVersion" -ForegroundColor Yellow
    
    # Verificar se é Java 21 (incompatível)
    if ($javaVersion -match "21\.") {
        Write-Host "ATENÇÃO: Java 21 detectado - incompatível com Gradle 7.4" -ForegroundColor Red
        Write-Host "Recomendação: Instale Java 8 ou 11" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Java não encontrado no PATH" -ForegroundColor Red
}

# Criar wrapper do Gradle limpo
Write-Host "5. Recriando Gradle Wrapper..." -ForegroundColor Cyan
try {
    gradle wrapper --gradle-version 7.4 --distribution-type all
    Write-Host "Gradle Wrapper recriado" -ForegroundColor Green
} catch {
    Write-Host "Erro ao recriar wrapper - usando wrapper existente" -ForegroundColor Yellow
}

Write-Host "=== Correção Concluída ===" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Se você tem Java 21, instale Java 8 ou 11" -ForegroundColor White
Write-Host "2. Defina JAVA_HOME para apontar para Java 8/11" -ForegroundColor White
Write-Host "3. Abra o Android Studio e importe o projeto" -ForegroundColor White
Write-Host "4. Se ainda houver erro, use File > Invalidate Caches and Restart" -ForegroundColor White

Set-Location ".."
