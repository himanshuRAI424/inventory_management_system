@echo off
title Inventory Management System - College Mini-Project
color 0b
echo ======================================================================
echo          INVENTORY MANAGEMENT SYSTEM - COLLEGE MINI-PROJECT
echo ======================================================================
echo.
echo   Technologies: Python Flask, SQLite3, HTML5, CSS3, Vanilla JavaScript
echo.
echo   Starting the Flask web server...
echo   Once started, open your web browser and visit:
echo.
echo          http://127.0.0.1:5000
echo.
echo   Press Ctrl + C in this window to stop the server.
echo ======================================================================
echo.

cd /d "%~dp0"
python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start Flask server.
    echo Please make sure Python and Flask are installed:
    echo   pip install -r requirements.txt
    echo.
    pause
)
