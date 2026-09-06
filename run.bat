@echo off
TITLE Multi-Agent Financial Document Intelligence Launcher
echo ========================================================
echo   Launching Multi-Agent Financial Document Platform
echo   Django REST + LangGraph + Ollama GGUF + ChromaDB
echo ========================================================
echo.

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%back_end
set FRONTEND_DIR=%ROOT_DIR%front_end\frontend

echo [1/3] Checking Backend Python Environment and Migrations...
cd /d "%BACKEND_DIR%"
if exist "venv\Scripts\python.exe" (
    call venv\Scripts\python.exe manage.py migrate >nul 2>&1
) else (
    echo Virtual environment not found in back_end\venv!
    pause
    exit /b 1
)

echo [2/3] Starting Django REST Backend (http://127.0.0.1:8000)...
start "Django REST Backend" cmd /k "cd /d %BACKEND_DIR% && venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"

ping -n 4 127.0.0.1 >nul

echo [3/3] Starting React Test Dashboard (http://127.0.0.1:5173)...
start "React Test UI" cmd /k "cd /d %FRONTEND_DIR% && npm run dev -- --host 127.0.0.1 --open"

echo.
echo ========================================================
echo   Platform Services Launched Successfully!
echo   - Backend REST API: http://127.0.0.1:8000/api/health/
echo   - React Test UI:    http://127.0.0.1:5173/
echo ========================================================
echo.
