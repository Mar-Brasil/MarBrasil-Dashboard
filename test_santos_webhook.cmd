@echo off
echo Testando webhook de localizacao para Santos...

REM Definindo as coordenadas de Santos-SP (aproximadamente)
set LAT=-23.9618
set LONG=-46.3322
set ACCURACY=10
set TIMESTAMP=%TIME%

REM URL do webhook (ajuste conforme necessário)
set WEBHOOK_URL=http://127.0.0.1:8000/api/webhook/location

echo Enviando dados: Latitude: %LAT%, Longitude: %LONG%, Precisao: %ACCURACY%
echo.

REM Usando curl para enviar a requisição POST
curl -X POST %WEBHOOK_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"location\": {\"latitude\": %LAT%, \"longitude\": %LONG%, \"accuracy\": %ACCURACY%}, \"timestamp\": \"%TIMESTAMP%\", \"device_id\": \"test-device-santos\", \"user_id\": \"test-user-santos\"}"

echo.
echo Teste concluido. Verifique o console do servidor para ver a resposta.
pause
