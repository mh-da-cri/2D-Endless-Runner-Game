@echo off
chcp 65001 >nul
title Knight Runner - Setup

echo ============================================
echo   Knight Runner - Endless Fantasy
echo   Automated Setup Script
echo ============================================
echo.

REM --- Kiểm tra Python ---
echo [1/4] Kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python chưa được cài đặt!
    echo Vui lòng tải Python tại: https://www.python.org/downloads/
    echo Lưu ý: Tick "Add Python to PATH" khi cài đặt.
    pause
    exit /b 1
)
python --version
echo       Python OK!
echo.

REM --- Tạo Virtual Environment ---
echo [2/4] Tạo Virtual Environment...
if exist "venv" (
    echo       Virtual environment đã tồn tại, bỏ qua...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Không thể tạo virtual environment!
        pause
        exit /b 1
    )
    echo       Virtual environment đã được tạo!
)
echo.

REM --- Cài đặt Dependencies ---
echo [3/4] Cài đặt dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Không thể cài đặt dependencies!
    pause
    exit /b 1
)
echo       Dependencies đã được cài đặt!
echo.

REM --- Tạo thư mục cần thiết ---
echo [4/4] Tạo thư mục cần thiết...
if not exist "data" mkdir data
if not exist "assets\images" mkdir assets\images
if not exist "assets\audio" mkdir assets\audio
echo       Thư mục OK!
echo.

echo ============================================
echo   Setup hoàn tất!
echo   Chạy game bằng: run.bat
echo ============================================
pause
