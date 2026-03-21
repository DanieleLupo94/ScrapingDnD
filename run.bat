@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║      D&D 4e Database Scraper - Menu Principale           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:check_python
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto python_found
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto python_found
)

echo ❌ Python non trovato! Installa Python 3.7 o superiore
echo    Scarica da: https://www.python.org/downloads/
pause
exit /b 1

:python_found
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PY_VERSION=%%i
echo ✓ Python trovato: %PY_VERSION%

:menu
echo.
echo Cosa vuoi fare?
echo 1) Installa dipendenze
echo 2) Scarica database (scraper SAFE - CONSIGLIATO) ⭐
echo 3) Scarica database (scraper avanzato con resume)
echo 4) Scarica database (scraper base)
echo 5) Parsa i dati scaricati (da JS a JSON)
echo 6) Tutto in uno (download SAFE + parsing)
echo 7) Esci
echo.

set /p choice="Scelta [1-7]: "

if "%choice%"=="1" goto install_deps
if "%choice%"=="2" goto run_safe
if "%choice%"=="3" goto run_advanced
if "%choice%"=="4" goto run_basic
if "%choice%"=="5" goto run_parser
if "%choice%"=="6" goto run_all
if "%choice%"=="7" goto exit
goto invalid_choice

:install_deps
echo.
echo 📦 Installazione dipendenze...
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo ✓ Dipendenze installate con successo
) else (
    echo ❌ Errore nell'installazione delle dipendenze
)
pause
goto menu

:run_safe
echo.
echo 🚀 Avvio scraper SAFE (no loop, consigliato)...
echo.
%PYTHON_CMD% dnd_scraper_safe.py
pause
goto menu

:run_basic
echo.
echo 🚀 Avvio scraper base...
echo.
%PYTHON_CMD% dnd_scraper.py
pause
goto menu

:run_advanced
echo.
echo 🚀 Avvio scraper avanzato (con resume)...
echo.
%PYTHON_CMD% dnd_scraper_advanced.py
pause
goto menu

:run_parser
echo.
echo 🔍 Avvio parser dei dati...
echo.
%PYTHON_CMD% dnd_parser.py
pause
goto menu

:run_all
echo.
echo 🚀 Processo completo in corso...
echo.
%PYTHON_CMD% dnd_scraper_safe.py
if %errorlevel% equ 0 (
    echo.
    echo ✓ Download completato, avvio parsing...
    echo.
    %PYTHON_CMD% dnd_parser.py
) else (
    echo ❌ Download fallito, parsing saltato
)
pause
goto menu

:invalid_choice
echo ❌ Scelta non valida
pause
goto menu

:exit
echo.
echo 👋 Arrivederci!
echo.
pause
exit /b 0
