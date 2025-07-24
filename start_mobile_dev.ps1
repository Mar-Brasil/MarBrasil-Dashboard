# Script para iniciar o ambiente de desenvolvimento mobile
# Execute este script para configurar tudo automaticamente

Write-Host "🚀 Iniciando ambiente de desenvolvimento Painel Auvo Mobile..." -ForegroundColor Green

# Verifica se o Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado. Instale o Python primeiro." -ForegroundColor Red
    exit 1
}

# Verifica se as dependências estão instaladas
Write-Host "📦 Verificando dependências Python..." -ForegroundColor Yellow

$requiredPackages = @("fastapi", "uvicorn", "bcrypt", "pydantic")
foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>$null
        Write-Host "✅ $package instalado" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Instalando $package..." -ForegroundColor Yellow
        pip install $package
    }
}

# Verifica se o banco de dados existe
if (Test-Path "auvo.db") {
    Write-Host "✅ Banco de dados encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ Banco de dados auvo.db não encontrado!" -ForegroundColor Red
    Write-Host "   Certifique-se de que o banco está no diretório raiz do projeto." -ForegroundColor Yellow
}

# Configura regra do firewall
Write-Host "🔥 Configurando firewall..." -ForegroundColor Yellow
try {
    New-NetFirewallRule -DisplayName "Auvo Mobile API" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -ErrorAction SilentlyContinue
    Write-Host "✅ Regra de firewall configurada" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Não foi possível configurar o firewall automaticamente" -ForegroundColor Yellow
    Write-Host "   Execute como administrador ou configure manualmente" -ForegroundColor Yellow
}

# Obtém o IP local
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"} | Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "🌐 Configuração de Rede:" -ForegroundColor Cyan
Write-Host "   Para Emulador Android: http://10.0.2.2:8001/" -ForegroundColor White
Write-Host "   Para Dispositivo Físico: http://${localIP}:8001/" -ForegroundColor White
Write-Host ""

# Inicia o backend mobile
Write-Host "🚀 Iniciando backend mobile na porta 8001..." -ForegroundColor Green
Write-Host "   Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

try {
    python api_backend_mobile.py
} catch {
    Write-Host "❌ Erro ao iniciar o backend mobile" -ForegroundColor Red
    Write-Host "   Verifique se o arquivo api_backend_mobile.py existe" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "👋 Backend mobile finalizado" -ForegroundColor Yellow
