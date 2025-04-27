#!/bin/bash
# Set the SSL certificate path to the certifi path
export SSL_CERT_FILE="C:/Users/40104002/AppData/Local/anaconda3/Lib/site-packages/certifi/cacert.pem"
echo "Using certificate at: $SSL_CERT_FILE"

# Check if .venv exists, create it if it doesn't
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
fi

# Run the script with uv using the virtual environment
uv run --python .venv/Scripts/python "$@"

# Clear the environment variable when done
unset SSL_CERT_FILE 