#!/bin/bash
echo "Removing existing virtual environment..."
rm -rf .venv

echo "Creating new virtual environment..."
uv venv .venv

echo "Virtual environment recreated successfully."
echo "To install packages, run: uv pip install -r requirements.min.txt --python .venv/Scripts/python" 