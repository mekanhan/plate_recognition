#!/usr/bin/env python3
"""
Quick test of authentication system
"""
import requests
import json

def test_authentication():
    print("🔐 Testing Simple Authentication System")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    # Test 1: Create admin user via quick setup
    print("1. Testing quick setup...")
    response = requests.post(f"{base_url}/api/auth/quick-setup", json={
        "username": "testadmin",
        "email": "test@lpr.local",
        "password": "TestPassword123!"
    })
    
    if response.status_code == 200:
        print("✅ Quick setup successful")
    elif response.status_code == 400 and "already exists" in response.text:
        print("ℹ️  User already exists - continuing with login test")
    else:
        print(f"❌ Quick setup failed: {response.status_code} - {response.text}")
        return False
    
    # Test 2: Login with created user
    print("\n2. Testing login...")
    response = requests.post(f"{base_url}/api/auth/login", json={
        "username": "testadmin", 
        "password": "TestPassword123!"
    })
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"   Token: {data['access_token'][:50]}...")
        print(f"   User: {data['user']}")
        token = data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    # Test 3: Get current user info
    print("\n3. Testing /me endpoint...")
    response = requests.get(f"{base_url}/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ User info retrieved successfully!")
        print(f"   User ID: {user_info['id']}")
        print(f"   Username: {user_info['username']}")
        print(f"   Role: {user_info['role']}")
    else:
        print(f"❌ Get user info failed: {response.status_code} - {response.text}")
        return False
    
    # Test 4: List users
    print("\n4. Testing list users...")
    response = requests.get(f"{base_url}/api/auth/users", headers={
        "Authorization": f"Bearer {token}"
    })
    
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Found {len(users)} users:")
        for user in users:
            print(f"   - {user['username']} ({user['role']})")
    else:
        print(f"❌ List users failed: {response.status_code} - {response.text}")
    
    print("\n🎉 Authentication system is working!")
    return True

if __name__ == "__main__":
    try:
        test_authentication()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")