#!/bin/bash
# Production startup script for Baign Mart

# Activate virtual environment
source /root/w/baign_mart/venv/bin/activate

# Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=0

# Run the application with gunicorn if available, otherwise use Flask's built-in server
if command -v gunicorn &> /dev/null; then
    echo "Starting with Gunicorn..."
    gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 run:app
else
    echo "Gunicorn not found. Starting with Flask development server in production mode..."
    python production.py
fi