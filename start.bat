@echo off
echo ============================================
echo    GoTec.AI - Launcher
echo ============================================
start "GoTec Backend" cmd /k "cd /d %~dp0architect-agent && set PYTHONPATH=%cd%\src&& set ARCH_PORT=8000&& python -m archagent.server"
timeout /t 3 >nul
start "GoTec Frontend" cmd /k "cd /d %~dp0frontend\gotec-web && npm run dev"
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
pause
