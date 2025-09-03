#!/usr/bin/env python3
"""Start the main API service"""
import subprocess
import sys
import os

# Get project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

# Determine Python executable
if os.path.exists('.venv/bin/python3'):
    python_exe = '.venv/bin/python3'
else:
    python_exe = sys.executable

# Start the main API
cmd = [
    python_exe, '-m', 'uvicorn',
    'api.main:app',
    '--host', '0.0.0.0',
    '--port', '8001',
    '--reload'
]

# Create log file with timestamp
from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f'logs/main_api_{timestamp}.log'

# Start in background
with open(log_file, 'w') as log:
    process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    print(f"Started main API (PID: {process.pid}, Log: {log_file})")
    sys.exit(0)