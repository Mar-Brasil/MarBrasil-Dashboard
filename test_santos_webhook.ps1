Write-Host "Testando webhook de localizacao para Santos..." -ForegroundColor Green

# Definindo as coordenadas de Santos-SP (aproximadamente)
$LAT = "-23.9618"
$LONG = "-46.3322"
$ACCURACY = "10"
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# URL do webhook (ajuste conforme necessário)
$WEBHOOK_URL = "http://127.0.0.1:8000/api/webhook/location"

Write-Host "Enviando dados: Latitude: $LAT, Longitude: $LONG, Precisao: $ACCURACY"
Write-Host ""

# Preparando o corpo da requisição
$body = @{
    location = @{
        latitude = $LAT
        longitude = $LONG
        accuracy = $ACCURACY
    }
    timestamp = $TIMESTAMP
    device_id = "test-device-santos"
    user_id = "test-user-santos"
} | ConvertTo-Json

# Usando Invoke-WebRequest para enviar a requisição POST
try {
    $response = Invoke-WebRequest -Uri $WEBHOOK_URL -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    Write-Host "Resposta do servidor (Status: $($response.StatusCode)):" -ForegroundColor Green
    Write-Host $response.Content
}
catch {
    Write-Host "Erro ao enviar requisição: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status code: $statusCode" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Teste concluido. Verifique o console do servidor para ver a resposta." -ForegroundColor Green
Write-Host "Pressione qualquer tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
