"""
Database service for async SQLite operations
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, func, desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import logging
from .models import (Base, Camera, Detection, VideoRecording, VideoClip, HourlyStatistics,
                     CameraNew, CameraConnection, CameraRecordingConfig, CameraSetting, CameraStatus)

class DatabaseService:
    def __init__(self, database_url: str = "sqlite+aiosqlite:///data/license_plates.db"):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.logger = logging.getLogger("DatabaseService")
        
    async def init_db(self):
        """Initialize database and create tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("Database initialized and tables created")
    
    async def create_tables(self):
        """Create all database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("Database tables created")
    
    def get_session(self):
        """Get async database session"""
        return self.async_session()
    
    async def save_detection(self, detection_data: Dict) -> str:
        """Save detection to database"""
        async with self.async_session() as session:
            # Convert datetime if it's a string
            if isinstance(detection_data.get('detected_at'), str):
                detection_data['detected_at'] = datetime.fromisoformat(detection_data['detected_at'])
            elif 'timestamp' in detection_data:
                detection_data['detected_at'] = detection_data.pop('timestamp')
            
            detection = Detection(**detection_data)
            session.add(detection)
            await session.commit()
            await session.refresh(detection)
            return detection.id
    
    async def get_recent_detections(self, limit: int = 100, camera_id: Optional[str] = None) -> List[Detection]:
        """Get recent detections"""
        async with self.async_session() as session:
            query = select(Detection).order_by(desc(Detection.detected_at)).limit(limit)
            
            if camera_id:
                query = query.where(Detection.camera_id == camera_id)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_detection_by_id(self, detection_id: str) -> Optional[Detection]:
        """Get detection by ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Detection).where(Detection.id == detection_id)
            )
            return result.scalar_one_or_none()
    
    async def search_detections(self, 
                               plate_text: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               camera_id: Optional[str] = None,
                               min_confidence: Optional[float] = None,
                               vehicle_type: Optional[str] = None,
                               limit: int = 100,
                               offset: int = 0) -> List[Detection]:
        """Search detections by criteria with enhanced filtering"""
        async with self.async_session() as session:
            query = select(Detection).order_by(desc(Detection.detected_at))
            
            conditions = []
            if plate_text:
                # Support both exact match and fuzzy search
                if plate_text.startswith('"') and plate_text.endswith('"'):
                    # Exact match
                    exact_plate = plate_text.strip('"')
                    conditions.append(Detection.plate_text == exact_plate)
                else:
                    # Fuzzy search
                    conditions.append(Detection.plate_text.like(f"%{plate_text}%"))
            if start_date:
                conditions.append(Detection.detected_at >= start_date)
            if end_date:
                conditions.append(Detection.detected_at <= end_date)
            if camera_id:
                conditions.append(Detection.camera_id == camera_id)
            if min_confidence is not None:
                conditions.append(Detection.confidence >= min_confidence)
            if vehicle_type:
                conditions.append(Detection.vehicle_type.like(f"%{vehicle_type}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_search_count(self,
                              plate_text: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              camera_id: Optional[str] = None,
                              min_confidence: Optional[float] = None,
                              vehicle_type: Optional[str] = None) -> int:
        """Get count of detections matching search criteria"""
        async with self.async_session() as session:
            query = select(func.count(Detection.id))
            
            conditions = []
            if plate_text:
                if plate_text.startswith('"') and plate_text.endswith('"'):
                    exact_plate = plate_text.strip('"')
                    conditions.append(Detection.plate_text == exact_plate)
                else:
                    conditions.append(Detection.plate_text.like(f"%{plate_text}%"))
            if start_date:
                conditions.append(Detection.detected_at >= start_date)
            if end_date:
                conditions.append(Detection.detected_at <= end_date)
            if camera_id:
                conditions.append(Detection.camera_id == camera_id)
            if min_confidence is not None:
                conditions.append(Detection.confidence >= min_confidence)
            if vehicle_type:
                conditions.append(Detection.vehicle_type.like(f"%{vehicle_type}%"))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalar() or 0
    
    async def get_similar_plates(self, plate_text: str, limit: int = 10) -> List[Detection]:
        """Find plates similar to the given text using fuzzy matching"""
        async with self.async_session() as session:
            # Simple similarity: plates that share most characters
            similar_conditions = []
            
            # Remove common characters for pattern matching
            base_chars = set(plate_text.upper())
            
            # Find plates with similar character sets
            query = select(Detection).order_by(desc(Detection.detected_at))
            
            # Look for plates with similar length and characters
            length_tolerance = 2
            min_length = max(1, len(plate_text) - length_tolerance)
            max_length = len(plate_text) + length_tolerance
            
            similar_conditions.append(
                func.length(Detection.plate_text).between(min_length, max_length)
            )
            
            # Add wildcard patterns for partial matches
            for i in range(len(plate_text)):
                if i < len(plate_text) - 1:
                    pattern = plate_text[:i] + '%' + plate_text[i+1:]
                    similar_conditions.append(Detection.plate_text.like(pattern))
            
            if similar_conditions:
                # Use OR condition for similarity matching
                from sqlalchemy import or_
                query = query.where(or_(*similar_conditions))
            
            query = query.limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_plate_history(self, plate_text: str, days: int = 30) -> List[Detection]:
        """Get complete history for a specific plate"""
        async with self.async_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            
            query = select(Detection).where(
                and_(
                    Detection.plate_text == plate_text.upper(),
                    Detection.detected_at >= start_date
                )
            ).order_by(desc(Detection.detected_at))
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_detection_stats(self, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get detection statistics for the given time period"""
        async with self.async_session() as session:
            query = select(Detection)
            
            conditions = []
            if start_date:
                conditions.append(Detection.detected_at >= start_date)
            if end_date:
                conditions.append(Detection.detected_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            detections = result.scalars().all()
            
            if not detections:
                return {
                    "total_detections": 0,
                    "unique_plates": 0,
                    "avg_confidence": 0.0,
                    "top_cameras": [],
                    "vehicle_types": {},
                    "hourly_distribution": {},
                    "confidence_distribution": {}
                }
            
            # Calculate statistics
            unique_plates = set(d.plate_text for d in detections)
            avg_confidence = sum(d.confidence for d in detections) / len(detections)
            
            # Camera statistics
            camera_counts = {}
            for d in detections:
                camera_counts[d.camera_id] = camera_counts.get(d.camera_id, 0) + 1
            top_cameras = sorted(camera_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Vehicle type distribution
            vehicle_types = {}
            for d in detections:
                if d.vehicle_type:
                    vehicle_types[d.vehicle_type] = vehicle_types.get(d.vehicle_type, 0) + 1
            
            # Hourly distribution
            hourly_dist = {}
            for d in detections:
                hour = d.detected_at.hour
                hourly_dist[hour] = hourly_dist.get(hour, 0) + 1
            
            # Confidence distribution
            confidence_ranges = {
                "high (>80%)": 0,
                "medium (50-80%)": 0,
                "low (<50%)": 0
            }
            
            for d in detections:
                if d.confidence > 0.8:
                    confidence_ranges["high (>80%)"] += 1
                elif d.confidence > 0.5:
                    confidence_ranges["medium (50-80%)"] += 1
                else:
                    confidence_ranges["low (<50%)"] += 1
            
            return {
                "total_detections": len(detections),
                "unique_plates": len(unique_plates),
                "avg_confidence": round(avg_confidence, 3),
                "top_cameras": top_cameras,
                "vehicle_types": vehicle_types,
                "hourly_distribution": hourly_dist,
                "confidence_distribution": confidence_ranges,
                "date_range": {
                    "start": min(d.detected_at for d in detections).isoformat(),
                    "end": max(d.detected_at for d in detections).isoformat()
                }
            }
    
    async def add_camera(self, camera_data: Dict) -> str:
        """Add a new camera"""
        async with self.async_session() as session:
            camera = Camera(**camera_data)
            session.add(camera)
            await session.commit()
            await session.refresh(camera)
            return camera.id
    
    async def get_all_cameras(self) -> List[Camera]:
        """Get all cameras"""
        async with self.async_session() as session:
            result = await session.execute(select(Camera))
            return result.scalars().all()
    
    async def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Get camera by ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Camera).where(Camera.camera_id == camera_id)
            )
            return result.scalar_one_or_none()
    
    async def update_camera(self, camera_id: str, camera_data: Dict) -> bool:
        """Update camera configuration"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Camera).where(Camera.camera_id == camera_id)
            )
            camera = result.scalar_one_or_none()
            if camera:
                # Update camera fields
                for key, value in camera_data.items():
                    if hasattr(camera, key):
                        setattr(camera, key, value)
                camera.updated_at = datetime.utcnow()
                await session.commit()
                return True
            return False
    
    async def delete_camera(self, camera_id: str) -> bool:
        """Delete camera"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Camera).where(Camera.camera_id == camera_id)
            )
            camera = result.scalar_one_or_none()
            if camera:
                await session.delete(camera)
                await session.commit()
                return True
            return False
    
    async def update_camera_status(self, camera_id: str, status: str):
        """Update camera status"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Camera).where(Camera.camera_id == camera_id)
            )
            camera = result.scalar_one_or_none()
            if camera:
                camera.status = status
                camera.updated_at = datetime.utcnow()
                await session.commit()
    
    async def update_camera_test_result(self, camera_id: str, test_result: str):
        """Update camera test result"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Camera).where(Camera.camera_id == camera_id)
            )
            camera = result.scalar_one_or_none()
            if camera:
                camera.last_test_at = datetime.utcnow()
                camera.last_test_result = test_result
                await session.commit()
    
    async def save_video_recording(self, recording_data: Dict) -> str:
        """Save video recording meta_data"""
        async with self.async_session() as session:
            recording = VideoRecording(**recording_data)
            session.add(recording)
            await session.commit()
            await session.refresh(recording)
            return recording.id
    
    async def get_video_recording(self, recording_id: str) -> Optional[VideoRecording]:
        """Get video recording by ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(VideoRecording).where(VideoRecording.id == recording_id)
            )
            return result.scalar_one_or_none()
    
    async def create_video_clip(self, clip_data: Dict) -> str:
        """Create video clip for detection"""
        async with self.async_session() as session:
            clip = VideoClip(**clip_data)
            session.add(clip)
            
            # Update detection with clip reference
            if clip_data.get('detection_id'):
                detection_result = await session.execute(
                    select(Detection).where(Detection.id == clip_data['detection_id'])
                )
                detection = detection_result.scalar_one_or_none()
                if detection:
                    detection.video_clip_id = clip.id
                    
            await session.commit()
            await session.refresh(clip)
            return clip.id
    
    async def get_video_clip(self, clip_id: str) -> Optional[VideoClip]:
        """Get video clip by ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(VideoClip).where(VideoClip.id == clip_id)
            )
            return result.scalar_one_or_none()
    
    async def get_analytics_overview(self) -> Dict[str, Any]:
        """Get dashboard analytics overview"""
        async with self.async_session() as session:
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Today's detections
            today_detections = await session.execute(
                select(func.count(Detection.id)).where(
                    Detection.detected_at >= today_start
                )
            )
            total_today = today_detections.scalar() or 0
            
            # Unique plates today
            unique_plates = await session.execute(
                select(func.count(func.distinct(Detection.plate_text))).where(
                    Detection.detected_at >= today_start
                )
            )
            unique_today = unique_plates.scalar() or 0
            
            # Active cameras
            active_cameras = await session.execute(
                select(func.count(Camera.id)).where(Camera.status == 'active')
            )
            active_count = active_cameras.scalar() or 0
            
            total_cameras = await session.execute(select(func.count(Camera.id)))
            total_count = total_cameras.scalar() or 0
            
            # Hourly trend (last 24 hours)
            hourly_data = []
            for i in range(24):
                hour_start = now - timedelta(hours=23-i)
                hour_start = hour_start.replace(minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)
                
                count_result = await session.execute(
                    select(func.count(Detection.id)).where(
                        and_(
                            Detection.detected_at >= hour_start,
                            Detection.detected_at < hour_end
                        )
                    )
                )
                count = count_result.scalar() or 0
                hourly_data.append({
                    'hour': hour_start.strftime('%H:00'),
                    'detections': count
                })
            
            # Top vehicle types
            vehicle_types = await session.execute(
                select(
                    Detection.vehicle_type,
                    func.count(Detection.id).label('count')
                ).where(
                    Detection.detected_at >= today_start
                ).group_by(Detection.vehicle_type).limit(5)
            )
            top_vehicles = [
                {'type': row[0] or 'Unknown', 'count': row[1]}
                for row in vehicle_types
            ]
            
            return {
                'total_detections_today': total_today,
                'unique_plates_today': unique_today,
                'active_cameras': {
                    'active': active_count,
                    'total': total_count
                },
                'storage_used_gb': 0,  # TODO: Calculate actual storage usage
                'hourly_trend': hourly_data,
                'top_vehicles': top_vehicles
            }
    
    async def get_last_detection_time(self, camera_id: str) -> Optional[str]:
        """Get last detection time for a camera"""
        async with self.async_session() as session:
            result = await session.execute(
                select(func.max(Detection.detected_at)).where(
                    Detection.camera_id == camera_id
                )
            )
            last_time = result.scalar()
            return last_time.isoformat() if last_time else None
    
    async def close(self):
        """Close database connection"""
        await self.engine.dispose()