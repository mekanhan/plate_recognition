# Universal Detection Results Page - Architecture & Implementation

## 1. Database Schema Updates

First, let's extend your existing models to support universal object detection:

```python
# database/models.py - Add to existing models

class ObjectType(Base):
    """Define all detectable object types"""
    __tablename__ = 'object_types'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type_code = Column(String(50), unique=True, nullable=False)  # 'vehicle', 'person', 'package', etc.
    display_name = Column(String(100), nullable=False)
    icon = Column(String(50))  # FontAwesome or custom icon class
    color = Column(String(7))  # Hex color for UI
    priority = Column(Integer, default=0)  # Display ordering
    active = Column(Boolean, default=True)
    metadata_schema = Column(JSON)  # Expected metadata fields
    created_at = Column(DateTime, default=datetime.utcnow)

class UniversalDetection(Base):
    """Universal detection model replacing the vehicle-specific Detection"""
    __tablename__ = 'universal_detections'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(50), nullable=False)
    object_type = Column(String(50), ForeignKey('object_types.type_code'))
    
    # Core detection data
    confidence = Column(Float, nullable=False)
    detected_at = Column(DateTime, nullable=False)
    bbox = Column(JSON)  # {"x": 120, "y": 45, "width": 150, "height": 80}
    
    # Media storage
    frame_path = Column(String(500))
    object_image_path = Column(String(500))
    video_clip_id = Column(String(36))
    video_thumbnail_path = Column(String(500))  # For card view
    
    # Flexible metadata for any object type
    metadata = Column(JSON, default={})
    # Examples:
    # Vehicle: {"plate_text": "ABC123", "color": "blue", "make": "Toyota", "model": "Camry"}
    # Person: {"age_range": "25-35", "gender": "male", "clothing": "blue shirt"}
    # Package: {"size": "medium", "label_visible": true, "carrier": "FedEx"}
    
    # Status and workflow
    status = Column(String(20), default='unverified')  # unverified, verified, flagged, archived
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    tags = Column(JSON, default=[])
    
    # Performance metrics
    processing_time_ms = Column(Integer)
    model_version = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## 2. Backend API Enhancements

```python
# api/detection_endpoints.py

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v2/detections")

class DetectionFilter(BaseModel):
    """Advanced filtering options"""
    object_types: Optional[List[str]] = None
    cameras: Optional[List[str]] = None
    confidence_min: Optional[float] = None
    confidence_max: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata_filters: Optional[Dict] = None  # Dynamic filters based on object type

class SmartSearchQuery(BaseModel):
    """Natural language search processing"""
    query: str
    include_metadata: bool = True
    fuzzy_match: bool = True

@router.post("/search")
async def universal_search(
    filters: Optional[DetectionFilter] = None,
    smart_search: Optional[str] = None,
    view_mode: str = Query("list", regex="^(list|card|timeline|map)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=10, le=200),
    sort_by: str = Query("detected_at", regex="^(detected_at|confidence|object_type)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """
    Universal detection search with multiple view modes
    """
    # Parse smart search if provided
    if smart_search:
        search_filters = await parse_smart_search(smart_search)
        filters = merge_filters(filters, search_filters)
    
    # Apply filters and pagination
    detections = await db.search_detections(
        filters=filters,
        offset=(page - 1) * limit,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Format based on view mode
    if view_mode == "card":
        results = format_card_view(detections)
    elif view_mode == "timeline":
        results = format_timeline_view(detections)
    elif view_mode == "map":
        results = format_map_view(detections)
    else:
        results = format_list_view(detections)
    
    return {
        "results": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": await db.count_detections(filters),
            "pages": (await db.count_detections(filters) + limit - 1) // limit
        },
        "filters_applied": filters,
        "view_mode": view_mode
    }

@router.get("/statistics")
async def detection_statistics(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d|custom)$"),
    group_by: str = Query("object_type", regex="^(object_type|camera|hour|day)$")
):
    """Get detection statistics for dashboard widgets"""
    stats = await db.get_detection_statistics(time_range, group_by)
    return stats

@router.get("/export")
async def export_detections(
    format: str = Query("csv", regex="^(csv|json|pdf)$"),
    filters: Optional[DetectionFilter] = None
):
    """Export filtered detections"""
    # Implementation for data export
    pass
```

## 3. Frontend Implementation

### 3.1 Enhanced DetectionsPage Component

```javascript
// frontend/src/pages/DetectionsPage.js

class UniversalDetectionsPage {
    constructor() {
        this.viewMode = localStorage.getItem('detectionViewMode') || 'list';
        this.detections = [];
        this.filters = {
            search: '',
            objectTypes: [],
            cameras: [],
            dateRange: 'today',
            customDateFrom: null,
            customDateTo: null,
            confidence: { min: 0, max: 100 },
            status: [],
            tags: []
        };
        this.advancedSearchMode = false;
        this.selectedDetections = new Set();
        this.pagination = {
            page: 1,
            limit: 50,
            total: 0
        };
        
        this.init();
    }
    
    getTemplate() {
        return `
            <div class="detections-page">
                <!-- Page Header -->
                <div class="page-header">
                    <div class="page-title-section">
                        <h1 class="page-title">Detection Results</h1>
                        <p class="page-subtitle">Universal object detection monitoring and analysis</p>
                    </div>
                    <div class="page-actions">
                        <button class="btn btn-primary" onclick="detectionsPage.exportData()">
                            <i class="fas fa-download"></i> Export
                        </button>
                        <button class="btn btn-secondary" onclick="detectionsPage.showAnalytics()">
                            <i class="fas fa-chart-line"></i> Analytics
                        </button>
                    </div>
                </div>
                
                <!-- Search and Filter Section -->
                <div class="search-filter-section">
                    <!-- Smart Search Bar -->
                    <div class="smart-search-container">
                        <div class="smart-search-wrapper">
                            <i class="fas fa-search search-icon"></i>
                            <input type="text" 
                                   id="smart-search" 
                                   class="smart-search-input" 
                                   placeholder="Search by object type, location, time, or any attribute..."
                                   value="${this.filters.search}">
                            <button class="search-mode-toggle" 
                                    onclick="detectionsPage.toggleSearchMode()"
                                    title="${this.advancedSearchMode ? 'Switch to Basic' : 'Switch to Advanced'}">
                                <i class="fas fa-${this.advancedSearchMode ? 'toggle-on' : 'toggle-off'}"></i>
                                ${this.advancedSearchMode ? 'Advanced' : 'Basic'}
                            </button>
                        </div>
                        
                        <!-- Search Suggestions -->
                        <div class="search-suggestions" id="search-suggestions" style="display: none;">
                            <div class="suggestion-category">
                                <span class="category-label">Recent:</span>
                                <span class="suggestion" onclick="detectionsPage.applySuggestion('vehicles in last hour')">vehicles in last hour</span>
                                <span class="suggestion" onclick="detectionsPage.applySuggestion('high confidence detections')">high confidence detections</span>
                            </div>
                            <div class="suggestion-category">
                                <span class="category-label">Try:</span>
                                <span class="suggestion" onclick="detectionsPage.applySuggestion('red cars at entrance')">red cars at entrance</span>
                                <span class="suggestion" onclick="detectionsPage.applySuggestion('packages today')">packages today</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Advanced Filters (Collapsible) -->
                    <div class="advanced-filters ${this.advancedSearchMode ? 'expanded' : 'collapsed'}" id="advanced-filters">
                        <div class="filter-row">
                            <!-- Object Type Filter -->
                            <div class="filter-group">
                                <label>Object Type</label>
                                <div class="multi-select-wrapper">
                                    <div class="selected-items" id="selected-object-types">
                                        ${this.filters.objectTypes.length ? 
                                            this.filters.objectTypes.map(type => `
                                                <span class="selected-tag">
                                                    ${type}
                                                    <i class="fas fa-times" onclick="detectionsPage.removeFilter('objectTypes', '${type}')"></i>
                                                </span>
                                            `).join('') : 
                                            '<span class="placeholder">All types</span>'
                                        }
                                    </div>
                                    <button class="dropdown-toggle" onclick="detectionsPage.toggleDropdown('object-types')">
                                        <i class="fas fa-chevron-down"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Camera Filter -->
                            <div class="filter-group">
                                <label>Camera</label>
                                <select multiple class="filter-select" id="camera-filter">
                                    <option value="">All Cameras</option>
                                    <!-- Dynamically populated -->
                                </select>
                            </div>
                            
                            <!-- Date Range -->
                            <div class="filter-group">
                                <label>Time Range</label>
                                <select class="filter-select" id="date-range-filter" 
                                        onchange="detectionsPage.handleDateRangeChange(this.value)">
                                    <option value="today">Today</option>
                                    <option value="yesterday">Yesterday</option>
                                    <option value="week">Last 7 Days</option>
                                    <option value="month">Last 30 Days</option>
                                    <option value="custom">Custom Range</option>
                                </select>
                                <div class="custom-date-range" id="custom-date-range" style="display: none;">
                                    <input type="datetime-local" id="date-from" class="date-input">
                                    <span>to</span>
                                    <input type="datetime-local" id="date-to" class="date-input">
                                </div>
                            </div>
                            
                            <!-- Confidence Range -->
                            <div class="filter-group">
                                <label>Confidence</label>
                                <div class="range-slider-container">
                                    <input type="range" min="0" max="100" value="${this.filters.confidence.min}" 
                                           class="range-slider" id="confidence-min">
                                    <input type="range" min="0" max="100" value="${this.filters.confidence.max}" 
                                           class="range-slider" id="confidence-max">
                                    <div class="range-values">
                                        <span id="confidence-min-value">${this.filters.confidence.min}%</span>
                                        <span id="confidence-max-value">${this.filters.confidence.max}%</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Status Filter -->
                            <div class="filter-group">
                                <label>Status</label>
                                <div class="checkbox-group">
                                    <label class="checkbox-label">
                                        <input type="checkbox" value="unverified"> Unverified
                                    </label>
                                    <label class="checkbox-label">
                                        <input type="checkbox" value="verified"> Verified
                                    </label>
                                    <label class="checkbox-label">
                                        <input type="checkbox" value="flagged"> Flagged
                                    </label>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Filter Actions -->
                        <div class="filter-actions">
                            <button class="btn btn-secondary btn-small" onclick="detectionsPage.resetFilters()">
                                <i class="fas fa-undo"></i> Reset
                            </button>
                            <button class="btn btn-primary btn-small" onclick="detectionsPage.applyFilters()">
                                <i class="fas fa-filter"></i> Apply Filters
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- View Mode Toggle -->
                <div class="view-controls">
                    <div class="view-mode-toggle">
                        <button class="view-mode-btn ${this.viewMode === 'list' ? 'active' : ''}" 
                                onclick="detectionsPage.setViewMode('list')"
                                title="List View">
                            <i class="fas fa-list"></i>
                        </button>
                        <button class="view-mode-btn ${this.viewMode === 'card' ? 'active' : ''}" 
                                onclick="detectionsPage.setViewMode('card')"
                                title="Card View">
                            <i class="fas fa-th-large"></i>
                        </button>
                        <button class="view-mode-btn ${this.viewMode === 'timeline' ? 'active' : ''}" 
                                onclick="detectionsPage.setViewMode('timeline')"
                                title="Timeline View">
                            <i class="fas fa-stream"></i>
                        </button>
                        <button class="view-mode-btn ${this.viewMode === 'map' ? 'active' : ''}" 
                                onclick="detectionsPage.setViewMode('map')"
                                title="Map View">
                            <i class="fas fa-map"></i>
                        </button>
                    </div>
                    
                    <div class="results-info">
                        <span class="result-count">${this.pagination.total} results</span>
                        <select class="per-page-select" onchange="detectionsPage.setPageLimit(this.value)">
                            <option value="25">25 per page</option>
                            <option value="50" selected>50 per page</option>
                            <option value="100">100 per page</option>
                            <option value="200">200 per page</option>
                        </select>
                    </div>
                </div>
                
                <!-- Results Container -->
                <div class="detection-results-container">
                    ${this.renderViewMode()}
                </div>
                
                <!-- Pagination -->
                <div class="pagination-container">
                    ${this.renderPagination()}
                </div>
            </div>
        `;
    }
    
    renderViewMode() {
        switch(this.viewMode) {
            case 'card':
                return this.renderCardView();
            case 'timeline':
                return this.renderTimelineView();
            case 'map':
                return this.renderMapView();
            default:
                return this.renderListView();
        }
    }
    
    renderCardView() {
        return `
            <div class="detection-cards-grid">
                ${this.detections.map(detection => `
                    <div class="detection-card ${detection.status}" data-detection-id="${detection.id}">
                        <!-- Video Thumbnail with Preview -->
                        <div class="card-media">
                            <img src="${detection.video_thumbnail_path || detection.frame_path}" 
                                 alt="Detection thumbnail" 
                                 class="card-thumbnail">
                            ${detection.video_clip_id ? `
                                <div class="video-overlay" onclick="detectionsPage.playVideoPreview('${detection.id}')">
                                    <i class="fas fa-play-circle"></i>
                                </div>
                                <video class="video-preview" id="preview-${detection.id}" style="display: none;">
                                    <source src="/api/v2/detections/${detection.id}/video" type="video/mp4">
                                </video>
                            ` : ''}
                            <span class="detection-type-badge ${detection.object_type}">
                                <i class="${this.getObjectIcon(detection.object_type)}"></i>
                                ${detection.object_type}
                            </span>
                        </div>
                        
                        <!-- Card Content -->
                        <div class="card-content">
                            <div class="card-header">
                                <h4 class="card-title">${this.getDetectionTitle(detection)}</h4>
                                <span class="confidence-indicator ${this.getConfidenceClass(detection.confidence)}">
                                    ${detection.confidence.toFixed(1)}%
                                </span>
                            </div>
                            
                            <div class="card-details">
                                <div class="detail-row">
                                    <i class="fas fa-camera"></i>
                                    <span>${detection.camera_name}</span>
                                </div>
                                <div class="detail-row">
                                    <i class="fas fa-clock"></i>
                                    <span>${this.formatRelativeTime(detection.detected_at)}</span>
                                </div>
                                ${this.renderObjectSpecificDetails(detection)}
                            </div>
                            
                            <!-- Quick Actions -->
                            <div class="card-actions">
                                <button class="action-btn" onclick="detectionsPage.viewDetails('${detection.id}')" title="View Details">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="action-btn" onclick="detectionsPage.toggleFlag('${detection.id}')" 
                                        title="${detection.flagged ? 'Unflag' : 'Flag'}"
                                        class="${detection.flagged ? 'flagged' : ''}">
                                    <i class="fas fa-flag"></i>
                                </button>
                                <button class="action-btn" onclick="detectionsPage.downloadDetection('${detection.id}')" title="Download">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="action-btn" onclick="detectionsPage.shareDetection('${detection.id}')" title="Share">
                                    <i class="fas fa-share"></i>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Selection Overlay -->
                        <div class="card-selection">
                            <input type="checkbox" 
                                   class="card-checkbox" 
                                   ${this.selectedDetections.has(detection.id) ? 'checked' : ''}
                                   onchange="detectionsPage.toggleSelection('${detection.id}')">
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderListView() {
        return `
            <div class="detection-table-wrapper">
                <table class="detection-table">
                    <thead>
                        <tr>
                            <th class="checkbox-column">
                                <input type="checkbox" id="select-all" 
                                       onchange="detectionsPage.toggleSelectAll(this.checked)">
                            </th>
                            <th class="sortable" data-sort="detected_at" onclick="detectionsPage.sort('detected_at')">
                                Time <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="object_type" onclick="detectionsPage.sort('object_type')">
                                Type <i class="fas fa-sort"></i>
                            </th>
                            <th>Details</th>
                            <th class="sortable" data-sort="camera_name" onclick="detectionsPage.sort('camera_name')">
                                Camera <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="confidence" onclick="detectionsPage.sort('confidence')">
                                Confidence <i class="fas fa-sort"></i>
                            </th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.detections.map(detection => `
                            <tr class="detection-row ${detection.status}" data-detection-id="${detection.id}">
                                <td class="checkbox-column">
                                    <input type="checkbox" 
                                           ${this.selectedDetections.has(detection.id) ? 'checked' : ''}
                                           onchange="detectionsPage.toggleSelection('${detection.id}')">
                                </td>
                                <td class="time-column">
                                    <div class="time-display">
                                        <span class="relative-time">${this.formatRelativeTime(detection.detected_at)}</span>
                                        <span class="absolute-time">${this.formatDateTime(detection.detected_at)}</span>
                                    </div>
                                </td>
                                <td class="type-column">
                                    <span class="type-badge ${detection.object_type}">
                                        <i class="${this.getObjectIcon(detection.object_type)}"></i>
                                        ${detection.object_type}
                                    </span>
                                </td>
                                <td class="details-column">
                                    ${this.renderListDetails(detection)}
                                </td>
                                <td class="camera-column">${detection.camera_name}</td>
                                <td class="confidence-column">
                                    <div class="confidence-bar">
                                        <div class="confidence-fill ${this.getConfidenceClass(detection.confidence)}" 
                                             style="width: ${detection.confidence}%"></div>
                                        <span class="confidence-text">${detection.confidence.toFixed(1)}%</span>
                                    </div>
                                </td>
                                <td class="status-column">
                                    <span class="status-badge ${detection.status}">
                                        ${detection.status}
                                    </span>
                                </td>
                                <td class="actions-column">
                                    <div class="action-buttons">
                                        <button class="action-btn" onclick="detectionsPage.viewDetails('${detection.id}')" title="View">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button class="action-btn" onclick="detectionsPage.downloadDetection('${detection.id}')" title="Download">
                                            <i class="fas fa-download"></i>
                                        </button>
                                        <div class="more-actions">
                                            <button class="action-btn" onclick="detectionsPage.showMoreActions('${detection.id}')">
                                                <i class="fas fa-ellipsis-v"></i>
                                            </button>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Helper methods for rendering object-specific details
    renderObjectSpecificDetails(detection) {
        const metadata = detection.metadata || {};
        
        switch(detection.object_type) {
            case 'vehicle':
                return `
                    ${metadata.plate_text ? `
                        <div class="detail-row highlight">
                            <i class="fas fa-id-card"></i>
                            <span class="plate-number">${metadata.plate_text}</span>
                        </div>
                    ` : ''}
                    ${metadata.color || metadata.make ? `
                        <div class="detail-row">
                            <i class="fas fa-car"></i>
                            <span>${[metadata.color, metadata.make, metadata.model].filter(Boolean).join(' ')}</span>
                        </div>
                    ` : ''}
                `;
                
            case 'person':
                return `
                    ${metadata.age_range ? `
                        <div class="detail-row">
                            <i class="fas fa-user"></i>
                            <span>Age: ${metadata.age_range}</span>
                        </div>
                    ` : ''}
                    ${metadata.clothing ? `
                        <div class="detail-row">
                            <i class="fas fa-tshirt"></i>
                            <span>${metadata.clothing}</span>
                        </div>
                    ` : ''}
                `;
                
            case 'package':
                return `
                    ${metadata.size ? `
                        <div class="detail-row">
                            <i class="fas fa-box"></i>
                            <span>Size: ${metadata.size}</span>
                        </div>
                    ` : ''}
                    ${metadata.carrier ? `
                        <div class="detail-row">
                            <i class="fas fa-truck"></i>
                            <span>${metadata.carrier}</span>
                        </div>
                    ` : ''}
                `;
                
            default:
                return Object.entries(metadata).slice(0, 2).map(([key, value]) => `
                    <div class="detail-row">
                        <i class="fas fa-info-circle"></i>
                        <span>${key}: ${value}</span>
                    </div>
                `).join('');
        }
    }
    
    // Video preview functionality
    playVideoPreview(detectionId) {
        const video = document.getElementById(`preview-${detectionId}`);
        const thumbnail = video.previousElementSibling.previousElementSibling;
        
        if (video.style.display === 'none') {
            // Show video
            thumbnail.style.display = 'none';
            video.style.display = 'block';
            video.play();
            
            // Auto-hide after preview
            video.addEventListener('ended', () => {
                video.style.display = 'none';
                thumbnail.style.display = 'block';
            });
        } else {
            // Hide video
            video.pause();
            video.style.display = 'none';
            thumbnail.style.display = 'block';
        }
    }
}
```

### 3.2 CSS Styling for Modern UI

```css
/* frontend/src/styles/detections.css */

.detections-page {
    padding: 24px;
    background-color: var(--bg-primary);
}

/* Smart Search Styling */
.smart-search-container {
    position: relative;
    margin-bottom: 24px;
}

.smart-search-wrapper {
    display: flex;
    align-items: center;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 12px 20px;
    transition: all 0.3s ease;
}

.smart-search-wrapper:focus-within {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

.smart-search-input {
    flex: 1;
    border: none;
    background: none;
    font-size: 16px;
    padding: 0 12px;
    outline: none;
}

.search-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    margin-top: 8px;
    padding: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 100;
}

/* View Mode Toggle */
.view-mode-toggle {
    display: flex;
    gap: 4px;
    background: var(--bg-secondary);
    padding: 4px;
    border-radius: 8px;
}

.view-mode-btn {
    padding: 8px 12px;
    border: none;
    background: transparent;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.view-mode-btn.active {
    background: var(--primary-color);
    color: white;
}

/* Card View Styling */
.detection-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
    padding: 20px 0;
}

.detection-card {
    background: var(--bg-secondary);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    position: relative;
}

.detection-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-media {
    position: relative;
    padding-top: 56.25%; /* 16:9 aspect ratio */
    overflow: hidden;
    background: #000;
}

.card-thumbnail {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.video-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.3);
    opacity: 0;
    transition: opacity 0.3s ease;
    cursor: pointer;
}

.detection-card:hover .video-overlay {
    opacity: 1;
}

.video-overlay i {
    font-size: 48px;
    color: white;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
}

.video-preview {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.detection-type-badge {
    position: absolute;
    top: 12px;
    left: 12px;
    padding: 6px 12px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Confidence Indicators */
.confidence-indicator {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.confidence-indicator.high {
    background: var(--success-light);
    color: var(--success-dark);
}

.confidence-indicator.medium {
    background: var(--warning-light);
    color: var(--warning-dark);
}

.confidence-indicator.low {
    background: var(--danger-light);
    color: var(--danger-dark);
}

/* Advanced Filters */
.advanced-filters {
    background: var(--bg-secondary);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    transition: all 0.3s ease;
}

.advanced-filters.collapsed {
    max-height: 0;
    padding: 0;
    overflow: hidden;
    margin: 0;
}

.filter-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 16px;
}

/* Multi-select with tags */
.multi-select-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 8px;
    min-height: 40px;
}

.selected-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: var(--primary-color);
    color: white;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 4px;
}

.selected-tag i {
    cursor: pointer;
    opacity: 0.8;
}

.selected-tag i:hover {
    opacity: 1;
}

/* Responsive Design */
@media (max-width: 768px) {
    .detection-cards-grid {
        grid-template-columns: 1fr;
    }
    
    .filter-row {
        grid-template-columns: 1fr;
    }
    
    .view-controls {
        flex-direction: column;
        gap: 12px;
    }
    
    .detection-table-wrapper {
        overflow-x: auto;
    }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #1a1a1a;
        --bg-secondary: #2a2a2a;
        --text-primary: #ffffff;
        --text-secondary: #b0b0b0;
        --border-color: #3a3a3a;
    }
}
```

## 4. Smart Search Implementation

```javascript
// frontend/src/services/smartSearch.js

class SmartSearchParser {
    constructor() {
        this.patterns = {
            objectType: /\b(vehicle|car|truck|person|people|package|box)\b/gi,
            color: /\b(red|blue|green|white|black|silver|gray|yellow)\b/gi,
            location: /\b(entrance|exit|parking|loading|dock|gate)\b/gi,
            time: /\b(today|yesterday|hour|hours|minute|minutes|week|month)\b/gi,
            confidence: /\b(high|low|medium|confident|uncertain)\b/gi,
            plate: /\b([A-Z0-9]{2,8})\b/g,
            attributes: {
                vehicle: /\b(sedan|suv|truck|van|motorcycle)\b/gi,
                person: /\b(male|female|adult|child|uniform)\b/gi,
                package: /\b(small|medium|large|fedex|ups|amazon)\b/gi
            }
        };
    }
    
    parse(query) {
        const filters = {
            objectTypes: [],
            metadata: {},
            timeRange: null,
            confidence: null,
            cameras: [],
            freeText: []
        };
        
        // Extract object types
        const typeMatches = query.match(this.patterns.objectType);
        if (typeMatches) {
            filters.objectTypes = [...new Set(typeMatches.map(t => this.normalizeObjectType(t)))];
        }
        
        // Extract colors
        const colorMatches = query.match(this.patterns.color);
        if (colorMatches) {
            filters.metadata.colors = [...new Set(colorMatches.map(c => c.toLowerCase()))];
        }
        
        // Extract time references
        const timeMatches = query.match(this.patterns.time);
        if (timeMatches) {
            filters.timeRange = this.parseTimeReference(timeMatches[0]);
        }
        
        // Extract confidence levels
        const confidenceMatches = query.match(this.patterns.confidence);
        if (confidenceMatches) {
            filters.confidence = this.parseConfidenceLevel(confidenceMatches[0]);
        }
        
        // Extract license plate patterns
        const plateMatches = query.match(this.patterns.plate);
        if (plateMatches) {
            filters.metadata.plates = plateMatches;
        }
        
        // Extract remaining text as free-form search
        let remainingQuery = query;
        Object.values(this.patterns).forEach(pattern => {
            if (pattern instanceof RegExp) {
                remainingQuery = remainingQuery.replace(pattern, '');
            }
        });
        
        const freeText = remainingQuery.trim();
        if (freeText) {
            filters.freeText = freeText.split(/\s+/).filter(t => t.length > 2);
        }
        
        return filters;
    }
    
    normalizeObjectType(type) {
        const typeMap = {
            'car': 'vehicle',
            'truck': 'vehicle',
            'people': 'person',
            'box': 'package'
        };
        return typeMap[type.toLowerCase()] || type.toLowerCase();
    }
    
    parseTimeReference(timeStr) {
        const now = new Date();
        const timeMap = {
            'today': { from: new Date(now.setHours(0,0,0,0)), to: new Date() },
            'yesterday': { 
                from: new Date(now.setDate(now.getDate() - 1)), 
                to: new Date(now.setDate(now.getDate() + 1))
            },
            'hour': { from: new Date(now.setHours(now.getHours() - 1)), to: new Date() },
            'week': { from: new Date(now.setDate(now.getDate() - 7)), to: new Date() },
            'month': { from: new Date(now.setMonth(now.getMonth() - 1)), to: new Date() }
        };
        
        return timeMap[timeStr.toLowerCase()] || null;
    }
    
    parseConfidenceLevel(confidenceStr) {
        const confidenceMap = {
            'high': { min: 80, max: 100 },
            'medium': { min: 50, max: 80 },
            'low': { min: 0, max: 50 },
            'confident': { min: 70, max: 100 },
            'uncertain': { min: 0, max: 70 }
        };
        
        return confidenceMap[confidenceStr.toLowerCase()] || null;
    }
}
```

## 5. Real-time Updates via WebSocket

```javascript
// frontend/src/services/detectionWebSocket.js

class DetectionWebSocket {
    constructor(onDetection, onStatusUpdate) {
        this.ws = null;
        this.onDetection = onDetection;
        this.onStatusUpdate = onStatusUpdate;
        this.reconnectInterval = 5000;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        
        this.connect();
    }
    
    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:8001/ws/detections');
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.subscribeToUpdates();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.attemptReconnect();
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.attemptReconnect();
        }
    }
    
    handleMessage(data) {
        switch(data.type) {
            case 'new_detection':
                if (this.onDetection) {
                    this.onDetection(data.detection);
                }
                break;
                
            case 'status_update':
                if (this.onStatusUpdate) {
                    this.onStatusUpdate(data.status);
                }
                break;
                
            case 'statistics':
                // Update dashboard statistics
                this.updateStatistics(data.stats);
                break;
        }
    }
    
    subscribeToUpdates() {
        this.send({
            action: 'subscribe',
            filters: {
                // Subscribe based on current page filters
                objectTypes: detectionsPage.filters.objectTypes,
                cameras: detectionsPage.filters.cameras
            }
        });
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), this.reconnectInterval);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
```

## 6. Purpose & Benefits

### Universal Object Detection
- **Flexible Schema**: Supports any object type through metadata JSON field
- **Extensible**: Easy to add new object types without schema changes
- **Type-specific UI**: Renders appropriate details based on object type

### Advanced Search Capabilities
- **Natural Language**: "Show me red cars at the entrance today"
- **Smart Filters**: Combine multiple criteria intuitively
- **Real-time Suggestions**: Help users discover search capabilities

### Multiple View Modes
- **List View**: Traditional table for detailed analysis
- **Card View**: Visual grid with video previews
- **Timeline View**: Chronological event stream
- **Map View**: Spatial distribution of detections

### Performance Optimizations
- **Lazy Loading**: Load detections as needed
- **Virtual Scrolling**: Handle thousands of results smoothly
- **Efficient Caching**: Minimize API calls
- **WebSocket Updates**: Real-time without polling

### User Experience
- **Responsive Design**: Works on all devices
- **Dark Mode**: Automatic theme switching
- **Keyboard Navigation**: Full accessibility
- **Bulk Operations**: Efficient management of multiple detections

This architecture provides a solid foundation for your universal detection system while maintaining the simplicity and performance your users expect.
