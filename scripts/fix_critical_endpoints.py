#!/usr/bin/env python3
"""
Fix Critical Endpoints Script
After database fresh start, fix the remaining endpoint issues
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from database.service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CriticalEndpointFixer:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    async def test_database_connection(self):
        """Test basic database connectivity"""
        logger.info("🔍 Testing database connection...")
        
        try:
            db_service = DatabaseService()
            
            # Test basic queries
            cameras = await db_service.get_all_cameras()
            detections = await db_service.get_recent_detections(5)
            
            logger.info(f"✅ Database connection successful")
            logger.info(f"   - Cameras found: {len(cameras)}")
            logger.info(f"   - Recent detections: {len(detections)}")
            
            await db_service.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.issues_found.append(f"Database connection: {e}")
            return False
            
    def fix_search_endpoint_real_data(self):
        """Replace mock data in search endpoint with real database calls"""
        logger.info("🔧 Fixing search endpoint to use real data...")
        
        api_main_path = "api/main.py"
        
        if not os.path.exists(api_main_path):
            logger.error(f"❌ API main file not found: {api_main_path}")
            return False
            
        # Read current file
        with open(api_main_path, 'r') as f:
            content = f.read()
            
        # Find and replace the mock search endpoint
        mock_search_start = '@app.get("/api/detections/search")'
        mock_search_end = 'return {"results": mock_results}'
        
        if mock_search_start in content and mock_search_end in content:
            # Create the real implementation
            real_implementation = '''@app.get("/api/detections/search")  
async def search_detections(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query("detected_at", description="Field to sort by"),
    sort_direction: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Sort direction"),
    plate_text: Optional[str] = Query(None, description="Filter by plate text"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    db_service: DatabaseService = Depends(get_database_service)
):
    """Search detections with real database queries"""
    
    try:
        # Get recent detections (primary table)
        all_detections = await db_service.get_recent_detections(limit + offset, camera_id)
        
        # Apply text filtering if specified
        if plate_text:
            all_detections = [d for d in all_detections if plate_text.upper() in d.plate_text.upper()]
        
        # Apply offset and limit
        if offset > 0:
            detections = all_detections[offset:offset + limit] if len(all_detections) > offset else []
        else:
            detections = all_detections[:limit]
        
        # Format results
        results = []
        for d in detections:
            results.append({
                "id": d.id,
                "camera_id": d.camera_id,
                "camera_name": d.camera_id,  # Will be enhanced later with camera names
                "plate_text": d.plate_text,
                "confidence": d.confidence,
                "vehicle_type": d.vehicle_type or "vehicle",
                "object_type": d.vehicle_type or "vehicle",
                "detected_at": d.detected_at.isoformat() if hasattr(d.detected_at, 'isoformat') else str(d.detected_at),
                "plate_image": d.plate_image_path,
                "frame_image": d.frame_path,
                "status": getattr(d, 'status', 'unverified'),
                "has_video": d.video_clip_id is not None,
                "video_clip_id": d.video_clip_id
            })
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        # Return empty results with error logged, don't crash
        return {"results": [], "error": "Database query failed"}'''
            
            # Find the full function to replace
            start_idx = content.find(mock_search_start)
            if start_idx == -1:
                logger.error("❌ Could not find search endpoint start")
                return False
                
            # Find the end of the function (next @app. decorator or end of file)
            next_endpoint = content.find('@app.', start_idx + 1)
            if next_endpoint == -1:
                next_endpoint = len(content)
                
            # Replace the function
            new_content = content[:start_idx] + real_implementation + '\\n\\n' + content[next_endpoint:]
            
            # Write back to file
            with open(api_main_path, 'w') as f:
                f.write(new_content)
                
            logger.info("✅ Search endpoint updated to use real database queries")
            self.fixes_applied.append("Search endpoint - real data implementation")
            return True
            
        else:
            logger.warning("⚠️  Mock search endpoint not found - may already be fixed")
            return True
            
    def fix_recent_detections_endpoint(self):
        """Ensure recent detections endpoint works with fresh database"""
        logger.info("🔧 Checking recent detections endpoint...")
        
        # The recent detections endpoint should work with fresh database
        # Just verify it's using proper dependency injection
        api_main_path = "api/main.py"
        
        with open(api_main_path, 'r') as f:
            content = f.read()
            
        # Check if recent detections endpoint uses dependency injection
        recent_pattern = '@app.get("/api/detections/recent")'
        if recent_pattern in content:
            # Find the function
            start_idx = content.find(recent_pattern)
            next_endpoint = content.find('@app.', start_idx + 1)
            if next_endpoint == -1:
                next_endpoint = start_idx + 1000  # Look ahead
                
            function_content = content[start_idx:next_endpoint]
            
            if 'db_service: DatabaseService = Depends(get_database_service)' in function_content:
                logger.info("✅ Recent detections endpoint already uses dependency injection")
                return True
            else:
                logger.warning("⚠️  Recent detections endpoint may need dependency injection fix")
                self.issues_found.append("Recent detections endpoint - missing dependency injection")
                return False
        else:
            logger.error("❌ Recent detections endpoint not found")
            return False
            
    def remove_duplicate_endpoints(self):
        """Clean up duplicate/broken endpoint definitions"""
        logger.info("🧹 Cleaning up duplicate endpoints...")
        
        api_main_path = "api/main.py"
        
        with open(api_main_path, 'r') as f:
            lines = f.readlines()
            
        # Track endpoint definitions
        endpoint_lines = []
        duplicates_removed = 0
        
        # Find all @app. lines and their associated functions
        for i, line in enumerate(lines):
            if line.strip().startswith('@app.get("/api/detections/similar/'):
                endpoint_lines.append(i)
                
        # If we have multiple similar endpoints, keep only the first working one
        if len(endpoint_lines) > 1:
            logger.info(f"Found {len(endpoint_lines)} duplicate similar plate endpoints")
            
            # Remove duplicates (keep first, remove others)
            lines_to_remove = []
            for endpoint_line in endpoint_lines[1:]:  # Skip first one
                # Find the function end
                func_start = endpoint_line
                func_end = func_start + 1
                
                # Find next @app or end of file
                while func_end < len(lines) and not lines[func_end].strip().startswith('@app.'):
                    func_end += 1
                    
                # Mark lines for removal
                for line_idx in range(func_start, func_end):
                    lines_to_remove.append(line_idx)
                    
            # Remove the lines (in reverse order to maintain indices)
            for line_idx in reversed(sorted(lines_to_remove)):
                lines.pop(line_idx)
                duplicates_removed += 1
                
            # Write back cleaned content
            with open(api_main_path, 'w') as f:
                f.writelines(lines)
                
            logger.info(f"✅ Removed {duplicates_removed} duplicate endpoint lines")
            self.fixes_applied.append(f"Removed {duplicates_removed} duplicate endpoint lines")
            
        return True
        
    async def test_critical_endpoints(self):
        """Test the critical endpoints after fixes"""
        logger.info("🧪 Testing critical endpoints...")
        
        import requests
        import time
        
        # Wait for any service restarts
        time.sleep(2)
        
        base_url = "http://localhost:8001"
        endpoints_to_test = [
            ("/health", "Health check"),
            ("/api/system/health", "System health"),
            ("/api/cameras", "Cameras list"),
            ("/api/detections/recent?limit=5", "Recent detections"),
            ("/api/detections/search?limit=10", "Search detections")
        ]
        
        results = []
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
                results.append((description, status, response.status_code))
                logger.info(f"   {description}: {status}")
            except Exception as e:
                results.append((description, f"❌ ERROR ({e})", 0))
                logger.error(f"   {description}: ❌ ERROR - {e}")
                
        # Summary
        passed = sum(1 for r in results if "✅ PASS" in r[1])
        total = len(results)
        
        logger.info(f"📊 Endpoint test results: {passed}/{total} passed")
        
        return passed == total
        
    async def run_critical_fixes(self):
        """Run all critical fixes"""
        logger.info("🔧 STARTING CRITICAL ENDPOINT FIXES")
        logger.info("=" * 45)
        
        success = True
        
        # Step 1: Test database
        if not await self.test_database_connection():
            success = False
            
        # Step 2: Fix search endpoint
        if not self.fix_search_endpoint_real_data():
            success = False
            
        # Step 3: Check recent detections
        if not self.fix_recent_detections_endpoint():
            success = False
            
        # Step 4: Clean up duplicates
        if not self.remove_duplicate_endpoints():
            success = False
            
        logger.info("=" * 45)
        
        if success:
            logger.info("✅ All critical fixes completed successfully!")
            logger.info("🔄 Restart services to apply changes:")
            logger.info("   python3 bin/start_lpr.py")
            
            # Test endpoints after restart
            logger.info("⏳ Waiting 5 seconds for service restart...")
            await asyncio.sleep(5)
            
            if await self.test_critical_endpoints():
                logger.info("🎉 ALL CRITICAL ENDPOINTS WORKING!")
                return True
            else:
                logger.warning("⚠️  Some endpoints still have issues")
                return False
                
        else:
            logger.error("❌ Some critical fixes failed")
            if self.issues_found:
                logger.error("Issues found:")
                for issue in self.issues_found:
                    logger.error(f"   - {issue}")
            return False

async def main():
    """Main execution function"""
    print("🔧 CRITICAL ENDPOINT FIXES")
    print("=" * 30)
    print("This will fix endpoint issues after database fresh start.")
    print()
    
    fixer = CriticalEndpointFixer()
    success = await fixer.run_critical_fixes()
    
    if success:
        print("\\n🎯 NEXT STEPS:")
        print("1. ✅ Database is clean and working")
        print("2. ✅ Critical endpoints are fixed")
        print("3. 🌐 Test frontend at http://localhost:8080")
        print("4. 📊 Run full test suite: python3 test_endpoints.py")
        
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)