"""
Chart and Visualization Generation
"""
import io
import base64
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available - chart generation will be disabled")


class ChartGenerator:
    """Generate various types of charts for analytics"""
    
    def __init__(self):
        if MATPLOTLIB_AVAILABLE:
            # Set style
            plt.style.use('default')
            sns.set_palette("husl")
    
    def create_trend_chart(self, trend_data: List[Dict], width: int = 800, height: int = 600) -> bytes:
        """Create time-based trend chart"""
        if not MATPLOTLIB_AVAILABLE:
            return self._create_placeholder_chart("Matplotlib not available")
        
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(width/100, height/100), height_ratios=[3, 1])
            
            if not trend_data:
                ax1.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax1.transAxes)
                ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax2.transAxes)
            else:
                # Parse timestamps and values
                timestamps = []
                counts = []
                confidences = []
                
                for point in trend_data:
                    try:
                        timestamp = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                        timestamps.append(timestamp)
                        counts.append(point['count'])
                        confidences.append(point['average_confidence'])
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Skipping invalid data point: {e}")
                        continue
                
                if timestamps and counts:
                    # Detection counts
                    ax1.plot(timestamps, counts, marker='o', linewidth=2, markersize=4)
                    ax1.set_title('Detection Trends Over Time', fontsize=14, fontweight='bold')
                    ax1.set_ylabel('Detection Count', fontsize=12)
                    ax1.grid(True, alpha=0.3)
                    
                    # Format x-axis
                    if len(timestamps) > 10:
                        ax1.tick_params(axis='x', rotation=45)
                    
                    # Confidence scores
                    if confidences:
                        ax2.plot(timestamps, confidences, marker='s', color='orange', linewidth=2, markersize=3)
                        ax2.set_title('Average Confidence', fontsize=12)
                        ax2.set_ylabel('Confidence', fontsize=10)
                        ax2.set_ylim(0, 1)
                        ax2.grid(True, alpha=0.3)
                        ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_bytes = buffer.getvalue()
            plt.close(fig)
            
            return chart_bytes
            
        except Exception as e:
            logger.error(f"Trend chart generation failed: {e}")
            return self._create_placeholder_chart(f"Chart generation error: {str(e)}")
    
    def create_camera_chart(self, camera_data: Dict[str, Any], width: int = 800, height: int = 600) -> bytes:
        """Create camera performance comparison chart"""
        if not MATPLOTLIB_AVAILABLE:
            return self._create_placeholder_chart("Matplotlib not available")
        
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(width/100, height/100))
            
            if not camera_data:
                for ax in [ax1, ax2, ax3, ax4]:
                    ax.text(0.5, 0.5, 'No camera data', ha='center', va='center', transform=ax.transAxes)
            else:
                # Extract data for visualization
                camera_names = []
                detection_counts = []
                confidence_scores = []
                unique_plates = []
                
                for camera_id, data in camera_data.items():
                    metrics = data.get('metrics', {})
                    camera_info = data.get('camera_info', {})
                    
                    name = camera_info.get('name', camera_id)[:15]  # Truncate long names
                    camera_names.append(name)
                    detection_counts.append(metrics.get('total_detections', 0))
                    confidence_scores.append(metrics.get('average_confidence', 0))
                    unique_plates.append(metrics.get('unique_plates', 0))
                
                if camera_names:
                    # Detection counts bar chart
                    bars1 = ax1.bar(camera_names, detection_counts, color='skyblue')
                    ax1.set_title('Total Detections by Camera', fontsize=12, fontweight='bold')
                    ax1.set_ylabel('Detection Count')
                    ax1.tick_params(axis='x', rotation=45)
                    
                    # Add value labels on bars
                    for bar in bars1:
                        height = bar.get_height()
                        if height > 0:
                            ax1.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{int(height)}', ha='center', va='bottom', fontsize=9)
                    
                    # Confidence scores
                    bars2 = ax2.bar(camera_names, confidence_scores, color='lightgreen')
                    ax2.set_title('Average Confidence by Camera', fontsize=12, fontweight='bold')
                    ax2.set_ylabel('Confidence Score')
                    ax2.set_ylim(0, 1)
                    ax2.tick_params(axis='x', rotation=45)
                    
                    # Add value labels
                    for bar in bars2:
                        height = bar.get_height()
                        if height > 0:
                            ax2.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{height:.2f}', ha='center', va='bottom', fontsize=9)
                    
                    # Unique plates
                    bars3 = ax3.bar(camera_names, unique_plates, color='coral')
                    ax3.set_title('Unique Plates by Camera', fontsize=12, fontweight='bold')
                    ax3.set_ylabel('Unique Plates')
                    ax3.tick_params(axis='x', rotation=45)
                    
                    # Efficiency ratio (unique plates / total detections)
                    efficiency = [u/d if d > 0 else 0 for u, d in zip(unique_plates, detection_counts)]
                    bars4 = ax4.bar(camera_names, efficiency, color='gold')
                    ax4.set_title('Detection Efficiency', fontsize=12, fontweight='bold')
                    ax4.set_ylabel('Unique Plates / Total Detections')
                    ax4.tick_params(axis='x', rotation=45)
                    ax4.set_ylim(0, 1)
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_bytes = buffer.getvalue()
            plt.close(fig)
            
            return chart_bytes
            
        except Exception as e:
            logger.error(f"Camera chart generation failed: {e}")
            return self._create_placeholder_chart(f"Chart generation error: {str(e)}")
    
    def create_confidence_chart(self, data: Dict[str, Any], width: int = 800, height: int = 600) -> bytes:
        """Create confidence score distribution chart"""
        if not MATPLOTLIB_AVAILABLE:
            return self._create_placeholder_chart("Matplotlib not available")
        
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(width/100, height/100))
            
            # This would need actual confidence distribution data
            # For now, create a placeholder
            confidence_ranges = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
            counts = [10, 25, 45, 150, 300]  # Example data
            
            # Histogram
            ax1.bar(confidence_ranges, counts, color='lightblue', edgecolor='navy')
            ax1.set_title('Confidence Score Distribution', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Confidence Range')
            ax1.set_ylabel('Detection Count')
            ax1.tick_params(axis='x', rotation=45)
            
            # Pie chart
            ax2.pie(counts, labels=confidence_ranges, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Confidence Distribution', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_bytes = buffer.getvalue()
            plt.close(fig)
            
            return chart_bytes
            
        except Exception as e:
            logger.error(f"Confidence chart generation failed: {e}")
            return self._create_placeholder_chart(f"Chart generation error: {str(e)}")
    
    def create_heatmap_chart(self, data: Dict[str, Any], width: int = 800, height: int = 600) -> bytes:
        """Create activity heatmap"""
        if not MATPLOTLIB_AVAILABLE:
            return self._create_placeholder_chart("Matplotlib not available")
        
        try:
            fig, ax = plt.subplots(figsize=(width/100, height/100))
            
            # Create sample heatmap data (24 hours x 7 days)
            import numpy as np
            
            # Sample data - in real implementation, this would come from actual detection data
            detection_activity = np.random.randint(0, 50, size=(7, 24))
            
            # Create heatmap
            im = ax.imshow(detection_activity, cmap='YlOrRd', aspect='auto')
            
            # Set labels
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            hours = [f'{i:02d}:00' for i in range(24)]
            
            ax.set_xticks(range(24))
            ax.set_xticklabels(hours, rotation=45)
            ax.set_yticks(range(7))
            ax.set_yticklabels(days)
            
            ax.set_title('Detection Activity Heatmap', fontsize=14, fontweight='bold')
            ax.set_xlabel('Hour of Day')
            ax.set_ylabel('Day of Week')
            
            # Add colorbar
            plt.colorbar(im, ax=ax, label='Detection Count')
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_bytes = buffer.getvalue()
            plt.close(fig)
            
            return chart_bytes
            
        except Exception as e:
            logger.error(f"Heatmap generation failed: {e}")
            return self._create_placeholder_chart(f"Chart generation error: {str(e)}")
    
    def _create_placeholder_chart(self, message: str = "Chart not available") -> bytes:
        """Create a placeholder chart when generation fails"""
        if not MATPLOTLIB_AVAILABLE:
            # Create a simple text-based placeholder
            return b"Chart generation not available - matplotlib required"
        
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, message, ha='center', va='center', 
                   transform=ax.transAxes, fontsize=16)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xticks([])
            ax.set_yticks([])
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_bytes = buffer.getvalue()
            plt.close(fig)
            
            return chart_bytes
        except:
            return b"Unable to generate placeholder chart"


class DashboardGenerator:
    """Generate dashboard components and layouts"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator()
    
    def create_dashboard_widget(self, widget_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dashboard widget configuration"""
        
        widgets = {
            "metric_card": {
                "type": "metric",
                "title": data.get("title", "Metric"),
                "value": data.get("value", 0),
                "change": data.get("change", 0),
                "format": data.get("format", "number"),
                "color": self._get_metric_color(data.get("change", 0))
            },
            
            "trend_chart": {
                "type": "chart", 
                "chart_type": "line",
                "title": data.get("title", "Trends"),
                "data": data.get("trend_data", []),
                "height": 300
            },
            
            "camera_status": {
                "type": "status_grid",
                "title": "Camera Status",
                "cameras": data.get("cameras", {}),
                "columns": 2
            },
            
            "top_plates": {
                "type": "list",
                "title": "Most Detected Plates",
                "items": data.get("plates", []),
                "show_count": True,
                "max_items": 10
            },
            
            "alert_summary": {
                "type": "alert_panel",
                "alerts": data.get("alerts", []),
                "severity_counts": data.get("severity_counts", {})
            }
        }
        
        return widgets.get(widget_type, {"type": "unknown", "error": "Unknown widget type"})
    
    def _get_metric_color(self, change: float) -> str:
        """Get color based on metric change"""
        if change > 0:
            return "green"
        elif change < 0:
            return "red"
        else:
            return "blue"
    
    def create_dashboard_layout(self, widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create complete dashboard layout"""
        return {
            "layout": {
                "type": "grid",
                "columns": 12,
                "gap": 16,
                "widgets": widgets
            },
            "theme": {
                "primary_color": "#2196F3",
                "secondary_color": "#FFC107",
                "success_color": "#4CAF50",
                "warning_color": "#FF9800",
                "error_color": "#F44336",
                "background_color": "#FAFAFA"
            },
            "refresh_interval": 30000,  # 30 seconds
            "generated_at": datetime.now().isoformat()
        }


class ReportGenerator:
    """Generate PDF and other formatted reports"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator()
    
    def generate_pdf_report(self, config: Dict[str, Any], username: str) -> str:
        """Generate PDF report (placeholder implementation)"""
        # This would use libraries like reportlab or weasyprint
        # For now, return a mock file path
        
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"reports/lpr_analytics_report_{report_id}.pdf"
        
        logger.info(f"PDF report generation requested by {username}: {report_path}")
        
        # Mock report generation
        import os
        os.makedirs("reports", exist_ok=True)
        
        # Create a placeholder file
        with open(report_path, "w") as f:
            f.write(f"LPR Analytics Report\nGenerated: {datetime.now()}\nRequested by: {username}\nConfig: {config}")
        
        return report_path
    
    def generate_excel_report(self, data: Dict[str, Any]) -> bytes:
        """Generate Excel report (placeholder)"""
        # This would use openpyxl or xlswriter
        # For now, return CSV-like content
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers and data
        writer.writerow(["Report Type", "Value"])
        for key, value in data.items():
            if isinstance(value, (str, int, float)):
                writer.writerow([key, value])
        
        return output.getvalue().encode()


# Export classes for use in endpoints
__all__ = ['ChartGenerator', 'DashboardGenerator', 'ReportGenerator']