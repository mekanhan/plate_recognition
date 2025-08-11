#!/usr/bin/env python3
"""
Simple Detection Dashboard Server
"""
import http.server
import socketserver
import os

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/mekanhan/github/learning/plate_recognition", **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    PORT = 8888
    
    try:
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            print(f"🖥️  Detection Dashboard: http://localhost:{PORT}/detection_dashboard.html")
            print("⏹️  Press Ctrl+C to stop")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error: {e}")