@echo off
chcp 65001 > nul

:: Verificar se ja e administrador
net session > nul 2>&1
if %ERRORLEVEL% equ 0 goto :admin

:: Nao e admin: reabrir esta janela como administrador
powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
exit /b 0

:admin
cd /d "%~dp0"
cls
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
