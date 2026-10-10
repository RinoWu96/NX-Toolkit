@echo off
rem Build NX-Toolkit.exe into dist\NX-Toolkit  /  打包 NX-Toolkit.exe 到 dist\NX-Toolkit
cd /d "%~dp0"
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --name NX-Toolkit ^
  --icon assets\icon.ico --add-data "assets\icon.png;assets" ^
  --collect-submodules nsz.Fs --collect-submodules nsz.nut ^
  --exclude-module nsz.gui --exclude-module kivy --exclude-module tkinter ^
  app.py
