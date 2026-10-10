@echo off
rem Run NX Toolkit from source  /  从源码启动 NX Toolkit
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" app.py
