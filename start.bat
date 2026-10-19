@echo off
rem Doppelklick: installiert Pakete, fuehrt die In-Sample-Pipeline aus und oeffnet das Dashboard.
rem Details: docs\anleitung.md
cd /d "%~dp0"
where uv >nul 2>nul
if %errorlevel%==0 (set UV=uv) else (set UV=python -m uv)
%UV% sync || goto error
%UV% run python scripts/run_all.py %*
goto end
:error
echo.
echo Installation fehlgeschlagen. Ist Python 3.11+ und uv installiert? (pip install uv)
:end
pause
