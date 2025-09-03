#!/usr/bin/env python3
"""
Service monitor with auto-restart capability
Checks services every 30 seconds and restarts if down
"""
import os
import sys
import time
import subprocess
import logging
from datetime import datetime
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/service_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('service_monitor')

# Service definitions
SERVICES = {
    'main_api': {
        'port': 8001,
        'health_endpoint': '/api/system/health',
        'start_command': ['python3', 'bin/start_main_api.py']
    },
    'recording_service': {
        'port': 8002,
        'health_endpoint': '/health',
        'start_command': ['python3', 'bin/start_recording_service.py']
    },
    'frontend': {
        'port': 8080,
        'health_endpoint': '/',
        'start_command': ['python3', 'bin/start_frontend.py']
    }
}

# Check interval in seconds
CHECK_INTERVAL = 30
MAX_RESTART_ATTEMPTS = 3
RESTART_COOLDOWN = 60  # Wait before next restart attempt

# Track restart attempts
restart_attempts = {}
last_restart_time = {}

def check_service_health(port, endpoint):
    """Check if a service is healthy"""
    try:
        import requests
        response = requests.get(f'http://localhost:{port}{endpoint}', timeout=5)
        return response.status_code < 500
    except:
        return False

def restart_service(service_name, config):
    """Restart a service"""
    global restart_attempts, last_restart_time
    
    current_time = time.time()
    
    # Check cooldown period
    if service_name in last_restart_time:
        elapsed = current_time - last_restart_time[service_name]
        if elapsed < RESTART_COOLDOWN:
            logger.warning(f"Skipping restart of {service_name} (cooldown: {RESTART_COOLDOWN - elapsed:.0f}s remaining)")
            return False
    
    # Check restart attempts
    if service_name not in restart_attempts:
        restart_attempts[service_name] = 0
    
    if restart_attempts[service_name] >= MAX_RESTART_ATTEMPTS:
        logger.error(f"Max restart attempts ({MAX_RESTART_ATTEMPTS}) reached for {service_name}")
        return False
    
    logger.warning(f"Attempting to restart {service_name} (attempt {restart_attempts[service_name] + 1}/{MAX_RESTART_ATTEMPTS})")
    
    try:
        # Run start command
        result = subprocess.run(
            config['start_command'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully restarted {service_name}")
            restart_attempts[service_name] += 1
            last_restart_time[service_name] = current_time
            return True
        else:
            logger.error(f"Failed to restart {service_name}: {result.stderr}")
            restart_attempts[service_name] += 1
            last_restart_time[service_name] = current_time
            return False
    except Exception as e:
        logger.error(f"Error restarting {service_name}: {e}")
        restart_attempts[service_name] += 1
        last_restart_time[service_name] = current_time
        return False

def reset_restart_counts():
    """Reset restart counts periodically (every hour)"""
    global restart_attempts
    restart_attempts = {}
    logger.info("Reset restart attempt counters")

def monitor_loop():
    """Main monitoring loop"""
    logger.info("Starting service monitor (checking every {}s)".format(CHECK_INTERVAL))
    
    last_reset = time.time()
    
    while True:
        try:
            # Reset counters every hour
            if time.time() - last_reset > 3600:
                reset_restart_counts()
                last_reset = time.time()
            
            # Check each service
            for service_name, config in SERVICES.items():
                if not check_service_health(config['port'], config['health_endpoint']):
                    logger.warning(f"{service_name} is DOWN on port {config['port']}")
                    restart_service(service_name, config)
                else:
                    # Reset attempts on successful check
                    if service_name in restart_attempts and restart_attempts[service_name] > 0:
                        logger.info(f"{service_name} is healthy, resetting restart counter")
                        restart_attempts[service_name] = 0
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(CHECK_INTERVAL)

def handle_signal(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down monitor")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    # Check if running as daemon
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        # Fork to background
        try:
            pid = os.fork()
            if pid > 0:
                print(f"Monitor started in background (PID: {pid})")
                sys.exit(0)
        except OSError as e:
            logger.error(f"Fork failed: {e}")
            sys.exit(1)
        
        # Redirect outputs to log file
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
    
    monitor_loop()