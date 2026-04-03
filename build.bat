@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================
echo  EXE Build
echo ====================================
echo.

pip install pyinstaller >nul 2>&1

echo Building...
pyinstaller --noconfirm --onedir --console --name "PhotoClassifier" ^
  --add-data "templates;templates" ^
  --hidden-import face_recognition ^
  --hidden-import cv2 ^
  --hidden-import numpy ^
  --hidden-import flask ^
  --collect-data face_recognition_models ^
  app.py

if exist "dist\PhotoClassifier" (
    copy /y "run.bat" "dist\PhotoClassifier\run.bat" >nul
    copy /y "README.md" "dist\PhotoClassifier\README.md" >nul
    echo.
    echo ====================================
    echo  [OK] Build complete!
    echo ====================================
    echo.
    echo  dist\PhotoClassifier\ folder is ready to distribute.
    echo  Users just double-click run.bat to start.
) else (
    echo.
    echo [ERROR] Build failed.
)
echo.
pause
