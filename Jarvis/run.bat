@echo off
title J.A.R.V.I.S. OS 5.0 - Stark Industries
cd /d "%~dp0"
echo ===================================================
echo     STARTING J.A.R.V.I.S. DESKTOP ASSISTANT
echo ===================================================
python main.py
if errorlevel 1 (
    echo.
    echo Jarvis exited with an error. Check logs above.
    pause
)
