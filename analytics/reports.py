"""
Report Generation System for LPR Analytics
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReportTemplate:
    """Report template configuration"""
    name: str
    title: str
    sections: List[str]
    format: str = "pdf"  # pdf, excel, json
    schedule: Optional[str] = None  # daily, weekly, monthly


class ReportGenerator:
    """Generate various types of reports for LPR system"""
    
    def __init__(self):
        self.templates = self._load_report_templates()
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _load_report_templates(self) -> Dict[str, ReportTemplate]:
        """Load predefined report templates"""
        templates = {
            "daily_summary": ReportTemplate(
                name="daily_summary",
                title="Daily Detection Summary",
                sections=["overview", "camera_performance", "top_plates", "alerts"],
                format="pdf",
                schedule="daily"
            ),
            "weekly_analytics": ReportTemplate(
                name="weekly_analytics", 
                title="Weekly Analytics Report",
                sections=["overview", "trends", "camera_performance", "plate_analytics", "insights"],
                format="pdf",
                schedule="weekly"
            ),
            "monthly_executive": ReportTemplate(
                name="monthly_executive",
                title="Monthly Executive Summary",
                sections=["overview", "trends", "performance", "recommendations"],
                format="pdf",
                schedule="monthly"
            ),
            "camera_health": ReportTemplate(
                name="camera_health",
                title="Camera Health Report",
                sections=["camera_performance", "system_performance", "alerts"],
                format="pdf"
            ),
            "data_export": ReportTemplate(
                name="data_export",
                title="Raw Data Export",
                sections=["detections", "summary"],
                format="excel"
            )
        }
        return templates
    
    async def generate_report(self, template_name: str, analytics_data: Dict[str, Any], 
                            options: Dict[str, Any] = None) -> str:
        """Generate a report using specified template"""
        
        if template_name not in self.templates:
            raise ValueError(f"Unknown report template: {template_name}")
        
        template = self.templates[template_name]
        options = options or {}
        
        # Generate report based on format
        if template.format == "pdf":
            return await self._generate_pdf_report(template, analytics_data, options)
        elif template.format == "excel":
            return await self._generate_excel_report(template, analytics_data, options)
        elif template.format == "json":
            return await self._generate_json_report(template, analytics_data, options)
        else:
            raise ValueError(f"Unsupported report format: {template.format}")
    
    async def _generate_pdf_report(self, template: ReportTemplate, 
                                 analytics_data: Dict[str, Any], 
                                 options: Dict[str, Any]) -> str:
        """Generate PDF report"""
        try:
            # This is a simplified implementation
            # In production, you'd use libraries like reportlab, weasyprint, or jinja2 + html2pdf
            
            report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{template.name}_{report_id}.pdf"
            report_path = os.path.join(self.reports_dir, report_filename)
            
            # Create report content
            content = await self._create_report_content(template, analytics_data, options)
            
            # For this implementation, we'll create a text file as placeholder
            # In production, this would generate actual PDF
            with open(report_path.replace('.pdf', '.txt'), 'w') as f:
                f.write(content)
            
            logger.info(f"PDF report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"PDF report generation failed: {e}")
            raise
    
    async def _generate_excel_report(self, template: ReportTemplate,
                                   analytics_data: Dict[str, Any],
                                   options: Dict[str, Any]) -> str:
        """Generate Excel report"""
        try:
            report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{template.name}_{report_id}.xlsx"
            report_path = os.path.join(self.reports_dir, report_filename)
            
            # This would use openpyxl or xlsxwriter
            # For now, create CSV as placeholder
            csv_path = report_path.replace('.xlsx', '.csv')
            
            import csv
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['Report', template.title])
                writer.writerow(['Generated', datetime.now().isoformat()])
                writer.writerow([''])
                
                # Write analytics data
                for section_name, section_data in analytics_data.items():
                    writer.writerow([f'=== {section_name.upper()} ==='])
                    
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            if isinstance(value, (str, int, float)):
                                writer.writerow([key, value])
                    
                    writer.writerow([''])
            
            logger.info(f"Excel report generated: {csv_path}")
            return csv_path
            
        except Exception as e:
            logger.error(f"Excel report generation failed: {e}")
            raise
    
    async def _generate_json_report(self, template: ReportTemplate,
                                  analytics_data: Dict[str, Any],
                                  options: Dict[str, Any]) -> str:
        """Generate JSON report"""
        try:
            report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{template.name}_{report_id}.json"
            report_path = os.path.join(self.reports_dir, report_filename)
            
            # Create structured JSON report
            report_data = {
                "report_info": {
                    "template": template.name,
                    "title": template.title,
                    "generated_at": datetime.now().isoformat(),
                    "sections": template.sections,
                    "options": options
                },
                "analytics_data": analytics_data,
                "metadata": {
                    "version": "1.0",
                    "format": "json"
                }
            }
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"JSON report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"JSON report generation failed: {e}")
            raise
    
    async def _create_report_content(self, template: ReportTemplate,
                                   analytics_data: Dict[str, Any],
                                   options: Dict[str, Any]) -> str:
        """Create formatted report content"""
        
        content = f"""
{template.title}
{'=' * len(template.title)}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Template: {template.name}

"""
        
        # Process each section
        for section in template.sections:
            if section in analytics_data:
                content += await self._format_section(section, analytics_data[section])
        
        return content
    
    async def _format_section(self, section_name: str, section_data: Any) -> str:
        """Format a report section"""
        
        content = f"\n{section_name.replace('_', ' ').title()}\n"
        content += "-" * len(content.strip()) + "\n\n"
        
        if isinstance(section_data, dict):
            # Handle different data structures
            if 'summary' in section_data:
                summary = section_data['summary']
                content += "Summary:\n"
                for key, value in summary.items():
                    if isinstance(value, (str, int, float)):
                        content += f"  {key.replace('_', ' ').title()}: {value}\n"
            
            if 'camera_performance' in section_data:
                content += "\nCamera Performance:\n"
                for camera_id, perf in section_data['camera_performance'].items():
                    metrics = perf.get('metrics', {})
                    content += f"  {camera_id}: {metrics.get('total_detections', 0)} detections, "
                    content += f"{metrics.get('average_confidence', 0):.3f} avg confidence\n"
            
            if 'frequent_plates' in section_data:
                content += "\nMost Detected Plates:\n"
                for plate, count in section_data['frequent_plates'][:10]:
                    content += f"  {plate}: {count} times\n"
            
            if 'trends' in section_data:
                content += "\nRecent Trends:\n"
                trends = section_data['trends'][-5:]  # Last 5 data points
                for trend in trends:
                    content += f"  {trend.get('timestamp', 'Unknown')}: {trend.get('count', 0)} detections\n"
        
        elif isinstance(section_data, list):
            for item in section_data[:10]:  # Limit to first 10 items
                content += f"  {item}\n"
        
        else:
            content += f"  {section_data}\n"
        
        content += "\n"
        return content
    
    def generate_scheduled_reports(self, schedule_type: str = "daily") -> List[str]:
        """Generate all scheduled reports of specified type"""
        
        generated_reports = []
        
        for template_name, template in self.templates.items():
            if template.schedule == schedule_type:
                try:
                    # This would be called by a scheduler
                    logger.info(f"Generating scheduled report: {template_name}")
                    
                    # For now, just create a placeholder
                    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_filename = f"scheduled_{template_name}_{report_id}.txt"
                    report_path = os.path.join(self.reports_dir, report_filename)
                    
                    with open(report_path, 'w') as f:
                        f.write(f"Scheduled Report: {template.title}\n")
                        f.write(f"Generated: {datetime.now()}\n")
                        f.write(f"Schedule: {schedule_type}\n")
                    
                    generated_reports.append(report_path)
                    
                except Exception as e:
                    logger.error(f"Failed to generate scheduled report {template_name}: {e}")
        
        return generated_reports
    
    def get_report_templates(self) -> List[Dict[str, Any]]:
        """Get available report templates"""
        return [
            {
                "name": template.name,
                "title": template.title,
                "sections": template.sections,
                "format": template.format,
                "schedule": template.schedule
            }
            for template in self.templates.values()
        ]
    
    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Clean up old report files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for filename in os.listdir(self.reports_dir):
                file_path = os.path.join(self.reports_dir, filename)
                
                # Check file age
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.debug(f"Deleted old report: {filename}")
                    except OSError as e:
                        logger.warning(f"Failed to delete report {filename}: {e}")
            
            logger.info(f"Report cleanup complete: {deleted_count} files removed")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Report cleanup failed: {e}")
            return 0


class ScheduledReportManager:
    """Manage automated report generation"""
    
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.schedules = {
            "daily": {"hour": 6, "minute": 0},      # 6:00 AM daily
            "weekly": {"day": 1, "hour": 6, "minute": 0},  # Monday 6:00 AM
            "monthly": {"day": 1, "hour": 6, "minute": 0}  # 1st of month 6:00 AM
        }
    
    async def check_and_run_scheduled_reports(self):
        """Check if any scheduled reports need to be generated"""
        now = datetime.now()
        
        # Daily reports
        if now.hour == 6 and now.minute == 0:
            logger.info("Generating daily scheduled reports")
            self.report_generator.generate_scheduled_reports("daily")
        
        # Weekly reports (Monday)
        if now.weekday() == 0 and now.hour == 6 and now.minute == 0:
            logger.info("Generating weekly scheduled reports")
            self.report_generator.generate_scheduled_reports("weekly")
        
        # Monthly reports (1st of month)
        if now.day == 1 and now.hour == 6 and now.minute == 0:
            logger.info("Generating monthly scheduled reports")
            self.report_generator.generate_scheduled_reports("monthly")
    
    def get_next_scheduled_run(self, schedule_type: str) -> Optional[datetime]:
        """Get the next scheduled run time for a report type"""
        now = datetime.now()
        
        if schedule_type == "daily":
            next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule_type == "weekly":
            # Next Monday at 6:00 AM
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = (now + timedelta(days_ahead)).replace(hour=6, minute=0, second=0, microsecond=0)
            return next_run
        
        elif schedule_type == "monthly":
            # 1st of next month at 6:00 AM
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1, hour=6, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=1, hour=6, minute=0, second=0, microsecond=0)
            return next_run
        
        return None


# Global instances
report_generator = ReportGenerator()
scheduled_report_manager = ScheduledReportManager()