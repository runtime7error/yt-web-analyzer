@echo off
chcp 65001 > nul
title YT Web Analyzer - API de Download e Análise

echo ======================================================
echo    YT Web Analyzer - API de Download e Análise
echo ======================================================
echo.

where py >nul 2>nul
if %errorlevel% neq 0 (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERRO] Python não foi encontrado no sistema.
        pause
        exit /b 1
    )
    set PY_CMD=python
) else (
    set PY_CMD=py
)

echo [1/2] Verificando dependências...
%PY_CMD% -m pip install -r "%~dp0requirements.txt" --quiet

echo [2/2] Liberando porta 8000 e iniciando servidor...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

echo Acesse: http://localhost:8000/docs (Swagger UI)
echo Health: http://localhost:8000/health
echo.

%PY_CMD% -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

pause
