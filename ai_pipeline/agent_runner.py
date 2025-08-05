#!/usr/bin/env python3
"""
Agent Runner - Bridges Claude agent with diagnostic tools
"""
import asyncio
import json
from camera_diagnostics_agent import CameraDiagnosticsAgent, CameraConfig

class AgentRunner:
    def __init__(self):
        self.diagnostics = CameraDiagnosticsAgent()
        
    async def run_diagnostic_from_prompt(self, user_input: dict):
        """
        Parse user input and run diagnostics
        Expected format:
        {
            "ip": "192.168.1.100",
            "username": "admin",
            "password": "password",
            "manufacturer": "hikvision"  # optional
        }
        """
        # Create camera config from user input
        config = CameraConfig(
            camera_id=f"cam_{user_input['ip'].replace('.', '_')}",
            name=user_input.get('name', f"Camera at {user_input['ip']}"),
            ip_address=user_input['ip'],
            username=user_input.get('username', 'admin'),
            password=user_input.get('password', ''),
            port=user_input.get('port', 554)
        )
        
        # Run diagnostics
        results = await self.diagnostics.diagnose_camera(config)
        
        # Format for Claude agent
        return self.format_for_claude(results)
    
    def format_for_claude(self, results):
        """Format diagnostic results for Claude agent"""
        formatted = {
            "status": "success" if results.get("working_config") else "failed",
            "summary": self.generate_summary(results),
            "working_config": results.get("working_config"),
            "network_status": self.extract_network_status(results),
            "recommendations": results.get("recommendations", [])
        }
        return formatted
    
    def generate_summary(self, results):
        """Generate human-readable summary"""
        if results.get("working_config"):
            config = results["working_config"]
            return f"✅ Successfully connected! Use: {config['url']}"
        else:
            return "❌ Could not establish connection to camera"
    
    def extract_network_status(self, results):
        """Extract network test results"""
        network_tests = results.get("network_tests", [])
        return {
            "ping": any(t.test_name == "ping" and t.success for t in network_tests),
            "ports_open": any(t.test_name == "port_scan" and t.success for t in network_tests),
            "http_interface": any(t.test_name == "http_interface" and t.success for t in network_tests)
        }