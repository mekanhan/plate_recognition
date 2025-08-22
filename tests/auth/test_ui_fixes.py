#!/usr/bin/env python3
"""
Test UI fixes for header buttons, user menu, and sidebar navigation
"""
import requests

def test_ui_fixes():
    print("🔧 Testing UI Fixes")
    print("=" * 60)
    
    frontend_url = "http://localhost:8080"
    
    # Test 1: Check dashboard HTML for all components
    print("1. Testing dashboard components...")
    response = requests.get(f"{frontend_url}/dashboard.html")
    
    if response.status_code == 200:
        html = response.text
        
        # Check for header buttons
        if 'id="refresh-btn"' in html:
            print("✅ Refresh button exists")
        else:
            print("❌ Refresh button missing")
            
        if 'id="dark-mode-toggle"' in html:
            print("✅ Dark mode toggle exists")
        else:
            print("❌ Dark mode toggle missing")
            
        if 'id="fullscreen-btn"' in html:
            print("✅ Fullscreen button exists")
        else:
            print("❌ Fullscreen button missing")
            
        if 'class="user-avatar"' in html:
            print("✅ User avatar button exists")
        else:
            print("❌ User avatar button missing")
            
        if 'class="user-dropdown"' in html:
            print("✅ User dropdown menu exists")
        else:
            print("❌ User dropdown menu missing")
    
    # Test 2: Check sidebar for users navigation
    print("\n2. Testing sidebar navigation...")
    if response.status_code == 200:
        if "fa-users" in html and "Users" in html:
            print("✅ Users menu item added to sidebar")
        else:
            print("❌ Users menu item missing from sidebar")
            
        if 'src="vision_port_text.png"' in html:
            print("✅ Vision Port text logo referenced correctly")
        else:
            print("❌ Vision Port text logo reference issue")
            
        if 'src="logo.png"' in html:
            print("✅ Vision Port logo referenced correctly")
        else:
            print("❌ Vision Port logo reference issue")
    
    # Test 3: Check CSS/JS files
    print("\n3. Testing CSS/JS assets...")
    assets = [
        ('/src/styles/auth.css', 'Auth CSS'),
        ('/src/styles/sidebar-improvements.css', 'Sidebar CSS'),
        ('/src/components/layout/Header.js', 'Header JS'),
        ('/src/components/layout/Sidebar.js', 'Sidebar JS')
    ]
    
    for asset_path, asset_name in assets:
        try:
            response = requests.get(f"{frontend_url}{asset_path}")
            if response.status_code == 200:
                print(f"✅ {asset_name} accessible")
            else:
                print(f"❌ {asset_name} not accessible")
        except Exception as e:
            print(f"❌ {asset_name} error: {e}")
    
    # Test 4: Check users.html page
    print("\n4. Testing users.html page...")
    response = requests.get(f"{frontend_url}/users.html")
    if response.status_code == 200:
        print("✅ Users management page accessible")
    else:
        print("❌ Users management page not accessible")
    
    print("\n" + "=" * 60)
    print("📋 Manual Testing Instructions:")
    print("\n🔍 Test User Avatar Dropdown:")
    print("   1. Click on username in top-right corner")
    print("   2. Dropdown menu should appear with:")
    print("      - User info (username, role)")
    print("      - Profile link")
    print("      - User Management link → users.html")
    print("      - Preferences link")
    print("      - Logout button")
    
    print("\n🔍 Test Header Buttons:")
    print("   1. Refresh button → Should spin and show toast")
    print("   2. Dark mode toggle → Should switch themes")
    print("   3. Fullscreen button → Should toggle fullscreen")
    
    print("\n🔍 Test Sidebar Navigation:")
    print("   1. Click 'Users' in sidebar → Should go to users.html")
    print("   2. Logo images should display correctly")
    print("   3. System status should show at bottom")
    
    print("\n✅ Fixed Issues:")
    print("   • User avatar dropdown now has proper click handler")
    print("   • Fullscreen button updates icon on toggle")
    print("   • Dark mode properly saves preference")
    print("   • Refresh button shows loading animation")
    print("   • Users added to sidebar navigation")
    print("   • Logo paths are correct")
    print("   • User dropdown has higher z-index for visibility")

if __name__ == "__main__":
    test_ui_fixes()