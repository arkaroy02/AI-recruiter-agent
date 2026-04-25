@echo off
REM Talent Scout Studio - Windows setup

echo.
echo ================================================================
echo   Talent Scout Studio - FastAPI Setup
echo ================================================================
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required.
    echo         Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

echo.
echo [2/4] Checking Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama is not installed.
    echo         Download from: https://ollama.ai
    pause
    exit /b 1
)
echo [OK] Ollama installed

echo.
echo [3/4] Checking Ollama models...
ollama list | findstr /c:"tinyllama:latest" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Downloading tinyllama:latest...
    call ollama pull tinyllama:latest
)
echo [OK] tinyllama:latest available

ollama list | findstr /c:"gemma2:2b" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Downloading gemma2:2b...
    call ollama pull gemma2:2b
)
echo [OK] gemma2:2b available

ollama list | findstr /c:"nomic-embed" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Downloading nomic-embed-text:latest...
    call ollama pull nomic-embed-text:latest
)
echo [OK] nomic-embed-text:latest available

echo.
echo [4/4] Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

echo.
echo ================================================================
echo   Setup complete.
echo ================================================================
echo.
echo Next steps:
echo   1. Start Ollama: ollama serve
echo   2. Start the app: uvicorn webapp.main:app --reload --host 127.0.0.1 --port 8000
echo   3. Open: http://127.0.0.1:8000
echo.
pause
