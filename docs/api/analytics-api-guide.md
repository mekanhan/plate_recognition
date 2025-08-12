# Analytics API Usage Guide

## Overview

This guide provides complete documentation for using the LPR Analytics API. The analytics system transforms detection data into business insights through comprehensive endpoints for data analysis, visualization, and reporting.

## Authentication

All analytics endpoints require JWT authentication. Include the Bearer token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

### Getting an Auth Token

```bash
# Login to get token
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response contains access_token
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 43200
}
```

## Base URL

All analytics endpoints are prefixed with `/api/analytics`:

```
http://localhost:8001/api/analytics/
```

## Core Analytics Endpoints

### 1. Detection Overview

Get comprehensive detection statistics and summaries.

**Endpoint:** `GET /api/analytics/overview`

**Query Parameters:**
- `start_date` (optional): Start date for analysis (ISO format)
- `end_date` (optional): End date for analysis (ISO format)
- `camera_ids` (optional): Comma-separated camera IDs to filter
- `vehicle_types` (optional): Comma-separated vehicle types
- `min_confidence` (optional): Minimum confidence threshold (0.0-1.0)

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/overview?start_date=2025-08-01T00:00:00&end_date=2025-08-12T23:59:59&min_confidence=0.7"
```

**Response:**

```json
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
    "start_date": "2025-08-01T00:00:00",
    "end_date": "2025-08-12T23:59:59",
    "execution_time_ms": 245.7
  },
  "user": "admin"
}
```

### 2. Temporal Trends Analysis

Get time-based detection patterns with flexible grouping.

**Endpoint:** `GET /api/analytics/trends`

**Query Parameters:**
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis
- `camera_ids` (optional): Camera IDs to analyze
- `group_by` (optional): Time grouping - `hour`, `day`, `week`, `month` (default: `day`)
- `min_confidence` (optional): Minimum confidence threshold

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/trends?group_by=hour&start_date=2025-08-12T00:00:00&end_date=2025-08-12T23:59:59"
```

**Response:**

```json
{
  "success": true,
  "data": {
    "trends": [
      {
        "timestamp": "2025-08-12T08:00:00",
        "count": 45,
        "average_confidence": 0.852
      },
      {
        "timestamp": "2025-08-12T09:00:00",
        "count": 67,
        "average_confidence": 0.841
      },
      {
        "timestamp": "2025-08-12T10:00:00",
        "count": 52,
        "average_confidence": 0.863
      }
    ],
    "analysis": {
      "total_periods": 24,
      "peak_time": {
        "timestamp": "2025-08-12T14:00:00",
        "count": 89,
        "average_confidence": 0.876
      },
      "lowest_time": {
        "timestamp": "2025-08-12T03:00:00",
        "count": 5,
        "average_confidence": 0.743
      },
      "group_by": "hour"
    }
  },
  "query_info": {
    "group_by": "hour",
    "execution_time_ms": 178.3
  }
}
```

### 3. Camera Performance Analytics

Analyze individual camera metrics and performance comparisons.

**Endpoint:** `GET /api/analytics/cameras`

**Query Parameters:**
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis
- `min_confidence` (optional): Minimum confidence threshold

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/cameras?min_confidence=0.8&start_date=2025-08-01T00:00:00"
```

**Response:**

```json
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
          },
          "hourly_distribution": {
            "8": 245,
            "9": 387,
            "14": 456,
            "15": 423
          }
        }
      },
      "cam_exit": {
        "camera_info": {
          "name": "Exit Gate",
          "location": "Building A"
        },
        "metrics": {
          "total_detections": 6923,
          "unique_plates": 1876,
          "average_confidence": 0.823,
          "confidence_range": {
            "min": 0.567,
            "max": 0.976
          },
          "peak_hour": 17,
          "vehicle_types": {
            "car": 5234,
            "truck": 1145,
            "motorcycle": 544
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
      ],
      "most_unique_plates": [
        ["cam_entrance", 2156],
        ["cam_exit", 1876]
      ]
    },
    "summary": {
      "total_cameras_analyzed": 2,
      "total_cameras_configured": 3
    }
  },
  "query_info": {
    "execution_time_ms": 312.6
  }
}
```

### 4. License Plate Analytics

Analyze plate patterns, frequencies, and visitor tracking.

**Endpoint:** `GET /api/analytics/plates`

**Query Parameters:**
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis
- `camera_ids` (optional): Camera IDs to analyze
- `min_confidence` (optional): Minimum confidence threshold

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/plates?start_date=2025-08-01T00:00:00&end_date=2025-08-12T23:59:59"
```

**Response:**

```json
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
      ["DEF9012", 15],
      ["GHI3456", 12],
      ["JKL7890", 11]
    ],
    "multi_camera_plates": [
      ["ABC1234", 3],
      ["XYZ5678", 2],
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
      },
      "XYZ5678": {
        "visits": 18,
        "duration_minutes": 892.3,
        "cameras": 2,
        "average_confidence": 0.823,
        "first_seen": "2025-08-02T09:15:42",
        "last_seen": "2025-08-11T17:22:18"
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
        "7": 2007,
        "8": 0
      },
      "most_common_length": 7
    }
  },
  "query_info": {
    "execution_time_ms": 445.2
  }
}
```

### 5. System Performance Analytics

Analyze system performance metrics and processing efficiency.

**Endpoint:** `GET /api/analytics/performance`

**Query Parameters:**
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/performance?start_date=2025-08-12T00:00:00"
```

**Response:**

```json
{
  "success": true,
  "data": {
    "system_performance": {
      "detection_rate_per_hour": 35.3,
      "confidence_statistics": {
        "mean": 0.847,
        "min": 0.234,
        "max": 0.987,
        "high_confidence_count": 678,
        "low_confidence_count": 23
      },
      "peak_detection_hour": 14,
      "hourly_distribution": {
        "8": 145,
        "9": 267,
        "14": 445,
        "15": 389,
        "17": 423
      },
      "performance_score": 84.7
    },
    "analysis_period": {
      "start": "2025-08-12T00:00:00",
      "end": "2025-08-12T23:59:59"
    }
  },
  "query_info": {
    "execution_time_ms": 123.8
  }
}
```

## Comprehensive Reporting

### 6. Generate Comprehensive Report

Get a complete analytics report combining all analysis types.

**Endpoint:** `GET /api/analytics/comprehensive-report`

**Query Parameters:**
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis
- `camera_ids` (optional): Camera IDs to analyze
- `min_confidence` (optional): Minimum confidence threshold

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/comprehensive-report?start_date=2025-08-01T00:00:00&end_date=2025-08-12T23:59:59" \
  -o comprehensive_report.json
```

**Response Structure:**

```json
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
      "frequent_plates": [ /* frequent plates */ ],
      "visit_analysis": { /* visit data */ }
    },
    "system_performance": {
      "system_performance": { /* performance metrics */ }
    }
  },
  "metadata": {
    "generated_at": "2025-08-12T14:30:52",
    "query": {
      "start_date": "2025-08-01T00:00:00",
      "end_date": "2025-08-12T23:59:59",
      "camera_ids": null,
      "min_confidence": null
    },
    "execution_time_ms": 1247.3,
    "sections": [
      "overview",
      "temporal_trends", 
      "camera_performance",
      "plate_analytics",
      "system_performance"
    ],
    "generated_by": "admin"
  }
}
```

## Dashboard Data

### 7. Real-time Dashboard Data

Get optimized data for dashboard displays with live updates.

**Endpoint:** `GET /api/analytics/dashboard`

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/dashboard"
```

**Response:**

```json
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

## Data Export

### 8. CSV Data Export

Export analytics data in CSV format for external analysis.

**Endpoint:** `GET /api/analytics/export/csv`

**Query Parameters:**
- `start_date` (optional): Start date for export
- `end_date` (optional): End date for export
- `camera_ids` (optional): Camera IDs to export
- `min_confidence` (optional): Minimum confidence threshold
- `export_type` (required): Export type - `detections`, `summary`, or `cameras`

**Example Requests:**

```bash
# Export raw detection data
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/export/csv?export_type=detections&start_date=2025-08-01T00:00:00" \
  -o detections_export.csv

# Export summary analytics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/export/csv?export_type=summary&start_date=2025-08-01T00:00:00" \
  -o summary_export.csv

# Export camera performance data
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/export/csv?export_type=cameras" \
  -o cameras_export.csv
```

**CSV Output Examples:**

**Detections Export:**
```csv
Detection ID,Camera ID,Plate Text,Vehicle Type,Confidence,Detected At,Vehicle BBox,Plate BBox
det_001,cam_entrance,ABC1234,car,0.871,2025-08-01T08:23:15,"[100,200,300,400]","[150,220,200,250]"
det_002,cam_exit,XYZ5678,truck,0.823,2025-08-01T08:24:23,"[50,150,350,450]","[120,180,180,210]"
```

**Summary Export:**
```csv
Metric,Value
Total Detections,15847
Unique Plates,3241
Average Confidence,0.847
Detections Per Hour,28.4
```

## Visualization

### 9. Chart Generation

Generate server-side charts as PNG images.

**Endpoint:** `GET /api/analytics/charts/{chart_type}`

**Path Parameters:**
- `chart_type`: Chart type - `trends`, `cameras`, or `confidence`

**Query Parameters:**
- `start_date` (optional): Start date for chart data
- `end_date` (optional): End date for chart data
- `camera_ids` (optional): Camera IDs for chart
- `width` (optional): Chart width in pixels (default: 800)
- `height` (optional): Chart height in pixels (default: 600)

**Example Requests:**

```bash
# Generate trends chart
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/charts/trends?width=1200&height=800&start_date=2025-08-01T00:00:00" \
  -o trends_chart.png

# Generate camera performance chart
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/charts/cameras?width=800&height=600" \
  -o cameras_chart.png

# Generate confidence distribution chart
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/charts/confidence?width=600&height=400" \
  -o confidence_chart.png
```

**Response:** PNG image data with headers:
```
Content-Type: image/png
Content-Disposition: inline; filename=lpr_chart_trends_20250812_143052.png
```

## Automated Insights

### 10. Get Automated Insights

Receive AI-powered insights and recommendations based on system analysis.

**Endpoint:** `GET /api/analytics/insights`

**Query Parameters:**
- `start_date` (optional): Start date for analysis (default: 7 days ago)
- `end_date` (optional): End date for analysis (default: now)

**Example Request:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/analytics/insights?start_date=2025-08-05T00:00:00&end_date=2025-08-12T23:59:59"
```

**Response:**

```json
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
      "type": "quality",
      "severity": "warning",
      "title": "Low Average Confidence",
      "description": "Average detection confidence is 0.65",
      "recommendation": "Review camera positioning and lighting conditions"
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
  },
  "generated_at": "2025-08-12T14:30:52"
}
```

**Insight Types:**
- `volume`: Detection volume analysis
- `camera`: Camera performance issues
- `quality`: Confidence score issues
- `activity`: Unusual activity patterns
- `system`: System performance issues

**Severity Levels:**
- `info`: Informational insights
- `warning`: Issues requiring attention
- `critical`: Critical issues requiring immediate action

## Custom Reports

### 11. Generate Custom Reports

Request custom report generation with flexible configuration.

**Endpoint:** `POST /api/analytics/reports/generate`

**Request Body:**
```json
{
  "template": "weekly_analytics",
  "date_range": {
    "start": "2025-08-01T00:00:00",
    "end": "2025-08-08T23:59:59"
  },
  "sections": ["overview", "trends", "cameras", "plates"],
  "format": "pdf",
  "options": {
    "include_charts": true,
    "min_confidence": 0.7
  }
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8001/api/analytics/reports/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "weekly_analytics",
    "date_range": {
      "start": "2025-08-01T00:00:00",
      "end": "2025-08-08T23:59:59"
    },
    "sections": ["overview", "trends", "cameras"],
    "format": "pdf"
  }'
```

**Response:**

```json
{
  "success": true,
  "message": "Custom report generation started",
  "estimated_completion": "2-5 minutes",
  "config": {
    "template": "weekly_analytics",
    "sections": ["overview", "trends", "cameras"],
    "format": "pdf"
  }
}
```

**Available Templates:**
- `daily_summary`: Daily detection summary
- `weekly_analytics`: Comprehensive weekly report
- `monthly_executive`: Executive summary report
- `camera_health`: Camera performance report
- `data_export`: Raw data export report

## Usage Patterns

### Frontend Integration

**JavaScript Example:**

```javascript
class AnalyticsAPI {
  constructor(baseUrl, authToken) {
    this.baseUrl = baseUrl;
    this.authToken = authToken;
  }

  async getOverview(params = {}) {
    const url = new URL(`${this.baseUrl}/api/analytics/overview`);
    Object.keys(params).forEach(key => {
      if (params[key]) url.searchParams.append(key, params[key]);
    });

    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${this.authToken}` }
    });

    return response.json();
  }

  async getDashboardData() {
    const response = await fetch(`${this.baseUrl}/api/analytics/dashboard`, {
      headers: { 'Authorization': `Bearer ${this.authToken}` }
    });

    return response.json();
  }

  async exportCSV(exportType, params = {}) {
    const url = new URL(`${this.baseUrl}/api/analytics/export/csv`);
    url.searchParams.append('export_type', exportType);
    Object.keys(params).forEach(key => {
      if (params[key]) url.searchParams.append(key, params[key]);
    });

    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${this.authToken}` }
    });

    return response.blob();
  }
}

// Usage
const analytics = new AnalyticsAPI('http://localhost:8001', authToken);

// Load dashboard
analytics.getDashboardData().then(data => {
  if (data.success) {
    updateDashboard(data.dashboard);
  }
});

// Export data
analytics.exportCSV('detections', {
  start_date: '2025-08-01T00:00:00',
  end_date: '2025-08-12T23:59:59'
}).then(blob => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'detections.csv';
  a.click();
});
```

### Python Integration

```python
import requests
from datetime import datetime, timedelta

class LPRAnalytics:
    def __init__(self, base_url, auth_token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {auth_token}'}
    
    def get_overview(self, start_date=None, end_date=None, **kwargs):
        params = {k: v for k, v in kwargs.items() if v is not None}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        
        response = requests.get(
            f"{self.base_url}/api/analytics/overview",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def get_comprehensive_report(self, **kwargs):
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        response = requests.get(
            f"{self.base_url}/api/analytics/comprehensive-report",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def export_csv(self, export_type, filename=None, **kwargs):
        params = {'export_type': export_type}
        params.update({k: v for k, v in kwargs.items() if v is not None})
        
        response = requests.get(
            f"{self.base_url}/api/analytics/export/csv",
            headers=self.headers,
            params=params
        )
        
        if filename:
            with open(filename, 'wb') as f:
                f.write(response.content)
        
        return response.content

# Usage example
analytics = LPRAnalytics('http://localhost:8001', auth_token)

# Get last week's overview
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
overview = analytics.get_overview(start_date=start_date, end_date=end_date)

print(f"Total detections: {overview['data']['summary']['total_detections']}")

# Export detection data
analytics.export_csv('detections', 'detections_export.csv', 
                    start_date=start_date.isoformat(),
                    min_confidence=0.8)
```

## Error Handling

### Common HTTP Status Codes

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid or missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found (invalid endpoint)
- `500`: Internal Server Error

### Error Response Format

```json
{
  "success": false,
  "error": "Error description",
  "details": {
    "code": "INVALID_DATE_RANGE",
    "message": "Start date must be before end date"
  }
}
```

### Handling Errors

```javascript
async function safeApiCall(apiFunction) {
  try {
    const response = await apiFunction();
    
    if (!response.success) {
      throw new Error(response.error || 'API call failed');
    }
    
    return response.data;
  } catch (error) {
    console.error('API Error:', error.message);
    
    if (error.message.includes('401')) {
      // Handle authentication error
      redirectToLogin();
    } else if (error.message.includes('403')) {
      // Handle permissions error
      showPermissionError();
    } else {
      // Handle general error
      showErrorMessage(error.message);
    }
    
    return null;
  }
}
```

## Performance Tips

### Query Optimization

1. **Use Date Ranges**: Always specify reasonable date ranges to limit data processing
2. **Filter Early**: Use `min_confidence` and `camera_ids` to reduce dataset size
3. **Batch Requests**: Use comprehensive report endpoint instead of multiple individual calls
4. **Cache Results**: Cache analytics data on frontend for repeated use

### Rate Limiting

- Maximum 100 requests per minute per user
- Comprehensive reports limited to 10 per hour
- Chart generation limited to 50 per hour
- CSV exports limited to 20 per hour

### Best Practices

```bash
# Good: Specific date range
curl -H "Authorization: Bearer $TOKEN" \
  "/api/analytics/overview?start_date=2025-08-12T00:00:00&end_date=2025-08-12T23:59:59"

# Good: High confidence only
curl -H "Authorization: Bearer $TOKEN" \
  "/api/analytics/cameras?min_confidence=0.8"

# Good: Specific cameras
curl -H "Authorization: Bearer $TOKEN" \
  "/api/analytics/trends?camera_ids=cam_entrance,cam_exit"

# Avoid: No date limits (processes all data)
curl -H "Authorization: Bearer $TOKEN" \
  "/api/analytics/overview"
```

## Integration Examples

### Grafana Data Source

Configure Grafana to use analytics API as data source:

```json
{
  "name": "LPR Analytics",
  "type": "json-api",
  "url": "http://localhost:8001/api/analytics",
  "httpHeaderName1": "Authorization",
  "httpHeaderValue1": "Bearer YOUR_TOKEN_HERE"
}
```

### Slack Integration

Send daily reports to Slack:

```python
import requests
from datetime import datetime, timedelta

def send_daily_report():
    # Get yesterday's analytics
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=1)
    
    overview = analytics.get_overview(start_date=start_date, end_date=end_date)
    
    if overview['success']:
        summary = overview['data']['summary']
        
        slack_message = {
            "text": "📊 Daily LPR Analytics Report",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"""
*Daily Analytics Summary*
• Total Detections: {summary['total_detections']}
• Unique Plates: {summary['unique_plates']}  
• Average Confidence: {summary['average_confidence']:.3f}
• Detection Rate: {summary['detections_per_hour']:.1f}/hour
                        """
                    }
                }
            ]
        }
        
        requests.post(SLACK_WEBHOOK_URL, json=slack_message)
```

This comprehensive API guide provides everything needed to integrate with the LPR Analytics system, from basic queries to advanced reporting and visualization.