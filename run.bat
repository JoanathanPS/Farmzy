@echo off
setlocal

echo ==========================================
echo       Farmzy - Smart Farming Platform
echo ==========================================

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH.
    pause
    exit /b 1
)

echo.
echo [1/4] Setting up Backend...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing backend requirements...
pip install -r requirements.txt

echo.
echo [2/4] Setting up Frontend...
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)
cd ..

echo.
echo [3/4] Starting Backend Server...
start "Farmzy Backend" cmd /k "call venv\Scripts\activate && uvicorn app.main:app --reload"

echo.
echo [4/4] Starting Frontend Server...
cd frontend
start "Farmzy Frontend" cmd /k "npm run dev"

echo.
echo ==========================================
echo    Farmzy is running!
echo    Backend: http://127.0.0.1:8000
echo    Frontend: http://localhost:4321
echo ==========================================
echo.
echo Press any key to exit this launcher...
pause
