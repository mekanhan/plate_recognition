"""
Analytics API Endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import json
import io
import csv

from .engine import analytics_engine, AnalyticsQuery
from .reports import ReportGenerator
from .visualizations import ChartGenerator
from auth.dependencies import require_detection_view, require_admin, get_current_user
from auth.models import User

logger = logging.getLogger(__name__)

# Create analytics router
analytics_router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@analytics_router.get("/overview")
async def get_analytics_overview(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    camera_ids: Optional[List[str]] = Query(None, description="Camera IDs to analyze"),
    vehicle_types: Optional[List[str]] = Query(None, description="Vehicle types to filter"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user: User = Depends(require_detection_view)
):
    """Get high-level detection analytics overview"""
    try:
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            camera_ids=camera_ids,
            vehicle_types=vehicle_types,
            min_confidence=min_confidence
        )
        
        result = await analytics_engine.get_detection_overview(query)
        
        return {
            "success": True,
            "data": result.data,
            "query_info": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "execution_time_ms": result.execution_time_ms
            },
            "user": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Analytics overview failed: {e}")
        raise HTTPException(500, f"Analytics overview failed: {str(e)}")


@analytics_router.get("/trends")
async def get_temporal_trends(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    camera_ids: Optional[List[str]] = Query(None, description="Camera IDs to analyze"),
    group_by: str = Query("day", regex="^(hour|day|week|month)$", description="Time grouping"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user: User = Depends(require_detection_view)
):
    """Get time-based detection trends"""
    try:
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            camera_ids=camera_ids,
            min_confidence=min_confidence,
            group_by=group_by
        )
        
        result = await analytics_engine.get_temporal_trends(query)
        
        return {
            "success": True,
            "data": result.data,
            "query_info": {
                "group_by": group_by,
                "execution_time_ms": result.execution_time_ms
            }
        }
        
    except Exception as e:
        logger.error(f"Temporal trends analysis failed: {e}")
        raise HTTPException(500, f"Temporal trends analysis failed: {str(e)}")


@analytics_router.get("/cameras")
async def get_camera_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user: User = Depends(require_detection_view)
):
    """Get camera performance analytics"""
    try:
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence
        )
        
        result = await analytics_engine.get_camera_performance(query)
        
        return {
            "success": True,
            "data": result.data,
            "query_info": {
                "execution_time_ms": result.execution_time_ms
            }
        }
        
    except Exception as e:
        logger.error(f"Camera analytics failed: {e}")
        raise HTTPException(500, f"Camera analytics failed: {str(e)}")


@analytics_router.get("/plates")
async def get_plate_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    camera_ids: Optional[List[str]] = Query(None, description="Camera IDs to analyze"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user: User = Depends(require_detection_view)
):
    """Get license plate pattern analytics"""
    try:
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            camera_ids=camera_ids,
            min_confidence=min_confidence
        )
        
        result = await analytics_engine.get_plate_analytics(query)
        
        return {
            "success": True,
            "data": result.data,
            "query_info": {
                "execution_time_ms": result.execution_time_ms
            }
        }
        
    except Exception as e:
        logger.error(f"Plate analytics failed: {e}")
        raise HTTPException(500, f"Plate analytics failed: {str(e)}")


@analytics_router.get("/performance")
async def get_system_performance(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    current_user: User = Depends(require_detection_view)
):
    """Get system performance analytics"""
    try:
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date
        )
        
        result = await analytics_engine.get_system_performance_analytics(query)
        
        return {
            "success": True,
            "data": result.data,
            "query_info": {
                "execution_time_ms": result.execution_time_ms
            }
        }
        
    except Exception as e:
        logger.error(f"System performance analytics failed: {e}")
        raise HTTPException(500, f"System performance analytics failed: {str(e)}")


@analytics_router.get("/comprehensive-report")
async def generate_comprehensive_report(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    camera_ids: Optional[List[str]] = Query(None, description="Camera IDs to analyze"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    current_user: User = Depends(require_detection_view)
):
    """Generate comprehensive analytics report"""
    try:
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            camera_ids=camera_ids,
            min_confidence=min_confidence
        )
        
        results = await analytics_engine.generate_comprehensive_report(query)
        
        # Combine all results
        combined_data = {}
        total_execution_time = 0
        
        for section_name, result in results.items():
            combined_data[section_name] = result.data
            total_execution_time += result.execution_time_ms
        
        return {
            "success": True,
            "report": combined_data,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "query": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "camera_ids": camera_ids,
                    "min_confidence": min_confidence
                },
                "execution_time_ms": total_execution_time,
                "sections": list(results.keys()),
                "generated_by": current_user.username
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive report generation failed: {e}")
        raise HTTPException(500, f"Report generation failed: {str(e)}")


@analytics_router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(require_detection_view)
):
    """Get real-time dashboard data"""
    try:
        # Get last 24 hours of data for dashboard
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            group_by="hour"
        )
        
        # Get key metrics for dashboard
        overview_task = analytics_engine.get_detection_overview(query)
        trends_task = analytics_engine.get_temporal_trends(query)
        camera_task = analytics_engine.get_camera_performance(query)
        
        # Execute in parallel
        overview = await overview_task
        trends = await trends_task
        cameras = await camera_task
        
        # Create dashboard-friendly format
        dashboard_data = {
            "summary": overview.data.get('summary', {}),
            "recent_trends": trends.data.get('trends', [])[-12:],  # Last 12 hours
            "camera_status": {
                camera_id: {
                    'name': info['camera_info']['name'],
                    'detections': info['metrics']['total_detections'],
                    'confidence': info['metrics']['average_confidence']
                }
                for camera_id, info in cameras.data.get('camera_performance', {}).items()
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "dashboard": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Dashboard data generation failed: {e}")
        raise HTTPException(500, f"Dashboard data failed: {str(e)}")


@analytics_router.get("/export/csv")
async def export_analytics_csv(
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    camera_ids: Optional[List[str]] = Query(None, description="Camera IDs to export"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    export_type: str = Query("detections", regex="^(detections|summary|cameras)$", description="Export type"),
    current_user: User = Depends(require_detection_view)
):
    """Export analytics data as CSV"""
    try:
        from database.service import DatabaseService
        
        db = DatabaseService()
        
        if export_type == "detections":
            # Export raw detections data
            detections = await db.search_detections(
                start_date=start_date,
                end_date=end_date,
                camera_id=camera_ids[0] if camera_ids else None,
                min_confidence=min_confidence,
                limit=10000
            )
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow([
                'Detection ID', 'Camera ID', 'Plate Text', 'Vehicle Type',
                'Confidence', 'Detected At', 'Vehicle BBox', 'Plate BBox'
            ])
            
            # Data rows
            for d in detections:
                writer.writerow([
                    d.id, d.camera_id, d.plate_text, d.vehicle_type,
                    d.confidence, d.detected_at.isoformat() if d.detected_at else '',
                    d.vehicle_bbox, d.plate_bbox
                ])
        
        elif export_type == "summary":
            # Export summary analytics
            query = AnalyticsQuery(
                start_date=start_date,
                end_date=end_date,
                camera_ids=camera_ids,
                min_confidence=min_confidence
            )
            
            overview = await analytics_engine.get_detection_overview(query)
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Summary data
            summary = overview.data.get('summary', {})
            writer.writerow(['Metric', 'Value'])
            for key, value in summary.items():
                if isinstance(value, dict):
                    continue
                writer.writerow([key.replace('_', ' ').title(), value])
        
        await db.close()
        
        # Create response
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=lpr_analytics_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(500, f"CSV export failed: {str(e)}")


@analytics_router.get("/charts/{chart_type}")
async def generate_chart(
    chart_type: str,
    start_date: Optional[datetime] = Query(None, description="Start date for chart"),
    end_date: Optional[datetime] = Query(None, description="End date for chart"),
    camera_ids: Optional[List[str]] = Query(None, description="Camera IDs for chart"),
    width: int = Query(800, ge=200, le=2000, description="Chart width"),
    height: int = Query(600, ge=200, le=1500, description="Chart height"),
    current_user: User = Depends(require_detection_view)
):
    """Generate visualization charts"""
    try:
        chart_generator = ChartGenerator()
        
        query = AnalyticsQuery(
            start_date=start_date,
            end_date=end_date,
            camera_ids=camera_ids
        )
        
        if chart_type == "trends":
            result = await analytics_engine.get_temporal_trends(query)
            chart_data = result.data.get('trends', [])
            chart_bytes = chart_generator.create_trend_chart(chart_data, width, height)
            
        elif chart_type == "cameras":
            result = await analytics_engine.get_camera_performance(query)
            chart_data = result.data.get('camera_performance', {})
            chart_bytes = chart_generator.create_camera_chart(chart_data, width, height)
            
        elif chart_type == "confidence":
            result = await analytics_engine.get_detection_overview(query)
            # This would need confidence distribution data
            chart_bytes = chart_generator.create_confidence_chart({}, width, height)
            
        else:
            raise HTTPException(400, f"Unknown chart type: {chart_type}")
        
        return StreamingResponse(
            io.BytesIO(chart_bytes),
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=lpr_chart_{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            }
        )
        
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        raise HTTPException(500, f"Chart generation failed: {str(e)}")


@analytics_router.post("/reports/generate")
async def generate_custom_report(
    report_config: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_detection_view)
):
    """Generate custom analytics report"""
    try:
        report_generator = ReportGenerator()
        
        def generate_report():
            try:
                # This would generate a PDF report based on config
                report_path = report_generator.generate_pdf_report(
                    report_config, 
                    current_user.username
                )
                logger.info(f"Custom report generated: {report_path}")
                return report_path
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
        
        background_tasks.add_task(generate_report)
        
        return {
            "success": True,
            "message": "Custom report generation started",
            "estimated_completion": "2-5 minutes",
            "config": report_config
        }
        
    except Exception as e:
        logger.error(f"Custom report request failed: {e}")
        raise HTTPException(500, f"Custom report request failed: {str(e)}")


@analytics_router.get("/insights")
async def get_automated_insights(
    start_date: Optional[datetime] = Query(None, description="Start date for insights"),
    end_date: Optional[datetime] = Query(None, description="End date for insights"),
    current_user: User = Depends(require_detection_view)
):
    """Get automated insights and recommendations"""
    try:
        # Use last 7 days if no date range specified
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        query = AnalyticsQuery(start_date=start_date, end_date=end_date)
        
        # Get comprehensive data for insights
        overview = await analytics_engine.get_detection_overview(query)
        trends = await analytics_engine.get_temporal_trends(query) 
        cameras = await analytics_engine.get_camera_performance(query)
        plates = await analytics_engine.get_plate_analytics(query)
        
        # Generate insights
        insights = []
        
        # Detection volume insights
        total_detections = overview.data.get('summary', {}).get('total_detections', 0)
        if total_detections > 1000:
            insights.append({
                'type': 'volume',
                'severity': 'info',
                'title': 'High Detection Volume',
                'description': f'System processed {total_detections} detections in the analysis period',
                'recommendation': 'Consider monitoring storage usage and cleanup policies'
            })
        
        # Camera performance insights
        camera_data = cameras.data.get('camera_performance', {})
        offline_cameras = [cam_id for cam_id, data in camera_data.items() 
                          if data['metrics']['total_detections'] == 0]
        
        if offline_cameras:
            insights.append({
                'type': 'camera',
                'severity': 'warning',
                'title': 'Inactive Cameras Detected',
                'description': f'{len(offline_cameras)} cameras had no detections',
                'recommendation': 'Check camera connectivity and positioning',
                'affected_cameras': offline_cameras
            })
        
        # Confidence insights
        avg_confidence = overview.data.get('summary', {}).get('average_confidence', 0)
        if avg_confidence < 0.7:
            insights.append({
                'type': 'quality',
                'severity': 'warning',
                'title': 'Low Average Confidence',
                'description': f'Average detection confidence is {avg_confidence:.2f}',
                'recommendation': 'Review camera positioning and lighting conditions'
            })
        
        # Frequent visitor insights
        plate_data = plates.data.get('frequent_plates', [])
        if plate_data and len(plate_data) > 0:
            top_plate, visits = plate_data[0]
            if visits > 10:
                insights.append({
                    'type': 'activity',
                    'severity': 'info',
                    'title': 'Frequent Visitor Detected',
                    'description': f'Plate {top_plate} detected {visits} times',
                    'recommendation': 'Review if this indicates normal or unusual activity'
                })
        
        return {
            "success": True,
            "insights": insights,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Automated insights failed: {e}")
        raise HTTPException(500, f"Automated insights failed: {str(e)}")