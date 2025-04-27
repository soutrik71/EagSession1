#!/bin/bash
# Set the certificate path
export SSL_CERT_FILE="C:/Users/40104002/AppData/Local/anaconda3/Lib/site-packages/certifi/cacert.pem"

# Set PYTHONPATH to include the langchain_mcp directory
export PYTHONPATH="$(pwd)"

echo "Running with PYTHONPATH=$PYTHONPATH"

# Run the servers
echo "Choose a server to run:"
echo "1. String Server"
echo "2. Calculator Server"
echo ""

read -p "Enter choice (1 or 2): " server_choice

if [ "$server_choice" = "1" ]; then
    echo "Starting String Server..."
    python server/string_server.py
elif [ "$server_choice" = "2" ]; then
    echo "Starting Calculator Server..."
    python server/calculator_server.py
else
    echo "Invalid choice"
fi

# Clean up
unset SSL_CERT_FILE
unset PYTHONPATH 