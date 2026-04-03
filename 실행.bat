@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================
echo  Photo Classifier - Starting...
echo ====================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11.
    pause
    exit /b 1
)

pip show flask >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing flask...
    pip install flask -q
) else (
    echo [OK] flask
)

pip show opencv-python >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing opencv...
    pip install opencv-python -q
) else (
    echo [OK] opencv
)

pip show deepface >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing deepface (tensorflow included, may take a while)...
    pip install deepface -q
) else (
    echo [OK] deepface
)

pip show tf-keras >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing tf-keras...
    pip install tf-keras -q
) else (
    echo [OK] tf-keras
)

echo.
echo [READY] Starting server...
echo.
timeout /t 1 >nul
start http://localhost:5000
python app.py
pause
