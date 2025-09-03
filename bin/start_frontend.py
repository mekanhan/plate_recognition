#!/usr/bin/env python3
"""Start the frontend server"""
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

# Start the frontend server
cmd = [python_exe, '-m', 'http.server', '8080', '--directory', 'frontend']

# Create log file with timestamp
from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f'logs/frontend_{timestamp}.log'

# Start in background
with open(log_file, 'w') as log:
    process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    print(f"Started frontend (PID: {process.pid}, Log: {log_file})")
    sys.exit(0)