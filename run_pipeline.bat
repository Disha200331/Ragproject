@echo off
REM RAG Pipeline Startup Script

title RAG Pipeline - Startup
color 0A

echo.
echo ================================================================
echo   RAG PIPELINE STARTUP SCRIPT
echo ================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/4] Checking dependencies...
python verify_setup.py
if errorlevel 1 (
    echo.
    echo [ERROR] Setup verification failed
    echo Please fix the issues above
    pause
    exit /b 1
)

echo.
echo [2/4] Starting Ollama (in new window)...
echo        If Ollama is already running, close this message
timeout /t 2
start "Ollama Server" cmd /k "ollama serve"

echo.
echo [3/4] Starting Neo4j (in new window)...
echo        If Neo4j is already running, close this message
timeout /t 2
start "Neo4j Database" cmd /k "restart_neo4j.bat"

echo.
echo [4/4] Waiting for services to start...
echo        Checking connections (timeout: 30s)...
timeout /t 5

echo.
echo ================================================================
echo   RUNNING RAG PIPELINE
echo ================================================================
echo.

python rag_pipeline.py --rebuild

if errorlevel 1 (
    echo.
    echo [ERROR] Pipeline failed
    echo Check the error messages above
    pause
    exit /b 1
) else (
    echo.
    echo [SUCCESS] Pipeline completed!
    echo.
    echo Access Neo4j Browser at: http://localhost:7474
    echo Username: neo4j
    echo.
    pause
)
