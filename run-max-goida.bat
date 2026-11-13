@echo off
setlocal
echo Запуск MaxGoida через uv...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] uv не найден в PATH! Запуск через системный python...
    py main.py
) else (
    uv run python main.py
)
pause
