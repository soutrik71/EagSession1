@echo off
REM Set the SSL certificate path to the certifi path
set SSL_CERT_FILE=C:\Users\40104002\AppData\Local\anaconda3\Lib\site-packages\certifi\cacert.pem
echo Using certificate at: %SSL_CERT_FILE%

REM Check if .venv exists, create it if it doesn't
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv .venv
)

REM Run the script with uv using the virtual environment
uv run --python .venv\Scripts\python.exe %*

REM Clear the environment variable when done
set SSL_CERT_FILE= 