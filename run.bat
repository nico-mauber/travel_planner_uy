@echo off
REM Lanza Trip Planner usando el Python del venv, sin depender de PATH ni activacion.
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" -m streamlit run app.py %*
