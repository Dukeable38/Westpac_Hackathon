@echo off
rem Radar demo launcher: offline replay of the recorded OpenRouter answers, clean payments list.
rem Double-click, wait for "Application startup complete", then use the browser tab it opens.
cd /d "%~dp0"
set DEMO_MODE=replay
set RADAR_DB=%~dp0app\demo.sqlite
if exist "%RADAR_DB%" del "%RADAR_DB%"
start "" http://127.0.0.1:8080/
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080
