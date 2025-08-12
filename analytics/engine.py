"""
Analytics Engine for LPR System
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging
import json
from database.service import DatabaseService

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsQuery:
    """Analytics query parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    camera_ids: Optional[List[str]] = None
    vehicle_types: Optional[List[str]] = None
    min_confidence: Optional[float] = None
    group_by: str = "day"  # day, hour, week, month
    limit: Optional[int] = None


@dataclass
class AnalyticsResult:
    """Analytics result container"""
    query: AnalyticsQuery
    data: Dict[str, Any]
    generated_at: datetime
    execution_time_ms: float


class LPRAnalyticsEngine:
    """Core analytics engine for license plate recognition system"""
    
    def __init__(self):
        self.db = DatabaseService()
    
    async def get_detection_overview(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Get high-level detection statistics"""
        start_time = datetime.now()
        
        try:
            # Get total detections count
            detections = await self.db.search_detections(
                start_date=query.start_date,
                end_date=query.end_date,
                camera_id=query.camera_ids[0] if query.camera_ids else None,
                vehicle_type=query.vehicle_types[0] if query.vehicle_types else None,
                min_confidence=query.min_confidence,
                limit=10000  # Large limit for analytics
            )
            
            # Calculate overview metrics
            total_detections = len(detections)
            unique_plates = len(set(d.plate_text for d in detections if d.plate_text))
            
            # Average confidence
            avg_confidence = sum(d.confidence for d in detections) / total_detections if detections else 0
            
            # Vehicle type distribution
            vehicle_types = defaultdict(int)
            for d in detections:
                vehicle_types[d.vehicle_type or 'unknown'] += 1
            
            # Camera distribution
            camera_distribution = defaultdict(int)
            for d in detections:
                camera_distribution[d.camera_id] += 1
            
            # Time range analysis
            if detections:
                first_detection = min(d.detected_at for d in detections)
                last_detection = max(d.detected_at for d in detections)
                time_span = (last_detection - first_detection).total_seconds() / 3600  # hours
                detections_per_hour = total_detections / time_span if time_span > 0 else 0
            else:
                first_detection = last_detection = None
                detections_per_hour = 0
            
            data = {
                'summary': {
                    'total_detections': total_detections,
                    'unique_plates': unique_plates,
                    'average_confidence': round(avg_confidence, 3),
                    'detections_per_hour': round(detections_per_hour, 2),
                    'date_range': {
                        'start': query.start_date.isoformat() if query.start_date else None,
                        'end': query.end_date.isoformat() if query.end_date else None,
                        'first_detection': first_detection.isoformat() if first_detection else None,
                        'last_detection': last_detection.isoformat() if last_detection else None
                    }
                },
                'distributions': {
                    'vehicle_types': dict(vehicle_types),
                    'cameras': dict(camera_distribution)
                }
            }
            
        except Exception as e:
            logger.error(f"Detection overview analysis failed: {e}")
            data = {'error': str(e)}
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return AnalyticsResult(query, data, datetime.now(), execution_time)
    
    async def get_temporal_trends(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Get time-based detection trends"""
        start_time = datetime.now()
        
        try:
            detections = await self.db.search_detections(
                start_date=query.start_date,
                end_date=query.end_date,
                camera_id=query.camera_ids[0] if query.camera_ids else None,
                min_confidence=query.min_confidence,
                limit=10000
            )
            
            # Group by time periods
            time_groups = defaultdict(int)
            confidence_groups = defaultdict(list)
            
            for detection in detections:
                if not detection.detected_at:
                    continue
                
                # Group by specified time period
                if query.group_by == "hour":
                    time_key = detection.detected_at.replace(minute=0, second=0, microsecond=0)
                elif query.group_by == "day":
                    time_key = detection.detected_at.replace(hour=0, minute=0, second=0, microsecond=0)
                elif query.group_by == "week":
                    days_since_monday = detection.detected_at.weekday()
                    monday = detection.detected_at - timedelta(days=days_since_monday)
                    time_key = monday.replace(hour=0, minute=0, second=0, microsecond=0)
                elif query.group_by == "month":
                    time_key = detection.detected_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    time_key = detection.detected_at.replace(minute=0, second=0, microsecond=0)
                
                time_groups[time_key] += 1
                confidence_groups[time_key].append(detection.confidence)
            
            # Convert to sorted list
            trend_data = []
            for time_key in sorted(time_groups.keys()):
                avg_confidence = sum(confidence_groups[time_key]) / len(confidence_groups[time_key])
                trend_data.append({
                    'timestamp': time_key.isoformat(),
                    'count': time_groups[time_key],
                    'average_confidence': round(avg_confidence, 3)
                })
            
            # Calculate peak detection times
            if trend_data:
                peak_time = max(trend_data, key=lambda x: x['count'])
                lowest_time = min(trend_data, key=lambda x: x['count'])
            else:
                peak_time = lowest_time = None
            
            data = {
                'trends': trend_data,
                'analysis': {
                    'total_periods': len(trend_data),
                    'peak_time': peak_time,
                    'lowest_time': lowest_time,
                    'group_by': query.group_by
                }
            }
            
        except Exception as e:
            logger.error(f"Temporal trends analysis failed: {e}")
            data = {'error': str(e)}
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return AnalyticsResult(query, data, datetime.now(), execution_time)
    
    async def get_camera_performance(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Analyze camera-specific performance metrics"""
        start_time = datetime.now()
        
        try:
            # Get all cameras
            all_cameras = await self.db.get_all_cameras()
            camera_info = {c.camera_id: {'name': c.name, 'location': c.location} for c in all_cameras}
            
            # Get detections for analysis
            detections = await self.db.search_detections(
                start_date=query.start_date,
                end_date=query.end_date,
                min_confidence=query.min_confidence,
                limit=10000
            )
            
            # Analyze by camera
            camera_stats = defaultdict(lambda: {
                'detection_count': 0,
                'confidence_scores': [],
                'unique_plates': set(),
                'vehicle_types': defaultdict(int),
                'hourly_distribution': defaultdict(int)
            })
            
            for detection in detections:
                camera_id = detection.camera_id
                camera_stats[camera_id]['detection_count'] += 1
                camera_stats[camera_id]['confidence_scores'].append(detection.confidence)
                if detection.plate_text:
                    camera_stats[camera_id]['unique_plates'].add(detection.plate_text)
                
                vehicle_type = detection.vehicle_type or 'unknown'
                camera_stats[camera_id]['vehicle_types'][vehicle_type] += 1
                
                if detection.detected_at:
                    hour = detection.detected_at.hour
                    camera_stats[camera_id]['hourly_distribution'][hour] += 1
            
            # Calculate performance metrics
            camera_performance = {}
            for camera_id, stats in camera_stats.items():
                if stats['confidence_scores']:
                    avg_confidence = sum(stats['confidence_scores']) / len(stats['confidence_scores'])
                    min_confidence = min(stats['confidence_scores'])
                    max_confidence = max(stats['confidence_scores'])
                else:
                    avg_confidence = min_confidence = max_confidence = 0
                
                # Find peak hour
                peak_hour = max(stats['hourly_distribution'].items(), 
                              key=lambda x: x[1])[0] if stats['hourly_distribution'] else 0
                
                camera_performance[camera_id] = {
                    'camera_info': camera_info.get(camera_id, {'name': 'Unknown', 'location': 'Unknown'}),
                    'metrics': {
                        'total_detections': stats['detection_count'],
                        'unique_plates': len(stats['unique_plates']),
                        'average_confidence': round(avg_confidence, 3),
                        'confidence_range': {
                            'min': round(min_confidence, 3),
                            'max': round(max_confidence, 3)
                        },
                        'peak_hour': peak_hour,
                        'vehicle_types': dict(stats['vehicle_types']),
                        'hourly_distribution': dict(stats['hourly_distribution'])
                    }
                }
            
            # Rank cameras by performance
            camera_rankings = {
                'most_detections': sorted(camera_performance.items(), 
                                        key=lambda x: x[1]['metrics']['total_detections'], reverse=True)[:5],
                'highest_confidence': sorted(camera_performance.items(),
                                           key=lambda x: x[1]['metrics']['average_confidence'], reverse=True)[:5],
                'most_unique_plates': sorted(camera_performance.items(),
                                           key=lambda x: x[1]['metrics']['unique_plates'], reverse=True)[:5]
            }
            
            data = {
                'camera_performance': camera_performance,
                'rankings': {
                    'most_detections': [(k, v['metrics']['total_detections']) for k, v in camera_rankings['most_detections']],
                    'highest_confidence': [(k, round(v['metrics']['average_confidence'], 3)) for k, v in camera_rankings['highest_confidence']],
                    'most_unique_plates': [(k, v['metrics']['unique_plates']) for k, v in camera_rankings['most_unique_plates']]
                },
                'summary': {
                    'total_cameras_analyzed': len(camera_performance),
                    'total_cameras_configured': len(all_cameras)
                }
            }
            
        except Exception as e:
            logger.error(f"Camera performance analysis failed: {e}")
            data = {'error': str(e)}
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return AnalyticsResult(query, data, datetime.now(), execution_time)
    
    async def get_plate_analytics(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Analyze license plate patterns and frequencies"""
        start_time = datetime.now()
        
        try:
            detections = await self.db.search_detections(
                start_date=query.start_date,
                end_date=query.end_date,
                camera_id=query.camera_ids[0] if query.camera_ids else None,
                min_confidence=query.min_confidence,
                limit=10000
            )
            
            # Analyze plate patterns
            plate_frequency = defaultdict(int)
            plate_cameras = defaultdict(set)
            plate_confidences = defaultdict(list)
            plate_first_seen = {}
            plate_last_seen = {}
            
            for detection in detections:
                if not detection.plate_text or detection.plate_text == 'TEXAS':
                    continue
                
                plate = detection.plate_text.upper()
                plate_frequency[plate] += 1
                plate_cameras[plate].add(detection.camera_id)
                plate_confidences[plate].append(detection.confidence)
                
                if detection.detected_at:
                    if plate not in plate_first_seen or detection.detected_at < plate_first_seen[plate]:
                        plate_first_seen[plate] = detection.detected_at
                    if plate not in plate_last_seen or detection.detected_at > plate_last_seen[plate]:
                        plate_last_seen[plate] = detection.detected_at
            
            # Find frequent visitors (plates seen multiple times)
            frequent_plates = [(plate, count) for plate, count in plate_frequency.items() if count > 1]
            frequent_plates.sort(key=lambda x: x[1], reverse=True)
            
            # Analyze plate patterns (state identification, format analysis)
            pattern_analysis = self._analyze_plate_patterns(list(plate_frequency.keys()))
            
            # Multi-camera plates (plates seen by multiple cameras)
            multi_camera_plates = [(plate, len(cameras)) for plate, cameras in plate_cameras.items() if len(cameras) > 1]
            multi_camera_plates.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate visit durations for frequent plates
            visit_durations = {}
            for plate, count in frequent_plates[:20]:  # Top 20 frequent plates
                if plate in plate_first_seen and plate in plate_last_seen:
                    duration = (plate_last_seen[plate] - plate_first_seen[plate]).total_seconds() / 60  # minutes
                    avg_confidence = sum(plate_confidences[plate]) / len(plate_confidences[plate])
                    visit_durations[plate] = {
                        'visits': count,
                        'duration_minutes': round(duration, 1),
                        'cameras': len(plate_cameras[plate]),
                        'average_confidence': round(avg_confidence, 3),
                        'first_seen': plate_first_seen[plate].isoformat(),
                        'last_seen': plate_last_seen[plate].isoformat()
                    }
            
            data = {
                'summary': {
                    'total_unique_plates': len(plate_frequency),
                    'total_detections': sum(plate_frequency.values()),
                    'frequent_plates_count': len(frequent_plates),
                    'multi_camera_plates_count': len(multi_camera_plates)
                },
                'frequent_plates': frequent_plates[:20],  # Top 20
                'multi_camera_plates': multi_camera_plates[:10],  # Top 10
                'visit_analysis': visit_durations,
                'pattern_analysis': pattern_analysis
            }
            
        except Exception as e:
            logger.error(f"Plate analytics failed: {e}")
            data = {'error': str(e)}
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return AnalyticsResult(query, data, datetime.now(), execution_time)
    
    def _analyze_plate_patterns(self, plates: List[str]) -> Dict[str, Any]:
        """Analyze license plate format patterns"""
        import re
        
        patterns = {
            'texas_standard': 0,  # ABC1234 or AB12345
            'texas_specialty': 0,  # Various specialty formats
            'numeric_only': 0,    # Only numbers
            'alpha_only': 0,      # Only letters
            'mixed': 0,           # Mixed formats
            'unknown': 0
        }
        
        lengths = defaultdict(int)
        
        for plate in plates:
            if not plate or len(plate) < 3:
                patterns['unknown'] += 1
                continue
            
            lengths[len(plate)] += 1
            
            # Texas standard patterns
            if re.match(r'^[A-Z]{3}\d{4}$', plate):  # ABC1234
                patterns['texas_standard'] += 1
            elif re.match(r'^[A-Z]{2}\d{5}$', plate):  # AB12345
                patterns['texas_standard'] += 1
            elif plate.isdigit():
                patterns['numeric_only'] += 1
            elif plate.isalpha():
                patterns['alpha_only'] += 1
            elif re.match(r'^[A-Z0-9]+$', plate):
                patterns['mixed'] += 1
            else:
                patterns['unknown'] += 1
        
        return {
            'format_distribution': dict(patterns),
            'length_distribution': dict(lengths),
            'most_common_length': max(lengths.items(), key=lambda x: x[1])[0] if lengths else 0
        }
    
    async def get_system_performance_analytics(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Analyze system performance metrics"""
        start_time = datetime.now()
        
        try:
            # This would typically integrate with the monitoring system
            from monitoring.metrics import metrics
            
            # Get recent detections for performance analysis
            detections = await self.db.search_detections(
                start_date=query.start_date or (datetime.now() - timedelta(hours=24)),
                end_date=query.end_date or datetime.now(),
                limit=1000
            )
            
            # Calculate processing performance
            if detections:
                # Simulate processing time analysis (in a real system, this would come from metrics)
                detection_rate = len(detections) / 24  # per hour
                
                # Confidence distribution
                confidences = [d.confidence for d in detections]
                confidence_stats = {
                    'mean': sum(confidences) / len(confidences),
                    'min': min(confidences),
                    'max': max(confidences),
                    'high_confidence_count': len([c for c in confidences if c > 0.8]),
                    'low_confidence_count': len([c for c in confidences if c < 0.5])
                }
                
                # Time-based performance
                hourly_counts = defaultdict(int)
                for d in detections:
                    if d.detected_at:
                        hourly_counts[d.detected_at.hour] += 1
                
                peak_hour = max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else 0
                
            else:
                detection_rate = 0
                confidence_stats = {'mean': 0, 'min': 0, 'max': 0, 'high_confidence_count': 0, 'low_confidence_count': 0}
                peak_hour = 0
                hourly_counts = {}
            
            # System health simulation (would come from monitoring system)
            system_health = {
                'detection_rate_per_hour': round(detection_rate, 2),
                'confidence_statistics': confidence_stats,
                'peak_detection_hour': peak_hour,
                'hourly_distribution': dict(hourly_counts),
                'performance_score': min(100, max(0, (confidence_stats['mean'] * 100) if confidence_stats['mean'] > 0 else 0))
            }
            
            data = {
                'system_performance': system_health,
                'analysis_period': {
                    'start': (query.start_date or (datetime.now() - timedelta(hours=24))).isoformat(),
                    'end': (query.end_date or datetime.now()).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"System performance analytics failed: {e}")
            data = {'error': str(e)}
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        return AnalyticsResult(query, data, datetime.now(), execution_time)
    
    async def generate_comprehensive_report(self, query: AnalyticsQuery) -> Dict[str, AnalyticsResult]:
        """Generate a comprehensive analytics report"""
        logger.info("Generating comprehensive analytics report")
        
        # Run all analytics in parallel for better performance
        tasks = {
            'overview': self.get_detection_overview(query),
            'temporal_trends': self.get_temporal_trends(query),
            'camera_performance': self.get_camera_performance(query),
            'plate_analytics': self.get_plate_analytics(query),
            'system_performance': self.get_system_performance_analytics(query)
        }
        
        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
                logger.debug(f"Completed {name} analysis in {results[name].execution_time_ms:.1f}ms")
            except Exception as e:
                logger.error(f"Failed to complete {name} analysis: {e}")
                results[name] = AnalyticsResult(
                    query, 
                    {'error': str(e)}, 
                    datetime.now(), 
                    0
                )
        
        return results
    
    async def close(self):
        """Close database connections"""
        await self.db.close()


# Global analytics engine instance
analytics_engine = LPRAnalyticsEngine()