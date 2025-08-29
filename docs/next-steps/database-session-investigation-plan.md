# Database Session Investigation Plan

## Problem Statement

Despite fixing 32+ API endpoints with dependency injection, detection-related endpoints still experience database session binding errors:

```
Could not locate a bind configured on mapper Mapper[Detection(detections)], SQL expression or this Session.
Could not locate a bind configured on mapper Mapper[Camera(cameras)], SQL expression or this Session.
```

## Investigation Areas

### 1. Session Architecture Analysis

#### Current Implementation Review
**Files to Investigate**:
- `database/db_config.py` - Core session configuration
- `database/service.py` - DatabaseService session management  
- `api/main.py` - Endpoint dependency injection patterns

**Key Questions**:
- Are all database operations using `async with self.db_config.get_session()`?
- Is there session sharing between concurrent requests?
- Are background tasks interfering with API sessions?

#### Session Lifecycle Audit
**Check Points**:
```python
# Verify this pattern is used consistently
async with db_service.db_config.get_session() as session:
    # Database operations
    await session.commit()  # If needed
# Session automatically closed
```

### 2. Table-Specific Issues

#### Universal Detections vs Regular Detections
**Problem**: Search endpoint fails when accessing detection data
**Investigation**:
- [ ] Verify `universal_detections` table exists
- [ ] Check table schema compatibility
- [ ] Test direct SQL queries outside FastAPI context
- [ ] Compare working vs failing database methods

#### Database Schema Validation
```sql
-- Check table existence
.tables

-- Verify detection tables structure
.schema detections
.schema universal_detections

-- Check for foreign key constraints
PRAGMA foreign_key_list(detections);
PRAGMA foreign_key_list(universal_detections);
```

### 3. Concurrent Access Patterns

#### Background Process Conflicts
**Current Issue**: Processing loop shows continuous session errors
**Investigation Plan**:
- [ ] Map all background database access points
- [ ] Check for global session variables (old `db` references)
- [ ] Verify session isolation between processes

#### Request Concurrency
**Test Scenario**:
- Multiple simultaneous API requests
- Background processing + API requests
- WebSocket updates + database queries

### 4. Connection Pool Analysis

#### Current Configuration
**Review**:
- SQLite connection handling in async context
- aiosqlite configuration
- Session factory setup in `db_config.py`

#### Potential Issues
```python
# Check for these anti-patterns:
# 1. Shared session across requests
session = create_session()  # BAD if reused

# 2. Improper session cleanup
# Missing try/finally or context manager

# 3. Transaction conflicts
# Multiple operations without proper isolation
```

## Diagnostic Steps

### Step 1: Isolation Testing (30 minutes)
Create minimal test to reproduce the issue:

```python
# File: test_database_session_isolation.py
import asyncio
from database.service import DatabaseService

async def test_concurrent_database_access():
    """Test concurrent database operations"""
    
    async def query_detections(db_service):
        try:
            detections = await db_service.get_recent_detections(5)
            print(f"✅ Success: {len(detections)} detections")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    # Test concurrent access
    tasks = []
    for i in range(5):
        db_service = DatabaseService()
        task = asyncio.create_task(query_detections(db_service))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    success_count = sum(1 for r in results if r is True)
    print(f"Success rate: {success_count}/5")

if __name__ == "__main__":
    asyncio.run(test_concurrent_database_access())
```

### Step 2: Session Lifecycle Tracing (45 minutes)
Add debug logging to track session creation/destruction:

```python
# Add to DatabaseService.__init__
self.session_counter = 0

# Add to get_session context manager
async def get_session(self):
    self.session_counter += 1
    session_id = self.session_counter
    logger.debug(f"Creating session {session_id}")
    try:
        async with self.async_session() as session:
            logger.debug(f"Session {session_id} active")
            yield session
            logger.debug(f"Session {session_id} committing")
    except Exception as e:
        logger.error(f"Session {session_id} error: {e}")
        raise
    finally:
        logger.debug(f"Session {session_id} closed")
```

### Step 3: Table Access Validation (30 minutes)
Direct database testing outside FastAPI:

```python
# File: test_direct_database_access.py
import asyncio
import aiosqlite
from database.models import Detection

async def test_direct_table_access():
    """Test direct database table access"""
    
    # Test SQLite connection
    try:
        async with aiosqlite.connect("data/license_plates.db") as db:
            # Check tables exist
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = await cursor.fetchall()
            print(f"Available tables: {[t[0] for t in tables]}")
            
            # Test detection table access
            cursor = await db.execute("SELECT COUNT(*) FROM detections LIMIT 1")
            count = await cursor.fetchone()
            print(f"Detections count: {count[0]}")
            
    except Exception as e:
        print(f"Direct database error: {e}")

asyncio.run(test_direct_table_access())
```

### Step 4: Background Process Audit (60 minutes)
Review all background database operations:

**Files to Check**:
- Processing loop database calls
- WebSocket status broadcasts
- Camera health monitoring
- Storage cleanup operations

**Pattern to Find**:
```bash
# Search for old database patterns
grep -r "await db\." api/ --exclude-dir=__pycache__
grep -r "db\." api/ --exclude-dir=__pycache__ | grep -v "db_service"
```

## Fix Implementation Strategy

### Phase 1: Quick Wins (1-2 hours)
1. **Remove remaining global `db` references**
2. **Fix processing loop session isolation** 
3. **Add proper error handling to detection endpoints**

### Phase 2: Architecture Improvements (2-3 hours)
1. **Implement session-per-request pattern consistently**
2. **Add connection pooling if needed**
3. **Separate background task database context**

### Phase 3: Validation & Testing (1-2 hours)
1. **Run comprehensive endpoint tests**
2. **Load testing with concurrent requests**
3. **Monitor system for 24 hours**

## Expected Outcomes

### Success Indicators
- ✅ No database session binding errors in logs
- ✅ All detection endpoints return real data (not mock)
- ✅ Background processing runs without database errors
- ✅ Frontend can load detection data properly
- ✅ System stable under concurrent load

### Performance Targets
- API response times < 200ms for detection queries
- No memory leaks from unclosed sessions
- Background processing errors < 1 per hour
- 99%+ uptime over 24-hour period

## Rollback Plan

If investigation reveals complex architectural issues:

### Immediate Stabilization
1. Keep current mock data endpoints working
2. Isolate problematic detection methods
3. Implement circuit breaker pattern for failing operations

### Gradual Migration
1. Fix one detection endpoint at a time
2. Test thoroughly before moving to next
3. Maintain backward compatibility

## Timeline

### Day 1 (Today)
- [ ] **Hours 1-2**: Run diagnostic steps 1-3
- [ ] **Hours 3-4**: Implement Phase 1 quick wins
- [ ] **Hours 5-6**: Begin Phase 2 architecture improvements

### Day 2
- [ ] **Hours 1-3**: Complete Phase 2 improvements
- [ ] **Hours 4-6**: Phase 3 validation and testing

### Day 3-7
- [ ] **Continuous monitoring**: Watch for regressions
- [ ] **Performance tuning**: Optimize based on real usage
- [ ] **Documentation updates**: Record lessons learned

## Resource Requirements

### Development Time
- **Investigation**: 4-6 hours
- **Implementation**: 6-8 hours  
- **Testing & Validation**: 4-6 hours
- **Total**: 14-20 hours over 2-3 days

### Testing Requirements
- Isolated database test environment
- Concurrent request testing tools
- Log monitoring and analysis
- Performance benchmarking tools

---

**Status**: Ready to begin investigation
**Priority**: CRITICAL - System functionality depends on resolution
**Next Action**: Execute diagnostic Step 1 (Isolation Testing)