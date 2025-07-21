# 🚀 Postman Setup Guide - Camera API Testing

## Quick Start (5 Minutes)

### 1. Import Files into Postman

**Import Collection:**
1. Open Postman
2. Click "Import" button (top left)
3. Select `Camera_API_Postman_Collection.json`
4. Click "Import"

**Import Environment:**
1. Click "Import" again
2. Select `Camera_API_Environment.json`
3. Click "Import"
4. Select the "Camera API Development Environment" from the environment dropdown (top right)

### 2. Start Your Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### 3. Verify Setup
1. Run: `📁 Health & Monitoring` → `GET All Locations`
2. Should return 200 with location data
3. If successful, you're ready to test!

---

## 🧪 Recommended Testing Order

### **Phase 1: Basic Functionality**
1. `GET All Locations` - Get valid location IDs
2. `GET List All Cameras` - See current cameras
3. `GET Camera by ID` - Test existing camera retrieval

### **Phase 2: Connection Testing (Your Real Camera)**
1. `🔍 Real Camera Discovery (10.0.0.181)` folder:
   - Run all stream path tests
   - Find which one works for your camera
   - Note the successful stream path

### **Phase 3: Camera Management**
1. `POST Create New Camera` - Add test camera
2. `PUT Update Camera` - Modify camera settings
3. `DELETE Camera` - Clean up test camera

### **Phase 4: Complete Workflow**
1. `🔄 Full Camera Lifecycle` - End-to-end test
2. All steps should pass for complete functionality

---

## 📊 Expected Results Guide

### ✅ Success Indicators
- **GET requests**: Status 200, valid JSON structure
- **POST Create**: Status 201, returns camera ID
- **PUT Update**: Status 200, shows updated data
- **DELETE**: Status 204, no content
- **Connection tests**: `"success": true` in response

### ❌ Common Issues & Solutions

**Issue: Connection timeouts**
```json
{
  "success": false,
  "detail": "Connection test timed out"
}
```
**Solution:** 
- Check if camera IP is reachable
- Verify credentials (admin/Mekus_1987)
- Try different stream paths

**Issue: 404 Camera Not Found**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND"
  }
}
```
**Solution:** Update `camera_id` in environment variables

**Issue: 409 Duplicate IP**
```json
{
  "error": {
    "code": "RESOURCE_CONFLICT"
  }
}
```
**Solution:** Use different IP address or delete existing camera

---

## 🎯 Testing Your Real Camera (10.0.0.181)

### Test Different Stream Paths:
1. `/stream1` (most common)
2. `/stream2` (alternative)
3. `/h264Preview_01_main` (Reolink)
4. `/live1.sdp` (generic)
5. `/axis-media/media.amp` (Axis)

### Find Working Configuration:
1. Run each test in "Real Camera Discovery" folder
2. Look for `"success": true` response
3. Note the working stream path
4. Update your camera with the working path

---

## 🔧 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `base_url` | API base URL | `http://localhost:8002/api` |
| `camera_id` | Existing camera ID | `065d0400-90ca-4f15-a25e-7adb001c2c18` |
| `location_id` | Valid location ID | `6d882a8a-2ad8-46d9-b254-987c5e5d5eba` |
| `test_ip` | Your camera IP | `10.0.0.181` |
| `test_username` | Camera username | `admin` |
| `test_password` | Camera password | `Mekus_1987` |

**To Update Variables:**
1. Click gear icon (⚙️) next to environment name
2. Modify values as needed
3. Save changes

---

## 📈 Advanced Testing

### Automated Testing:
1. Select collection/folder
2. Click "Run" button  
3. Configure iterations and delay
4. Run automated test suite

### Test Scripts:
Each request includes test scripts that verify:
- Correct HTTP status codes
- Response structure validation
- Required fields presence
- Success/failure conditions

### Export Results:
1. After running tests, click "Export Results"
2. Save as JSON/CSV for reporting

---

## 🚨 Troubleshooting

### Server Not Responding:
```bash
# Check if server is running
curl http://localhost:8002/api/cameras/
```

### Authentication Issues:
- Camera API currently doesn't require auth
- If 401 errors, check server logs

### Network Issues:
```bash
# Test camera reachability
ping 10.0.0.181

# Test port accessibility  
telnet 10.0.0.181 554
```

### Database Issues:
- Restart server to reinitialize database
- Check `data/license_plates.db` exists

---

## 📞 Support

If you encounter issues:
1. Check server logs for errors
2. Verify all environment variables are set
3. Ensure camera is powered and on network
4. Try different stream paths for your camera model

**Success Criteria:**
- ✅ All basic CRUD operations work (GET, POST, PUT, DELETE)
- ✅ Connection test finds working stream path for 10.0.0.181
- ✅ Camera can be created, updated, and deleted successfully
- ✅ Real camera shows proper status and stream configuration

---

*Test with confidence! 🚀*