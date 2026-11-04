@echo off
title NeuroHR Launcher
echo Launching NeuroHR X Backend and Frontend...
start "" "%~dp0run_backend.bat"
start "" "%~dp0run_frontend.bat"
echo Both servers have been launched!
timeout /t 3
start http://localhost:5173/
exit

