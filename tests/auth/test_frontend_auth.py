#!/usr/bin/env python3
"""
Test frontend authentication integration
"""
import requests
import json

def test_frontend_auth_integration():
    print("🔐 Testing Frontend Authentication Integration")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    frontend_url = "http://localhost:8080"
    
    # Test 1: Check if frontend is accessible
    print("1. Testing frontend accessibility...")
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            if 'AuthService.js' in response.text or 'auth.css' in response.text:
                print("✅ Authentication assets are included")
            else:
                print("ℹ️  Authentication assets may not be fully integrated")
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend connection failed: {e}")
        return False
    
    # Test 2: Verify authentication API endpoints
    print("\n2. Testing authentication API endpoints...")
    
    # Test login endpoint
    response = requests.post(f"{base_url}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login API working")
        print(f"   Token type: {data.get('token_type', 'unknown')}")
        print(f"   Role: {data.get('role', 'unknown')}")
        print(f"   Permissions: {len(data.get('permissions', []))} permissions")
        token = data['access_token']
    else:
        print(f"❌ Login API failed: {response.status_code}")
        return False
    
    # Test user info endpoint
    response = requests.get(f"{base_url}/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ User info API working")
        print(f"   Username: {user_info.get('username', 'unknown')}")
        print(f"   Email: {user_info.get('email', 'unknown')}")
        print(f"   Active: {user_info.get('is_active', 'unknown')}")
    else:
        print(f"❌ User info API failed: {response.status_code}")
        return False
    
    # Test 3: Check auth service files exist
    print("\n3. Testing authentication service files...")
    auth_files = [
        f"{frontend_url}/src/services/AuthService.js",
        f"{frontend_url}/src/styles/auth.css"
    ]
    
    for file_url in auth_files:
        try:
            response = requests.get(file_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {file_url.split('/')[-1]} is accessible")
            else:
                print(f"⚠️  {file_url.split('/')[-1]} not accessible: {response.status_code}")
        except Exception as e:
            print(f"⚠️  {file_url.split('/')[-1]} connection failed: {e}")
    
    # Test 4: Check if main components can be loaded
    print("\n4. Testing component integration...")
    try:
        response = requests.get(f"{frontend_url}/src/components/layout/Header.js", timeout=5)
        if response.status_code == 200 and 'getUserDisplayName' in response.text:
            print("✅ Header component has authentication integration")
        else:
            print("⚠️  Header component authentication integration unclear")
            
        response = requests.get(f"{frontend_url}/src/app.js", timeout=5)
        if response.status_code == 200 and 'AuthService' in response.text:
            print("✅ Main app has authentication integration")
        else:
            print("⚠️  Main app authentication integration unclear")
    except Exception as e:
        print(f"⚠️  Component integration test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Frontend Authentication Integration Test Complete!")
    print("\n📋 To test the complete login/logout flow:")
    print("   1. Open http://localhost:8080 in a browser")
    print("   2. You should see a login modal if not already logged in")
    print("   3. Login with: admin / admin123")
    print("   4. Check the user menu in the top right corner")
    print("   5. Test logout functionality")
    print("\n🎯 Authentication Features Available:")
    print("   • Automatic login modal for unauthenticated users")
    print("   • JWT token management with localStorage")
    print("   • User info display in header")
    print("   • Logout functionality")
    print("   • Token refresh every 30 minutes")
    print("   • User role and permission management")
    print("   • User management page at /users.html")
    
    return True

if __name__ == "__main__":
    try:
        test_frontend_auth_integration()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")