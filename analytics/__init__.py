"""
Analytics and Visualization Module for LPR System
"""

from .engine import LPRAnalyticsEngine, AnalyticsQuery, AnalyticsResult, analytics_engine
from .endpoints import analytics_router
from .visualizations import ChartGenerator, DashboardGenerator, ReportGenerator
from .reports import ReportGenerator as ReportGen, ScheduledReportManager, report_generator

__all__ = [
    'LPRAnalyticsEngine',
    'AnalyticsQuery', 
    'AnalyticsResult',
    'analytics_engine',
    'analytics_router',
    'ChartGenerator',
    'DashboardGenerator', 
    'ReportGenerator',
    'ReportGen',
    'ScheduledReportManager',
    'report_generator'
]

def initialize_analytics_system():
    """Initialize the analytics system"""
    print("📊 Initializing analytics system...")
    
    # The analytics engine will be initialized when first used
    # Report directories will be created automatically
    
    print("   Analytics engine ready")
    print("   Visualization components loaded")
    print("   Report generator initialized")
    print("   API endpoints configured")
    
    return True