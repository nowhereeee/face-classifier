@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================
echo  Photo Classifier - Starting...
echo ====================================
echo.

python --version >/dev/null 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11.
    pause
    exit /b 1
)

echo Checking dependencies...
pip install flask opencv-python deepface tf-keras -q

echo.
echo [READY] Starting server...
echo.
timeout /t 1 >nul
start http://localhost:5000
python app.py
pause
