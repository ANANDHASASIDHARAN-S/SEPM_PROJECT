#!/bin/bash
# Start Script for ITPM Application - Production Use (Linux/Mac)

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database if needed
if [ ! -f "resource_allocation.db" ]; then
    echo "Initializing database..."
    python run.py init-db
fi

# Start Gunicorn
echo ""
echo "========================================"
echo "Starting ITPM Application"
echo "========================================"
echo ""
echo "Server: http://localhost:8000"
echo "Workers: 4"
echo ""

gunicorn -w 4 -b 0.0.0.0:8000 --access-logfile - --error-logfile - "app:create_app()"
