@echo off
echo Starting GoTec Backend...
cd /d %~dp0
call venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
pause
