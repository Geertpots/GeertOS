@echo off
setlocal
cd /d "%~dp0"
title GeertOS - Freedom Edition

echo ============================================
echo       GeertOS - Freedom Edition
echo ============================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  set PY=py
) else (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set PY=python
  ) else (
    echo Python is nog niet geinstalleerd.
    echo Download Python via https://www.python.org/downloads/
    echo Vink tijdens installatie aan: Add Python to PATH.
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Eenmalige installatie wordt voorbereid...
  %PY% -m venv .venv
  if errorlevel 1 goto :error
)

echo Benodigde onderdelen worden gecontroleerd...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo GeertOS wordt gestart...
start "GeertOS" ".venv\Scripts\python.exe" -m streamlit run app.py
exit /b 0

:error
echo.
echo Er ging iets mis. Maak een foto van deze melding en stuur die in de chat.
pause
exit /b 1
