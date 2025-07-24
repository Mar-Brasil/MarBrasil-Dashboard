@echo off
echo ========================================
echo  SINCRONIZACAO DIARIA DE EQUIPAMENTOS
echo ========================================
echo.
echo Iniciando agendador...
echo Pressione Ctrl+C para parar
echo.

cd /d "%~dp0"
python schedule_daily_equipment_sync.py

pause
