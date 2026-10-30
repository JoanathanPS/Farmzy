@echo off
echo ===================================================
echo             Starting Farmzy Platform
echo ===================================================

echo Starting FastAPI Backend on port 8000...
start "Farmzy Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Astro Frontend on port 4321...
start "Farmzy Astro Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo Farmzy Backend:  http://localhost:8000
echo API Docs:        http://localhost:8000/docs
echo Astro Frontend:  http://localhost:4321
echo ===================================================
