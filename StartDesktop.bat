@echo off
cd /d "%~dp0"
python ToolDesktop.py
if errorlevel 1 pause
