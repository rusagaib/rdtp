@echo off
title [RDTP] Radiologi DICOM to PACS
color 0A

echo [INFO] Starting Environment...
set PYTHON_EXE=D:\repo\rdtp\venv\Scripts\python.exe
set SCRIPT_PATH=D:\repo\rdtp\rdtp_services.py

echo [INFO] Runing Init Script...
echo ---------------------------------------

:: RUn python dari venv
"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo ---------------------------------------
echo [WARN] Script terhenti!
pause
