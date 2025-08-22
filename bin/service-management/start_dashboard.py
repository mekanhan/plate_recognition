#!/usr/bin/env python3
"""
Detection Dashboard Server
Serves the LPR detection dashboard on a local port
"""
import http.server
import socketserver
import webbrowser
import os
import signal
import sys
from threading import Timer

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/mekanhan/github/learning/plate_recognition", **kwargs)
    
    def end_headers(self):
        # Enable CORS for API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def open_browser():
    """Open browser after a short delay"""
    try:
        webbrowser.open('http://localhost:8888/detection_dashboard.html')
    except Exception:
        pass  # Ignore browser opening errors (e.g., in WSL)

def signal_handler(sig, frame):
    print('\n🛑 Shutting down dashboard server...')
    sys.exit(0)

if __name__ == "__main__":
    PORT = 8888
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            print("🖥️  LPR Detection Dashboard Server")
            print("=" * 50)
            print(f"📊 Dashboard URL: http://localhost:{PORT}/detection_dashboard.html")
            print(f"🌐 Server running on port {PORT}")
            print("⏹️  Press Ctrl+C to stop")
            print("=" * 50)
            
            # Open browser after 2 seconds
            Timer(2.0, open_browser).start()
            
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port or kill the existing process.")
        else:
            print(f"❌ Error starting server: {e}")
    except KeyboardInterrupt:
        print('\n🛑 Dashboard server stopped')
    except Exception as e:
        print(f"❌ Unexpected error: {e}")