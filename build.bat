@echo off
title NOVA EXE Builder
echo ===================================================
echo             Building Standalone NOVA.exe           
echo ===================================================
.\.venv\Scripts\python.exe build_exe.py
pause
