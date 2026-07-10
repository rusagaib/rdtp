@echo off
title [RDTP] Radiology DICOM to PACS

set "PYTHON_EXE=D:\repo\rdtp\venv\Scripts\python.exe"
set "SCRIPT_PATH=D:\repo\rdtp\rdtp_services.py"

cd /d D:\repo\rdtp

:restart

echo.
echo [%date% %time%] Starting RDTP...
echo.

"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo [%date% %time%] RDTP exited.
echo Restarting in 10 seconds...

timeout /t 10 >nul

goto restart
