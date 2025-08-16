# Postman API Testing - Troubleshooting Guide

## ✅ Services Are Now Running

The APIs are now working correctly:
- **Main API**: ✅ http://localhost:8001 
- **Recording API**: ✅ http://localhost:8002
- **Frontend**: ✅ http://localhost:8080

## 🔧 How to Fix the Authentication Issue

### Step 1: Login First
1. **Open the "Login" request** in the "🔐 Authentication & Users" folder
2. **Send the request** with default credentials:
   ```json
   {
     "username": "admin", 
     "password": "admin123"
   }
   ```
3. **Check the response** - you should get:
   ```json
   {
     "access_token": "eyJhbGci...",
     "token_type": "bearer",
     "expires_in": 43200,
     "role": "admin"
   }
   ```

### Step 2: Auto-Token Extraction
The collection has a **post-response script** that automatically extracts the JWT token and saves it to the environment variable `JWT_TOKEN`.

If it doesn't work automatically:

1. **Copy the `access_token`** from the login response
2. **Go to Environment Variables** (top right in Postman)
3. **Set `JWT_TOKEN`** to the copied token value

### Step 3: Test Authenticated Endpoints
Now try the "Get Recent Detections" request again - it should work!

## 🛠️ Manual Environment Setup

If you need to set up the environment manually:

| Variable | Value |
|----------|-------|
| `BASE_URL` | `http://localhost:8001` |
| `RECORDING_URL` | `http://localhost:8002` |
| `JWT_TOKEN` | `[Token from login response]` |
| `CAMERA_ID` | `entrance_cam` |
| `DETECTION_ID` | `[Any detection ID]` |

## 🧪 Test Sequence

**Recommended testing order:**

1. **Health Check** (`GET /health`) - No auth needed
2. **Login** (`POST /api/auth/login`) - Gets token
3. **Get All Cameras** (`GET /api/cameras`) - Uses token
4. **Get Recent Detections** (`GET /api/detections/recent`) - Should return `[]`
5. **Get Detection Stats** (`GET /api/detections/stats`) - Should show 0 counts

## 🐛 Common Issues & Solutions

### Issue: "ECONNRESET" Error
**Cause**: Services not running
**Solution**: Run `python3 start_lpr.py` in the project directory

### Issue: "401 Unauthorized"
**Cause**: Missing or expired JWT token
**Solution**: Re-run the login request to get a fresh token

### Issue: "404 Not Found"
**Cause**: Wrong endpoint URL
**Solution**: Check that `BASE_URL` is set to `http://localhost:8001`

### Issue: Empty Bearer Token
**Cause**: Token not extracted from login response
**Solution**: Manually copy token from login response to `JWT_TOKEN` variable

## 🔍 Testing Specific Features

### Camera Management
```bash
# 1. Get all cameras
GET {{BASE_URL}}/api/cameras

# 2. Create a test camera
POST {{BASE_URL}}/api/cameras
{
  "name": "Test Camera",
  "ip_address": "192.168.1.100",
  "port": 80,
  "connection_type": "http",
  "stream_path": "/mjpeg"
}

# 3. Get camera snapshot
GET {{BASE_URL}}/api/cameras/{{CAMERA_ID}}/snapshot
```

### Detection Management
```bash
# 1. Get recent detections (will be empty after cleanup)
GET {{BASE_URL}}/api/detections/recent?limit=10

# 2. Get detection statistics
GET {{BASE_URL}}/api/detections/stats

# 3. Get universal detection statistics
GET {{BASE_URL}}/api/v2/statistics
```

### Recording Service
```bash
# 1. Get recording status
GET {{RECORDING_URL}}/recordings/status

# 2. Get storage report
GET {{RECORDING_URL}}/api/v1/storage/report
```

## ✅ Expected Responses

After the recent database cleanup:

- **Detections**: Empty arrays `[]` or zero counts
- **Cameras**: Should show your configured cameras
- **Recording**: Should show active recording status
- **Health**: All services should show "healthy"

## 🎯 Working Example

Here's a working curl example you can compare with:

```bash
# 1. Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. Use token (replace YOUR_TOKEN with actual token)
curl http://localhost:8001/api/detections/recent?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Both should work identically in Postman!