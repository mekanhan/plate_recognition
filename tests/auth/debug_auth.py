#!/usr/bin/env python3
"""
Debug authentication system
"""
import requests
import json

def test_authentication():
    print("🔐 Debug Simple Authentication System")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    # Test login with both possible users
    users_to_test = [
        {"username": "admin", "password": "admin123"},
        {"username": "admin", "password": "AdminPassword123!"},
        {"username": "testadmin", "password": "TestPassword123!"}
    ]
    
    for i, user in enumerate(users_to_test, 1):
        print(f"\n{i}. Testing login with {user['username']}...")
        response = requests.post(f"{base_url}/api/auth/login", json=user)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            if 'user' in data:
                print(f"   User: {data['user']}")
            else:
                print(f"   Response: {data}")
            
            # Test /me endpoint
            print("\n   Testing /me endpoint...")
            me_response = requests.get(f"{base_url}/api/auth/me", headers={
                "Authorization": f"Bearer {data['access_token']}"
            })
            if me_response.status_code == 200:
                user_info = me_response.json()
                print("   ✅ User info retrieved successfully!")
                print(f"      User ID: {user_info['id']}")
                print(f"      Username: {user_info['username']}")
                print(f"      Role: {user_info['role']}")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
    
    return False

if __name__ == "__main__":
    try:
        test_authentication()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")