@echo off
REM Continuous Learning Pipeline Runner for Windows
REM This script runs the model training pipeline on a schedule

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set LOG_DIR=%PROJECT_ROOT%\logs
set VENV_PATH=%PROJECT_ROOT%\.venv

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Log file with timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOG_FILE=%LOG_DIR%\continuous_learning_%datetime:~0,8%_%datetime:~8,6%.log

REM Function to log messages
:log
echo [%date% %time%] %~1 | tee -a "%LOG_FILE%"
goto :eof

call :log "Starting continuous learning pipeline"

REM Check if virtual environment exists
if not exist "%VENV_PATH%" (
    call :log "Creating virtual environment..."
    python -m venv "%VENV_PATH%"
)

REM Activate virtual environment
call :log "Activating virtual environment..."
call "%VENV_PATH%\Scripts\activate.bat"

REM Install dependencies if requirements.txt exists
if exist "%PROJECT_ROOT%\requirements.txt" (
    call :log "Installing dependencies..."
    pip install -r "%PROJECT_ROOT%\requirements.txt" >> "%LOG_FILE%" 2>&1
)

REM Additional ML dependencies
call :log "Installing ML dependencies..."
pip install pandas numpy scikit-learn transformers torch >> "%LOG_FILE%" 2>&1

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Run the training pipeline
call :log "Running model training pipeline..."
python "%SCRIPT_DIR%model_training_pipeline.py" >> "%LOG_FILE%" 2>&1

REM Check exit status
if %ERRORLEVEL% EQU 0 (
    call :log "Pipeline completed successfully"
    
    REM Optional: Send success notification (uncomment and configure as needed)
    REM curl -X POST -H "Content-type: application/json" --data "{\"text\":\"RoleReady continuous learning pipeline completed successfully\"}" %SLACK_WEBHOOK_URL%
    
) else (
    call :log "Pipeline failed with exit code %ERRORLEVEL%"
    
    REM Optional: Send failure notification (uncomment and configure as needed)
    REM curl -X POST -H "Content-type: application/json" --data "{\"text\":\"RoleReady continuous learning pipeline failed. Check logs.\"}" %SLACK_WEBHOOK_URL%
    
    exit /b 1
)

call :log "Continuous learning pipeline finished"

REM Clean up old log files (keep last 30 days)
forfiles /p "%LOG_DIR%" /m "continuous_learning_*.log" /d -30 /c "cmd /c del @path" 2>nul

call :log "Log cleanup completed"

endlocal
