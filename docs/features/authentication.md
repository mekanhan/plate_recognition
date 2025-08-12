# JWT Authentication System

## Overview

The LPR system now includes a comprehensive JWT-based authentication system with Role-Based Access Control (RBAC) to secure all API endpoints.

## Features

### 🔐 Security Implementation
- **JWT Token Authentication** with configurable expiration times
- **Password Hashing** using PBKDF2 with random salt
- **Role-Based Access Control** with granular permissions
- **Secure Secret Management** with environment variables

### 👥 User Roles

#### Admin Role
- Full system access including user management
- Can create, update, and delete users
- Access to system configuration and diagnostics
- Emergency storage cleanup capabilities

#### Operator Role
- Can manage cameras and view all data
- Export detections and recordings
- System status monitoring
- No user management access

#### Viewer Role
- Read-only access to cameras and detections
- Can view recordings and system status
- Cannot modify system configuration

### 🛡️ Protected Endpoints

#### Camera Management
- `GET /api/cameras` - Requires `camera:view`
- `POST /api/cameras` - Requires `camera:manage` 
- `PUT /api/cameras/{id}` - Requires `camera:manage`
- `DELETE /api/cameras/{id}` - Requires admin role
- `POST /api/cameras/{id}/test` - Requires `camera:manage`

#### Detection Access
- `GET /api/detections/*` - Requires `detection:view`
- Detection search and analytics require viewer role or higher

#### System Administration
- `GET /api/system/health` - Requires `system:config`
- `POST /api/storage/cleanup` - Requires admin role
- `GET /api/cameras/{id}/diagnostics` - Requires admin role

## API Usage

### 1. Login and Get Token
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 43200,
  "role": "admin",
  "permissions": ["camera:view", "camera:manage", ...]
}
```

### 2. Use Token for API Requests
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/cameras
```

### 3. User Management (Admin Only)
```bash
# Create new user
curl -X POST http://localhost:8001/api/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "operator1", "password": "securepass", "role": "operator"}'

# List users
curl -H "Authorization: Bearer <admin-token>" \
  http://localhost:8001/api/users
```

## Configuration

### Environment Variables
Add to your `.env` file:

```env
# Authentication Settings
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_EXPIRE_MINUTES=720
ADMIN_PASSWORD=your-secure-admin-password
```

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123` (or value from `ADMIN_PASSWORD` env var)
- **⚠️ Change immediately in production!**

## Security Best Practices

### 1. Environment Setup
```bash
# Generate secure JWT key
openssl rand -hex 32

# Set in .env file
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "ADMIN_PASSWORD=$(openssl rand -base64 24)" >> .env
```

### 2. User Management
- Change default admin password immediately
- Create separate operator/viewer accounts for daily use
- Regularly rotate JWT secret keys
- Monitor user access logs

### 3. API Security
- Always use HTTPS in production
- Set appropriate token expiration times
- Implement rate limiting (future enhancement)
- Monitor authentication failures

## Implementation Details

### File Structure
```
auth/
├── __init__.py          # Module initialization
├── models.py            # User models and permissions
├── jwt_handler.py       # JWT token management
├── user_manager.py      # User CRUD operations
├── dependencies.py      # FastAPI dependencies
├── endpoints.py         # Authentication routes
└── middleware.py        # Security middleware
```

### Database Storage
- Users stored in `data/users.json`
- Passwords hashed with PBKDF2 + salt
- Simple file-based storage for MVP
- **Production**: Replace with database backend

### Integration Points
- Main API service includes auth routers
- All sensitive endpoints protected with dependencies
- Automatic user initialization on startup
- Health endpoints remain public for monitoring

## Testing

### Authentication Flow
```bash
# Test login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Test protected endpoint
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/system/health

# Test user creation (admin only)
curl -X POST http://localhost:8001/api/users \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"username": "viewer", "role": "viewer", "password": "viewpass"}'
```

### Permission Testing
```bash
# Test permission check
curl -X POST http://localhost:8001/api/auth/check-permission \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '"camera:manage"'
```

## Future Enhancements

### Planned Features
1. **Database Integration**: Replace file storage with SQLite/PostgreSQL
2. **Session Management**: Active session tracking and revocation
3. **Audit Logging**: Track user actions and access attempts
4. **Multi-Factor Authentication**: TOTP/SMS verification
5. **API Rate Limiting**: Prevent abuse and brute force attacks
6. **OAuth2 Integration**: Support for external identity providers

### Monitoring Integration
- Integrate with Prometheus for auth metrics
- Add authentication dashboard to web UI
- User activity tracking and reporting
- Security event alerting

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check token expiration
- Verify JWT secret key consistency
- Ensure Bearer token format

**403 Forbidden**
- User lacks required permissions
- Check role assignments
- Verify endpoint permission requirements

**Token Issues**
- JWT_SECRET_KEY changed after token generation
- Token tampering or corruption
- Clock skew between servers

### Debugging
```bash
# Check auth system health
curl http://localhost:8001/api/auth/health

# Verify current user info
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/auth/me

# Check permissions
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/auth/permissions
```