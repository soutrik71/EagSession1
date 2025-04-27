@echo off
REM Set the certificate path
set SSL_CERT_FILE=C:\Users\40104002\AppData\Local\anaconda3\Lib\site-packages\certifi\cacert.pem

REM Set PYTHONPATH to include the langchain_mcp directory
set PYTHONPATH=%cd%

echo Running with PYTHONPATH=%PYTHONPATH%

REM Run the servers
echo Choose a server to run:
echo 1. String Server
echo 2. Calculator Server
echo.

set /p server_choice=Enter choice (1 or 2): 

if "%server_choice%"=="1" (
    echo Starting String Server...
    python server/string_server.py
) else if "%server_choice%"=="2" (
    echo Starting Calculator Server...
    python server/calculator_server.py
) else (
    echo Invalid choice
)

REM Clean up
set SSL_CERT_FILE=
set PYTHONPATH= 