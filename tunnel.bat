@echo off
cd /d "%~dp0"
echo.
echo MARDIOR + Cloudflare Tunnel
echo ==============================
echo.
echo Requisito: Tener cloudflared instalado
echo   winget install cloudflare.cloudflared
echo.
echo Iniciando servidor...
start /B python -m mardior --web-only --tunnel
echo.
echo Esperando tunel...
echo (La URL publica aparecera arriba cuando el tunel este listo)
echo.
echo Para detener: cierra esta ventana o presiona Ctrl+C
pause
