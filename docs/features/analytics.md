# Analytics & Visualization System

## Overview

The LPR system now includes a comprehensive analytics and visualization platform that transforms detection data into actionable business insights, performance metrics, and automated reports.

## Features

### 📊 **Analytics Engine**
- **Detection Analytics**: Comprehensive detection statistics, confidence analysis, and vehicle type distributions
- **Temporal Trends**: Time-based pattern analysis with flexible grouping (hour, day, week, month)
- **Camera Performance**: Individual camera metrics, rankings, and efficiency analysis
- **Plate Analytics**: License plate pattern recognition, frequent visitor tracking, and format analysis
- **System Performance**: Processing speed metrics, resource utilization, and optimization insights

### 📈 **Visualization Components**
- **Interactive Charts**: Time-series trends, bar charts, and distribution visualizations
- **Dashboard Widgets**: Real-time metric cards, status panels, and alert summaries
- **Heatmaps**: Activity pattern visualization across time periods
- **Performance Graphs**: Camera comparison charts and confidence score distributions
- **Export Capabilities**: PNG chart export with customizable dimensions

### 📋 **Reporting System**
- **Automated Reports**: Daily, weekly, and monthly scheduled reports
- **Custom Reports**: User-configurable report generation with multiple sections
- **Multiple Formats**: PDF reports, Excel exports, CSV data dumps, and JSON structured reports
- **Template System**: Pre-built report templates for common use cases

### 🤖 **Automated Insights**
- **Anomaly Detection**: Unusual activity patterns and system irregularities
- **Performance Recommendations**: Optimization suggestions based on analytics
- **Alert Generation**: Proactive notifications for system issues
- **Trend Predictions**: Pattern-based forecasting and insights

## API Endpoints

### Core Analytics Endpoints

#### Detection Overview
```bash
GET /api/analytics/overview?start_date=2025-08-01&end_date=2025-08-12
Authorization: Bearer <token>

{
  "success": true,
  "data": {
    "summary": {
      "total_detections": 15847,
      "unique_plates": 3241,
      "average_confidence": 0.847,
      "detections_per_hour": 28.4,
      "date_range": {
        "start": "2025-08-01T00:00:00",
        "end": "2025-08-12T23:59:59",
        "first_detection": "2025-08-01T06:23:15",
        "last_detection": "2025-08-12T18:45:32"
      }
    },
    "distributions": {
      "vehicle_types": {
        "car": 12847,
        "truck": 2154,
        "motorcycle": 846
      },
      "cameras": {
        "cam_entrance": 8924,
        "cam_exit": 6923
      }
    }
  },
  "query_info": {
    "execution_time_ms": 245.7
  }
}
```

#### Temporal Trends Analysis
```bash
GET /api/analytics/trends?group_by=day&start_date=2025-08-01
Authorization: Bearer <token>

{
  "success": true,
  "data": {
    "trends": [
      {
        "timestamp": "2025-08-01T00:00:00",
        "count": 247,
        "average_confidence": 0.852
      },
      {
        "timestamp": "2025-08-02T00:00:00", 
        "count": 312,
        "average_confidence": 0.841
      }
    ],
    "analysis": {
      "total_periods": 12,
      "peak_time": {
        "timestamp": "2025-08-08T00:00:00",
        "count": 445,
        "average_confidence": 0.863
      },
      "group_by": "day"
    }
  }
}
```

#### Camera Performance Analytics
```bash
GET /api/analytics/cameras?min_confidence=0.7
Authorization: Bearer <token>

{
  "success": true,
  "data": {
    "camera_performance": {
      "cam_entrance": {
        "camera_info": {
          "name": "Main Entrance",
          "location": "Building A"
        },
        "metrics": {
          "total_detections": 8924,
          "unique_plates": 2156,
          "average_confidence": 0.871,
          "confidence_range": {
            "min": 0.623,
            "max": 0.987
          },
          "peak_hour": 14,
          "vehicle_types": {
            "car": 7234,
            "truck": 1245,
            "motorcycle": 445
          }
        }
      }
    },
    "rankings": {
      "most_detections": [
        ["cam_entrance", 8924],
        ["cam_exit", 6923]
      ],
      "highest_confidence": [
        ["cam_entrance", 0.871],
        ["cam_exit", 0.823]
      ]
    }
  }
}
```

#### License Plate Pattern Analysis
```bash
GET /api/analytics/plates?start_date=2025-08-01&end_date=2025-08-12
Authorization: Bearer <token>

{
  "success": true,
  "data": {
    "summary": {
      "total_unique_plates": 3241,
      "total_detections": 15847,
      "frequent_plates_count": 847,
      "multi_camera_plates_count": 234
    },
    "frequent_plates": [
      ["ABC1234", 23],
      ["XYZ5678", 18],
      ["DEF9012", 15]
    ],
    "multi_camera_plates": [
      ["ABC1234", 3],
      ["GHI3456", 2]
    ],
    "visit_analysis": {
      "ABC1234": {
        "visits": 23,
        "duration_minutes": 1247.5,
        "cameras": 3,
        "average_confidence": 0.887,
        "first_seen": "2025-08-01T08:23:15",
        "last_seen": "2025-08-12T16:45:23"
      }
    },
    "pattern_analysis": {
      "format_distribution": {
        "texas_standard": 2847,
        "mixed": 394,
        "numeric_only": 0,
        "unknown": 0
      },
      "length_distribution": {
        "6": 1234,
        "7": 2007
      },
      "most_common_length": 7
    }
  }
}
```

### Visualization Endpoints

#### Generate Charts
```bash
GET /api/analytics/charts/trends?width=1200&height=800&start_date=2025-08-01
Authorization: Bearer <token>

# Returns PNG image data
Content-Type: image/png
Content-Disposition: inline; filename=lpr_chart_trends_20250812_143052.png
```

#### Dashboard Data
```bash
GET /api/analytics/dashboard
Authorization: Bearer <token>

{
  "success": true,
  "dashboard": {
    "summary": {
      "total_detections": 847,
      "unique_plates": 234,
      "average_confidence": 0.863,
      "detections_per_hour": 35.3
    },
    "recent_trends": [
      {
        "timestamp": "2025-08-12T06:00:00",
        "count": 12,
        "average_confidence": 0.845
      },
      {
        "timestamp": "2025-08-12T07:00:00",
        "count": 28,
        "average_confidence": 0.867
      }
    ],
    "camera_status": {
      "cam_entrance": {
        "name": "Main Entrance",
        "detections": 423,
        "confidence": 0.871
      },
      "cam_exit": {
        "name": "Exit Gate",
        "detections": 424,
        "confidence": 0.854
      }
    },
    "last_updated": "2025-08-12T14:30:52"
  }
}
```

### Export Endpoints

#### CSV Data Export
```bash
GET /api/analytics/export/csv?export_type=detections&start_date=2025-08-01
Authorization: Bearer <token>

# Returns CSV file
Content-Type: text/csv
Content-Disposition: attachment; filename=lpr_analytics_detections_20250812_143052.csv

Detection ID,Camera ID,Plate Text,Vehicle Type,Confidence,Detected At
det_001,cam_entrance,ABC1234,car,0.871,2025-08-01T08:23:15
det_002,cam_exit,XYZ5678,truck,0.823,2025-08-01T08:24:23
```

#### Comprehensive Report
```bash
GET /api/analytics/comprehensive-report?start_date=2025-08-01&end_date=2025-08-12
Authorization: Bearer <token>

{
  "success": true,
  "report": {
    "overview": {
      "summary": { /* overview data */ },
      "distributions": { /* distribution data */ }
    },
    "temporal_trends": {
      "trends": [ /* trend data */ ],
      "analysis": { /* trend analysis */ }
    },
    "camera_performance": {
      "camera_performance": { /* camera data */ },
      "rankings": { /* camera rankings */ }
    },
    "plate_analytics": {
      "summary": { /* plate summary */ },
      "frequent_plates": [ /* frequent plates */ ]
    },
    "system_performance": {
      "system_performance": { /* performance metrics */ }
    }
  },
  "metadata": {
    "generated_at": "2025-08-12T14:30:52",
    "execution_time_ms": 1247.3,
    "sections": ["overview", "temporal_trends", "camera_performance", "plate_analytics", "system_performance"],
    "generated_by": "admin"
  }
}
```

### Insights & Recommendations

#### Automated Insights
```bash
GET /api/analytics/insights?start_date=2025-08-05&end_date=2025-08-12
Authorization: Bearer <token>

{
  "success": true,
  "insights": [
    {
      "type": "volume",
      "severity": "info",
      "title": "High Detection Volume",
      "description": "System processed 15847 detections in the analysis period",
      "recommendation": "Consider monitoring storage usage and cleanup policies"
    },
    {
      "type": "camera",
      "severity": "warning",
      "title": "Inactive Cameras Detected",
      "description": "1 cameras had no detections",
      "recommendation": "Check camera connectivity and positioning",
      "affected_cameras": ["cam_backup"]
    },
    {
      "type": "activity",
      "severity": "info",
      "title": "Frequent Visitor Detected", 
      "description": "Plate ABC1234 detected 23 times",
      "recommendation": "Review if this indicates normal or unusual activity"
    }
  ],
  "analysis_period": {
    "start": "2025-08-05T00:00:00",
    "end": "2025-08-12T23:59:59"
  }
}
```

## Usage Examples

### Basic Analytics Query

```bash
# 1. Get authentication token
TOKEN=$(curl -X POST http://localhost:8001/api/auth/login \
  -d '{"username":"admin","password":"admin123"}' \
  -H "Content-Type: application/json" | jq -r .access_token)

# 2. Get detection overview for last 7 days
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/overview?start_date=$(date -d '7 days ago' -I)&end_date=$(date -I)"

# 3. Get hourly trends for today
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/trends?group_by=hour&start_date=$(date -I)"

# 4. Get camera performance analytics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/cameras?min_confidence=0.8"

# 5. Export detection data as CSV
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/export/csv?export_type=detections" \
  -o detections_export.csv
```

### Dashboard Integration

```javascript
// Frontend dashboard integration example
async function loadDashboardData() {
  const response = await fetch('/api/analytics/dashboard', {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  
  if (data.success) {
    updateMetricCards(data.dashboard.summary);
    updateTrendChart(data.dashboard.recent_trends);
    updateCameraStatus(data.dashboard.camera_status);
  }
}

// Update dashboard every 30 seconds
setInterval(loadDashboardData, 30000);
```

### Custom Report Generation

```bash
# Generate custom analytics report
curl -X POST http://localhost:8001/api/analytics/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "weekly_analytics",
    "date_range": {
      "start": "2025-08-01",
      "end": "2025-08-08"
    },
    "sections": ["overview", "trends", "cameras"],
    "format": "pdf",
    "email_recipients": ["admin@company.com"]
  }'
```

## Integration Examples

### Grafana Dashboard Integration

Use analytics API data to populate Grafana dashboards:

```json
{
  "dashboard": {
    "title": "LPR Analytics Dashboard",
    "panels": [
      {
        "title": "Detection Rate",
        "type": "stat",
        "targets": [
          {
            "url": "http://localhost:8001/api/analytics/overview",
            "method": "GET",
            "headers": {"Authorization": "Bearer ${token}"},
            "jsonPath": "$.data.summary.detections_per_hour"
          }
        ]
      },
      {
        "title": "Detection Trends",
        "type": "timeseries",
        "targets": [
          {
            "url": "http://localhost:8001/api/analytics/trends?group_by=hour",
            "jsonPath": "$.data.trends[*].{timestamp: timestamp, count: count}"
          }
        ]
      }
    ]
  }
}
```

### Business Intelligence Integration

Connect analytics API to BI tools like Tableau, Power BI, or Looker:

```sql
-- SQL-like query structure for BI integration
SELECT 
  camera_id,
  COUNT(*) as total_detections,
  AVG(confidence) as avg_confidence,
  COUNT(DISTINCT plate_text) as unique_plates
FROM analytics_api('/api/analytics/overview')
WHERE detected_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY camera_id
ORDER BY total_detections DESC
```

### Automated Alerting

Set up automated alerts based on analytics insights:

```python
import requests
import schedule
import time

def check_system_alerts():
    response = requests.get(
        'http://localhost:8001/api/analytics/insights',
        headers={'Authorization': f'Bearer {token}'},
        params={'start_date': (datetime.now() - timedelta(hours=1)).isoformat()}
    )
    
    if response.status_code == 200:
        insights = response.json()['insights']
        
        # Check for critical issues
        critical_alerts = [i for i in insights if i['severity'] == 'critical']
        if critical_alerts:
            send_email_alert(critical_alerts)
        
        # Check for warnings
        warning_alerts = [i for i in insights if i['severity'] == 'warning']
        if len(warning_alerts) > 3:
            send_slack_notification(warning_alerts)

# Schedule to run every hour
schedule.every().hour.do(check_system_alerts)
```

## Performance Optimization

### Query Optimization

```bash
# Use date ranges to limit data processing
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/overview?start_date=2025-08-12T00:00:00&end_date=2025-08-12T23:59:59"

# Filter by confidence to focus on high-quality detections
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/cameras?min_confidence=0.8"

# Use specific camera IDs to reduce processing
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/trends?camera_ids=cam_entrance,cam_exit"
```

### Caching Strategy

Analytics results are automatically cached for performance:

- **Detection overview**: Cached for 5 minutes
- **Temporal trends**: Cached for 2 minutes  
- **Camera performance**: Cached for 10 minutes
- **System performance**: Cached for 1 minute

### Large Dataset Handling

For systems with large detection volumes:

- Use date range filtering to limit data processing
- Implement pagination for large result sets
- Use background report generation for comprehensive reports
- Enable database indexing on timestamp and camera_id fields

## Configuration

### Analytics Settings

```env
# Analytics Configuration
ANALYTICS_CACHE_TTL=300
ANALYTICS_MAX_QUERY_DAYS=365
ANALYTICS_DEFAULT_LIMIT=10000
ANALYTICS_ENABLE_CHARTS=true
ANALYTICS_REPORT_STORAGE_DAYS=90
```

### Report Templates

Customize report templates in `analytics/reports.py`:

```python
templates = {
    "custom_daily": ReportTemplate(
        name="custom_daily",
        title="Custom Daily Report",
        sections=["overview", "top_plates", "camera_alerts"],
        format="pdf",
        schedule="daily"
    )
}
```

### Visualization Themes

Configure chart styling in `analytics/visualizations.py`:

```python
theme = {
    "primary_color": "#2196F3",
    "secondary_color": "#FFC107", 
    "success_color": "#4CAF50",
    "warning_color": "#FF9800",
    "error_color": "#F44336"
}
```

## Troubleshooting

### Common Issues

**Analytics Query Timeout**
```bash
# Check if date range is too large
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/overview?start_date=2025-08-01&end_date=2025-08-02"

# Verify database connectivity
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/monitoring/health/detailed"
```

**Chart Generation Fails**
```bash
# Verify matplotlib installation
python3 -c "import matplotlib; print('Matplotlib available')"

# Check chart endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/charts/trends?width=800&height=600"
```

**Report Generation Issues**
```bash
# Check reports directory permissions
ls -la reports/

# Verify report templates
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/reports/templates"
```

### Debug Mode

Enable debug logging for analytics:

```python
import logging
logging.getLogger('analytics').setLevel(logging.DEBUG)
```

### Performance Monitoring

Monitor analytics performance:

```bash
# Check analytics execution times
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/overview" | jq .query_info.execution_time_ms

# Monitor database query performance
tail -f logs/database.log | grep -i analytics
```

## Future Enhancements

### Planned Features
1. **Machine Learning Integration**: Predictive analytics and anomaly detection
2. **Real-time Streaming**: WebSocket-based real-time analytics updates
3. **Advanced Visualizations**: 3D charts, geographic heatmaps, and interactive dashboards
4. **Mobile Analytics**: Mobile-responsive dashboard and native app integration
5. **API Rate Limiting**: Enhanced performance controls for high-volume queries

### Advanced Analytics
- **Seasonal Pattern Detection**: Identify recurring patterns in detection data
- **Comparative Analysis**: Period-over-period comparisons and trend analysis
- **Predictive Modeling**: Forecast detection volumes and system requirements
- **Behavioral Analytics**: User interaction patterns and system usage analytics

The analytics system provides comprehensive business intelligence capabilities for the LPR system, enabling data-driven decision making and operational optimization.