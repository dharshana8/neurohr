@echo off
title NeuroHR Backend (FastAPI)
cd /d "%~dp0backend"
echo Starting NeuroHR Backend on http://127.0.0.1:8000 ...
..\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
pause

