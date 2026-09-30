@echo off
echo ============================================
echo    GoTec.AI - POC Launcher
echo ============================================
echo.
echo Starting backend in new window...
start "GoTec Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
timeout /t 3 >nul
echo Starting frontend in new window...
start "GoTec Frontend" cmd /k "cd /d %~dp0frontend\gotec-web && npm run dev"
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Both servers starting in separate windows.
pause
