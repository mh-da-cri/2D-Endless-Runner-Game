@echo off
chcp 65001 >nul
title Knight Runner - Endless Fantasy

REM --- Kiểm tra venv ---
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment chưa được tạo!
    echo Vui lòng chạy setup.bat trước.
    pause
    exit /b 1
)

REM --- Kích hoạt venv và chạy game ---
call venv\Scripts\activate.bat
python main.py
