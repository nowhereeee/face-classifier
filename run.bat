@echo off
chcp 65001 >nul
cd /d "%~dp0"
timeout /t 1 >nul
start http://localhost:5000
PhotoClassifier.exe
