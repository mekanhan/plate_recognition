# Development Notes & Best Practices

## Critical Learning Points

### 1. UI Development Struggles & Solutions

#### Modal Issues Pattern
**Problem**: Modals not responding to clicks, retaining state, or not closing properly

**Root Causes**:
- Event listeners attached to wrong elements
- State not properly reset between opens
- Child element clicks not bubbling correctly

**Solution Pattern**:
```javascript
// ALWAYS use this pattern for modal buttons
modal.addEventListener('click', (e) => {
    const saveBtn = e.target.closest('.save-button');
    const cancelBtn = e.target.closest('.cancel-button');
    
    if (saveBtn) {
        // Handle save
    } else if (cancelBtn) {
        // Handle cancel
    }
});

// ALWAYS reset state completely
function openModal() {
    // Clear all forms
    modal.querySelectorAll('input').forEach(input => input.value = '');
    // Reset all error states
    modal.querySelectorAll('.error').forEach(err => err.remove());
    // Reload data if needed
    loadFreshData();
}
```

#### Event Delegation Issues
**Problem**: Dynamically added elements not responding to events

**Solution**:
```javascript
// DON'T do this
button.addEventListener('click', handler);

// DO this for dynamic elements
parentContainer.addEventListener('click', (e) => {
    if (e.target.closest('.dynamic-button')) {
        handler(e);
    }
});
```

### 2. Database Migration Anti-Patterns

#### Breaking Changes
**NEVER DO**:
```python
# This breaks existing code
alter_column('cameras', 'ip', new_name='ip_address')
```

**ALWAYS DO**:
```python
# Add new column with default
add_column('cameras', Column('ip_address', String, default=''))
# Keep old column for compatibility
# Use facade pattern in code
```

#### Session Management
**NEVER DO**:
```python
# Mixing sync and async
with SessionLocal() as session:  # Sync
    await session.execute(...)    # Async - BREAKS!
```

**ALWAYS DO**:
```python
# Use async consistently
async with AsyncSessionLocal() as session:
    await session.execute(...)
```

### 3. Service Architecture Patterns

#### Dependency Management
**Problem**: Services starting before dependencies ready

**Solution**:
```python
async def wait_for_dependency(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return True
        except:
            pass
        await asyncio.sleep(1)
    raise TimeoutError(f"Dependency {url} not ready")

# In service startup
await wait_for_dependency("http://localhost:8001/health")
```

#### Health Check Pattern
**Always Include**:
```python
@app.get("/health")
async def health_check():
    checks = {
        "service": "healthy",
        "database": await check_database(),
        "dependencies": await check_dependencies(),
        "timestamp": datetime.utcnow()
    }
    
    if all(v == "healthy" for v in checks.values() if isinstance(v, str)):
        return JSONResponse(checks, status_code=200)
    return JSONResponse(checks, status_code=503)
```

### 4. Testing Discipline

#### The Testing Mantra
**NEVER** claim something works without:

1. **Syntax Check**
   ```bash
   python3 -m py_compile file.py
   ```

2. **Import Test**
   ```bash
   python3 -c "from module import function"
   ```

3. **Service Test**
   ```bash
   python3 bin/check_services.py
   ```

4. **Endpoint Test**
   ```bash
   curl http://localhost:8001/endpoint
   ```

5. **Stability Test**
   ```bash
   # Watch logs for 5+ minutes
   tail -f logs/*.log
   ```

6. **Integration Test**
   - Actually use the UI
   - Test the full workflow
   - Check database changes

### 5. Common Gotchas

#### Frontend State Management
**Problem**: UI shows stale data after operations

**Solution**:
```javascript
// Always refresh after mutations
async function saveCamera(data) {
    await api.updateCamera(data);
    await loadCameras();  // Refresh list
    updateUI();          // Update display
}
```

#### Async/Await Pitfalls
**Problem**: Forgetting await causes silent failures

**Solution**:
```python
# WRONG - Returns coroutine, doesn't execute
def get_data():
    return fetch_from_db()  # Missing await!

# RIGHT
async def get_data():
    return await fetch_from_db()
```

#### Environment Variables
**Problem**: Missing config causes cryptic errors

**Solution**:
```python
# Always provide defaults and validate
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET_KEY must be set!")
```

### 6. Performance Patterns

#### Database Queries
**DON'T**:
```python
# N+1 query problem
cameras = session.query(Camera).all()
for camera in cameras:
    recordings = session.query(Recording).filter_by(camera_id=camera.id).all()
```

**DO**:
```python
# Single query with join
cameras = session.query(Camera).options(
    joinedload(Camera.recordings)
).all()
```

#### Caching Strategy
```python
# Simple in-memory cache
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_camera_config(camera_id):
    return fetch_from_db(camera_id)

# Clear cache periodically
def clear_cache():
    get_camera_config.cache_clear()
```

### 7. Security Checklist

#### Authentication
- ✅ Never store plain passwords
- ✅ Use secure random tokens
- ✅ Implement token expiration
- ✅ Validate on every request
- ✅ Use HTTPS in production

#### API Security
- ✅ Validate all inputs
- ✅ Use parameterized queries
- ✅ Implement rate limiting
- ✅ Log security events
- ✅ Sanitize error messages

#### Configuration
- ✅ Never commit secrets
- ✅ Use environment variables
- ✅ Provide .env.example
- ✅ Rotate keys regularly
- ✅ Use different keys per environment

### 8. Debugging Techniques

#### The Console.log Strategy
```javascript
// Trace execution flow
console.log('1. Starting function');
console.log('2. Data received:', data);
console.log('3. Processing complete');
```

#### The Binary Search Method
- Comment out half the code
- If error persists, problem in remaining half
- Repeat until found

#### The Checkpoint Method
```python
print("✓ Checkpoint 1: Database connected")
print("✓ Checkpoint 2: Data loaded")
print("✗ Checkpoint 3: Processing failed")
```

### 9. Code Review Checklist

Before claiming completion:
- [ ] Code runs without errors
- [ ] All imports work
- [ ] Services start successfully
- [ ] API endpoints respond
- [ ] UI functions properly
- [ ] No errors in logs
- [ ] Database operations complete
- [ ] Tests pass
- [ ] Documentation updated

### 10. Recovery Procedures

#### When Everything Breaks
1. **Check logs first**
   ```bash
   tail -f logs/*.log
   ```

2. **Verify services**
   ```bash
   python3 bin/check_services.py
   ```

3. **Test database**
   ```bash
   sqlite3 data/license_plates.db "SELECT COUNT(*) FROM cameras;"
   ```

4. **Reset and restart**
   ```bash
   python3 bin/stop_all_services.py
   python3 bin/start_lpr.py
   ```

5. **Check dependencies**
   ```bash
   pip3 list | grep -E "fastapi|sqlalchemy|opencv"
   ```

#### Database Corruption
```bash
# Backup first
cp data/license_plates.db data/license_plates.backup.db

# Check integrity
sqlite3 data/license_plates.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
cp data/license_plates.backup.db data/license_plates.db
```

#### Service Won't Stop
```bash
# Find process
ps aux | grep python

# Force kill
kill -9 <PID>

# Or kill all Python
pkill -9 python3
```

## Summary

These notes represent hard-won knowledge from debugging and fixing numerous issues. Following these patterns will prevent most common problems and speed up development significantly.

**Golden Rules**:
1. Test everything before claiming it works
2. Never break existing functionality
3. Always provide migration paths
4. Document unusual solutions
5. Clean up after yourself

**Remember**: It's better to over-test than under-test. A working system with comprehensive tests is worth more than a "perfect" system that might break.