#!/bin/bash

# Sales Tracker Startup Script

echo "Starting Sales Tracker..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the Flask app
echo ""
echo "=========================================="
echo "Sales Tracker is starting..."
echo "Open your browser and go to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

python app.py
