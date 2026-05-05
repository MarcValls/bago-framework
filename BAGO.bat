@echo off
:: ─────────────────────────────────────────────────────────────────
::  BAGO.bat — Windows: doble clic para abrir BAGO Shell
::  Abre una ventana cmd y lanza el shell interactivo.
:: ─────────────────────────────────────────────────────────────────
cd /d "%~dp0"

:: Detectar Python (python3, python, o py launcher)
where python3 >nul 2>&1 && set PY=python3 && goto :launch
where python  >nul 2>&1 && set PY=python  && goto :launch
where py      >nul 2>&1 && set PY=py      && goto :launch

echo [ERROR] Python no encontrado.
echo Instala Python desde https://python.org/downloads
pause
exit /b 1

:launch
title BAGO Shell
cls
%PY% bago
pause
