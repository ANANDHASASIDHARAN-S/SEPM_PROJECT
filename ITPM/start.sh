#!/bin/bash

echo "Resource Allocation & Workforce Planning System"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade requirements
echo "Installing requirements..."
pip install -r requirements.txt -q

# Initialize database if needed
if [ ! -f "resource_allocation.db" ]; then
    echo "Initializing database with sample data..."
    python run.py init-db
fi

# Start the application
echo ""
echo "Starting application..."
echo "Open http://localhost:5000 in your browser"
echo ""
python run.py
