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

python -c "import dlib" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing dlib...
    pip install https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.1-cp311-cp311-win_amd64.whl
    if errorlevel 1 (
        echo [ERROR] dlib install failed.
        pause
        exit /b 1
    )
) else (
    echo [OK] dlib
)

python -c "import face_recognition" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing face_recognition...
    pip install face_recognition
) else (
    echo [OK] face_recognition
)

python -c "import numpy; exit(0 if int(numpy.__version__.split('.')[0]) < 2 else 1)" >nul 2>&1
if errorlevel 1 (
    echo [FIX] numpy downgrade...
    pip install "numpy<2"
) else (
    echo [OK] numpy
)

python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing flask...
    pip install flask
) else (
    echo [OK] flask
)

python -c "import cv2" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing opencv...
    pip install opencv-python
) else (
    echo [OK] opencv
)

echo.
echo [READY] Starting server...
echo.
timeout /t 1 >nul
start http://localhost:5000
python app.py
