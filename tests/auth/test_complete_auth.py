#!/usr/bin/env python3
"""
Complete authentication system test
"""
import requests
import json

def test_authentication():
    print("🔐 Testing Complete Authentication System")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    # Test 1: Login with existing admin user
    print("1. Testing login with existing admin user...")
    response = requests.post(f"{base_url}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"   Token: {data['access_token'][:50]}...")
        print(f"   Role: {data.get('role', 'Unknown')}")
        print(f"   Permissions: {len(data.get('permissions', []))} permissions")
        token = data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    # Test 2: Get current user info
    print("\n2. Testing /me endpoint...")
    response = requests.get(f"{base_url}/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ User info retrieved successfully!")
        print(f"   Username: {user_info.get('username', 'Unknown')}")
        print(f"   Email: {user_info.get('email', 'Unknown')}")
        print(f"   Role: {user_info.get('role', 'Unknown')}")
        print(f"   Active: {user_info.get('is_active', 'Unknown')}")
    else:
        print(f"❌ Get user info failed: {response.status_code} - {response.text}")
        return False
    
    # Test 3: List users
    print("\n3. Testing list users...")
    response = requests.get(f"{base_url}/api/auth/users", headers={
        "Authorization": f"Bearer {token}"
    })
    
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Found {len(users)} users:")
        for user in users:
            print(f"   - {user.get('username', 'Unknown')} ({user.get('role', 'Unknown')})")
    else:
        print(f"❌ List users failed: {response.status_code} - {response.text}")
    
    # Test 4: Test quick setup with new user
    print("\n4. Testing quick setup with new user...")
    response = requests.post(f"{base_url}/api/auth/quick-setup", json={
        "username": "testuser2",
        "email": "test2@lpr.local",
        "password": "TestPassword123!"
    })
    
    if response.status_code == 200:
        print("✅ Quick setup successful for new user!")
    elif response.status_code == 400 and "already exists" in response.text:
        print("ℹ️  User already exists - that's fine")
    else:
        print(f"❌ Quick setup failed: {response.status_code} - {response.text}")
    
    # Test 5: Check auth health
    print("\n5. Testing auth health endpoint...")
    response = requests.get(f"{base_url}/api/auth/health")
    
    if response.status_code == 200:
        health = response.json()
        print("✅ Auth health check successful!")
        print(f"   Service: {health.get('service', 'Unknown')}")
        print(f"   Status: {health.get('status', 'Unknown')}")
        print(f"   Users: {health.get('user_count', 'Unknown')}")
    else:
        print(f"❌ Auth health failed: {response.status_code} - {response.text}")
    
    print("\n🎉 Authentication system testing completed!")
    return True

if __name__ == "__main__":
    try:
        test_authentication()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")