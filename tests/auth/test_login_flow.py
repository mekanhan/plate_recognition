#!/usr/bin/env python3
"""
Test login and dashboard navigation flow
"""
import requests
import json
import time

def test_login_flow():
    print("🔐 Testing Login and Dashboard Navigation Flow")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    frontend_url = "http://localhost:8080"
    
    # Step 1: Clear any existing authentication
    print("1. Starting fresh (no existing authentication)...")
    
    # Step 2: Login via API
    print("\n2. Testing login via API...")
    response = requests.post(f"{base_url}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data['access_token']
        print("✅ Login successful!")
        print(f"   Token: {token[:50]}...")
        print(f"   Role: {data.get('role', 'unknown')}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        return False
    
    # Step 3: Verify token works with /me endpoint
    print("\n3. Verifying token with /me endpoint...")
    response = requests.get(f"{base_url}/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    
    if response.status_code == 200:
        user_data = response.json()
        print("✅ Token is valid!")
        print(f"   User: {user_data.get('username', 'unknown')}")
        print(f"   Email: {user_data.get('email', 'unknown')}")
        print(f"   Active: {user_data.get('is_active', 'unknown')}")
    else:
        print(f"❌ Token validation failed: {response.status_code}")
        return False
    
    # Step 4: Check if dashboard is accessible
    print("\n4. Checking dashboard accessibility...")
    response = requests.get(f"{frontend_url}/dashboard.html")
    
    if response.status_code == 200:
        print("✅ Dashboard HTML is accessible")
        
        # Check for key elements
        if 'LPR Security System - Dashboard' in response.text:
            print("✅ Dashboard has correct title")
        
        if 'src/app.js' in response.text:
            print("✅ Dashboard loads app.js")
            
        if 'AuthService' in response.text or 'auth' in response.text.lower():
            print("✅ Dashboard includes authentication components")
    else:
        print(f"❌ Dashboard not accessible: {response.status_code}")
    
    # Step 5: Instructions for browser testing
    print("\n" + "=" * 60)
    print("📋 Manual Browser Test Instructions:")
    print("\n1. Open Chrome/Firefox Developer Tools (F12)")
    print("2. Go to Application/Storage → Local Storage")
    print("3. Clear any existing 'lpr_auth_token' entries")
    print("4. Navigate to: http://localhost:8080")
    print("5. Click 'Login' button")
    print("6. Enter credentials: admin / admin123")
    print("7. Watch the Console tab for debug messages")
    print("\n🔍 Expected Console Output:")
    print("   - 'Login successful, token stored: ...'")
    print("   - 'Redirecting to dashboard.html'")
    print("   - 'Initializing authentication...'")
    print("   - 'User authenticated successfully'")
    print("\n⚠️  If Dashboard Redirects Back to Homepage:")
    print("   - Check Console for 'Token validation failed' errors")
    print("   - Verify the /api/auth/me endpoint is working")
    print("   - Check if token is properly stored in localStorage")
    print("\n🔧 Debug Steps:")
    print("   1. Open http://localhost:8080/test_auth_flow.html")
    print("   2. Click 'Test Login' to store a valid token")
    print("   3. Click 'Go to Dashboard' to test navigation")
    print("   4. Check if dashboard loads or redirects")
    
    return True

if __name__ == "__main__":
    try:
        test_login_flow()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")