# API Contracts - License Plate Recognition System

## Overview

This document defines the API contracts for the License Plate Recognition system, providing detailed specifications for request/response formats, data schemas, error codes, and validation rules. These contracts serve as the foundation for API testing and contract validation.

## Contract Validation

### Contract Testing Approach
- **Consumer-Driven Contracts**: Tests validate that API meets consumer expectations
- **Provider-Side Validation**: API implementation adheres to published contracts
- **Schema Validation**: All requests/responses conform to defined JSON schemas
- **Backward Compatibility**: API changes maintain compatibility with existing consumers

---

## 1. Detection API Contracts

### POST /api/detect/upload
**Purpose**: Upload and process image for license plate detection

#### Request Contract
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Image Upload Detection Request",
  "properties": {
    "file": {
      "type": "string",
      "format": "binary",
      "description": "Image file (JPEG, PNG, BMP, TIFF)",
      "maxLength": 52428800,
      "minLength": 1
    },
    "settings": {
      "type": "object",
      "properties": {
        "confidence_threshold": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "default": 0.7,
          "description": "Minimum confidence threshold for detections"
        },
        "save_results": {
          "type": "boolean",
          "default": true,
          "description": "Whether to save detection results to database"
        },
        "enhance_image": {
          "type": "boolean",
          "default": false,
          "description": "Whether to apply image enhancement before detection"
        },
        "return_cropped": {
          "type": "boolean",
          "default": false,
          "description": "Whether to return cropped license plate images"
        }
      },
      "additionalProperties": false
    }
  },
  "required": ["file"],
  "additionalProperties": false
}
```

#### Response Contract - Success (200)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Detection Success Response",
  "properties": {
    "success": {
      "type": "boolean",
      "const": true
    },
    "request_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
      "description": "Unique request identifier (UUID)"
    },
    "filename": {
      "type": "string",
      "description": "Original filename of uploaded image"
    },
    "file_size": {
      "type": "integer",
      "minimum": 0,
      "description": "File size in bytes"
    },
    "image_dimensions": {
      "type": "object",
      "properties": {
        "width": {"type": "integer", "minimum": 1},
        "height": {"type": "integer", "minimum": 1}
      },
      "required": ["width", "height"]
    },
    "detections": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/Detection"
      },
      "description": "Array of detected license plates"
    },
    "processing_time": {
      "type": "number",
      "minimum": 0,
      "description": "Processing time in seconds"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Processing timestamp in ISO 8601 format"
    }
  },
  "required": ["success", "request_id", "filename", "detections", "processing_time", "timestamp"],
  "additionalProperties": false,
  
  "definitions": {
    "Detection": {
      "type": "object",
      "properties": {
        "id": {
          "type": "integer",
          "description": "Unique detection ID (if saved to database)"
        },
        "license_plate": {
          "type": "string",
          "pattern": "^[A-Z0-9\\s\\-]{2,10}$",
          "description": "Detected license plate text"
        },
        "confidence": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Detection confidence score"
        },
        "bbox": {
          "type": "array",
          "items": {"type": "integer", "minimum": 0},
          "minItems": 4,
          "maxItems": 4,
          "description": "Bounding box coordinates [x1, y1, x2, y2]"
        },
        "ocr_confidence": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "OCR text recognition confidence"
        },
        "enhanced_image_path": {
          "type": ["string", "null"],
          "description": "Path to enhanced image (if enhancement was applied)"
        },
        "cropped_image": {
          "type": ["string", "null"],
          "format": "base64",
          "description": "Base64 encoded cropped license plate image (if requested)"
        },
        "plate_region": {
          "type": ["string", "null"],
          "pattern": "^[A-Z]{2}$",
          "description": "Detected plate region/state code"
        }
      },
      "required": ["license_plate", "confidence", "bbox"],
      "additionalProperties": false
    }
  }
}
```

#### Response Contract - Error (400, 413, 415, 500)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Detection Error Response",
  "properties": {
    "success": {
      "type": "boolean",
      "const": false
    },
    "error": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "enum": [
            "INVALID_FILE_FORMAT",
            "FILE_TOO_LARGE", 
            "FILE_CORRUPTED",
            "INVALID_SETTINGS",
            "PROCESSING_FAILED",
            "INTERNAL_ERROR"
          ]
        },
        "message": {
          "type": "string",
          "description": "Human-readable error message"
        },
        "details": {
          "type": ["object", "null"],
          "description": "Additional error details"
        }
      },
      "required": ["code", "message"],
      "additionalProperties": false
    },
    "request_id": {
      "type": "string",
      "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["success", "error", "timestamp"],
  "additionalProperties": false
}
```

### POST /api/detect/camera
**Purpose**: Trigger real-time detection from camera source

#### Request Contract
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Camera Detection Request",
  "properties": {
    "camera_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_-]{1,50}$",
      "description": "Camera identifier"
    },
    "duration": {
      "type": "integer",
      "minimum": 1,
      "maximum": 3600,
      "default": 10,
      "description": "Detection duration in seconds"
    },
    "settings": {
      "type": "object",
      "properties": {
        "confidence_threshold": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "default": 0.7
        },
        "save_results": {
          "type": "boolean",
          "default": true
        },
        "frame_interval": {
          "type": "integer",
          "minimum": 1,
          "maximum": 60,
          "default": 1,
          "description": "Process every Nth frame"
        }
      }
    }
  },
  "required": ["camera_id"],
  "additionalProperties": false
}
```

#### Response Contract - Success (200)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Camera Detection Response",
  "properties": {
    "success": {
      "type": "boolean",
      "const": true
    },
    "session_id": {
      "type": "string",
      "pattern": "^session_[a-f0-9]{8}$",
      "description": "Detection session identifier"
    },
    "camera_id": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["started", "processing", "completed", "failed"]
    },
    "detections": {
      "type": "array",
      "items": {
        "allOf": [
          {"$ref": "#/definitions/Detection"},
          {
            "properties": {
              "frame_number": {
                "type": "integer",
                "minimum": 0
              },
              "frame_timestamp": {
                "type": "string",
                "format": "date-time"
              }
            },
            "required": ["frame_number", "frame_timestamp"]
          }
        ]
      }
    },
    "processing_stats": {
      "type": "object",
      "properties": {
        "frames_processed": {"type": "integer", "minimum": 0},
        "total_detections": {"type": "integer", "minimum": 0},
        "average_processing_time": {"type": "number", "minimum": 0},
        "fps": {"type": "number", "minimum": 0}
      },
      "required": ["frames_processed", "total_detections"]
    }
  },
  "required": ["success", "session_id", "camera_id", "status", "detections"],
  "additionalProperties": false
}
```

---

## 2. Results API Contracts

### GET /api/results
**Purpose**: Retrieve detection results with filtering and pagination

#### Request Contract (Query Parameters)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Results Query Parameters",
  "properties": {
    "page": {
      "type": "integer",
      "minimum": 1,
      "default": 1,
      "description": "Page number for pagination"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 20,
      "description": "Number of results per page"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "description": "Filter results from this date (YYYY-MM-DD)"
    },
    "end_date": {
      "type": "string",
      "format": "date",
      "description": "Filter results until this date (YYYY-MM-DD)"
    },
    "license_plate": {
      "type": "string",
      "pattern": "^[A-Z0-9\\s\\-\\*\\?]{0,20}$",
      "description": "License plate text filter (supports wildcards)"
    },
    "camera_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_-]{1,50}$",
      "description": "Filter by camera identifier"
    },
    "confidence_min": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Minimum confidence threshold"
    },
    "confidence_max": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Maximum confidence threshold"
    },
    "sort_by": {
      "type": "string",
      "enum": ["timestamp", "confidence", "license_plate", "camera_id"],
      "default": "timestamp",
      "description": "Field to sort by"
    },
    "sort_order": {
      "type": "string",
      "enum": ["asc", "desc"],
      "default": "desc",
      "description": "Sort order"
    },
    "include_images": {
      "type": "boolean",
      "default": false,
      "description": "Whether to include image URLs in response"
    }
  },
  "additionalProperties": false
}
```

#### Response Contract - Success (200)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Results Response",
  "properties": {
    "success": {
      "type": "boolean",
      "const": true
    },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "license_plate": {"type": "string"},
          "confidence": {"type": "number"},
          "timestamp": {"type": "string", "format": "date-time"},
          "camera_id": {"type": "string"},
          "bbox": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 4,
            "maxItems": 4
          },
          "image_url": {
            "type": ["string", "null"],
            "format": "uri",
            "description": "URL to detection image (if include_images=true)"
          },
          "enhanced_image_url": {
            "type": ["string", "null"],
            "format": "uri"
          },
          "plate_region": {"type": ["string", "null"]},
          "vehicle_type": {"type": ["string", "null"]},
          "processed_status": {
            "type": "string",
            "enum": ["pending", "completed", "failed"]
          }
        },
        "required": ["id", "license_plate", "confidence", "timestamp", "camera_id", "bbox"],
        "additionalProperties": false
      }
    },
    "pagination": {
      "type": "object",
      "properties": {
        "current_page": {"type": "integer", "minimum": 1},
        "per_page": {"type": "integer", "minimum": 1},
        "total_results": {"type": "integer", "minimum": 0},
        "total_pages": {"type": "integer", "minimum": 0},
        "has_next_page": {"type": "boolean"},
        "has_previous_page": {"type": "boolean"}
      },
      "required": ["current_page", "per_page", "total_results", "total_pages", "has_next_page", "has_previous_page"],
      "additionalProperties": false
    },
    "filters_applied": {
      "type": "object",
      "description": "Summary of applied filters"
    },
    "query_time": {
      "type": "number",
      "minimum": 0,
      "description": "Query execution time in seconds"
    }
  },
  "required": ["success", "results", "pagination", "query_time"],
  "additionalProperties": false
}
```

### POST /api/results/search
**Purpose**: Advanced search with complex query capabilities

#### Request Contract
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Advanced Search Request",
  "properties": {
    "query": {
      "type": "object",
      "properties": {
        "license_plate": {
          "type": "string",
          "description": "License plate text with wildcard support"
        },
        "fuzzy_search": {
          "type": "boolean",
          "default": false,
          "description": "Enable fuzzy matching for license plate text"
        },
        "similarity_threshold": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "default": 0.8,
          "description": "Minimum similarity for fuzzy matching"
        },
        "confidence_range": {
          "type": "object",
          "properties": {
            "min": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "max": {"type": "number", "minimum": 0.0, "maximum": 1.0}
          },
          "additionalProperties": false
        },
        "date_range": {
          "type": "object",
          "properties": {
            "start": {"type": "string", "format": "date-time"},
            "end": {"type": "string", "format": "date-time"}
          },
          "required": ["start", "end"],
          "additionalProperties": false
        },
        "camera_ids": {
          "type": "array",
          "items": {"type": "string"},
          "uniqueItems": true,
          "maxItems": 100
        },
        "plate_regions": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^[A-Z]{2}$"
          },
          "uniqueItems": true
        },
        "vehicle_types": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["sedan", "suv", "truck", "motorcycle", "van", "other"]
          },
          "uniqueItems": true
        },
        "processed_status": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["pending", "completed", "failed"]
          },
          "uniqueItems": true
        }
      },
      "additionalProperties": false
    },
    "sort": {
      "type": "object",
      "properties": {
        "field": {
          "type": "string",
          "enum": ["timestamp", "confidence", "license_plate", "camera_id", "relevance"]
        },
        "order": {
          "type": "string",
          "enum": ["asc", "desc"]
        }
      },
      "required": ["field", "order"],
      "additionalProperties": false
    },
    "pagination": {
      "type": "object",
      "properties": {
        "page": {"type": "integer", "minimum": 1, "default": 1},
        "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 20}
      },
      "additionalProperties": false
    },
    "include": {
      "type": "object",
      "properties": {
        "images": {"type": "boolean", "default": false},
        "enhanced_images": {"type": "boolean", "default": false},
        "metadata": {"type": "boolean", "default": true}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

#### Response Contract - Success (200)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Advanced Search Response",
  "properties": {
    "success": {"type": "boolean", "const": true},
    "results": {
      "type": "array",
      "items": {
        "allOf": [
          {"$ref": "#/definitions/DetectionResult"},
          {
            "properties": {
              "relevance_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Search relevance score (for fuzzy search)"
              }
            }
          }
        ]
      }
    },
    "search_metadata": {
      "type": "object",
      "properties": {
        "total_matches": {"type": "integer", "minimum": 0},
        "exact_matches": {"type": "integer", "minimum": 0},
        "fuzzy_matches": {"type": "integer", "minimum": 0},
        "query_time": {"type": "number", "minimum": 0},
        "search_terms_used": {"type": "array", "items": {"type": "string"}},
        "filters_applied": {"type": "object"}
      },
      "required": ["total_matches", "query_time"],
      "additionalProperties": false
    },
    "pagination": {"$ref": "#/definitions/Pagination"},
    "aggregations": {
      "type": "object",
      "properties": {
        "by_camera": {
          "type": "object",
          "patternProperties": {
            "^[a-zA-Z0-9_-]+$": {"type": "integer", "minimum": 0}
          }
        },
        "by_date": {
          "type": "object",
          "patternProperties": {
            "^\\d{4}-\\d{2}-\\d{2}$": {"type": "integer", "minimum": 0}
          }
        },
        "by_confidence_range": {
          "type": "object",
          "properties": {
            "high": {"type": "integer", "minimum": 0, "description": "0.8-1.0"},
            "medium": {"type": "integer", "minimum": 0, "description": "0.5-0.8"},
            "low": {"type": "integer", "minimum": 0, "description": "0.0-0.5"}
          }
        }
      }
    }
  },
  "required": ["success", "results", "search_metadata", "pagination"],
  "additionalProperties": false
}
```

---

## 3. System API Contracts

### GET /api/system/health
**Purpose**: System health check and status information

#### Response Contract - Success (200)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "System Health Response",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["healthy", "degraded", "unhealthy"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "uptime": {
      "type": "integer",
      "minimum": 0,
      "description": "System uptime in seconds"
    },
    "services": {
      "type": "object",
      "properties": {
        "database": {
          "$ref": "#/definitions/ServiceHealth"
        },
        "camera_service": {
          "$ref": "#/definitions/ServiceHealth"
        },
        "detection_service": {
          "$ref": "#/definitions/ServiceHealth"
        },
        "storage_service": {
          "$ref": "#/definitions/ServiceHealth"
        }
      },
      "required": ["database", "camera_service", "detection_service", "storage_service"],
      "additionalProperties": false
    },
    "system_metrics": {
      "type": "object",
      "properties": {
        "cpu_usage": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 100.0,
          "description": "CPU usage percentage"
        },
        "memory_usage": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 100.0,
          "description": "Memory usage percentage"
        },
        "disk_usage": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 100.0,
          "description": "Disk usage percentage"
        },
        "active_connections": {
          "type": "integer",
          "minimum": 0
        }
      },
      "required": ["cpu_usage", "memory_usage", "disk_usage"],
      "additionalProperties": false
    }
  },
  "required": ["status", "timestamp", "version", "uptime", "services", "system_metrics"],
  "additionalProperties": false,
  
  "definitions": {
    "ServiceHealth": {
      "type": "object",
      "properties": {
        "status": {
          "type": "string",
          "enum": ["healthy", "degraded", "unhealthy"]
        },
        "response_time": {
          "type": "number",
          "minimum": 0,
          "description": "Service response time in milliseconds"
        },
        "last_check": {
          "type": "string",
          "format": "date-time"
        },
        "error_message": {
          "type": ["string", "null"],
          "description": "Error message if service is unhealthy"
        },
        "details": {
          "type": "object",
          "description": "Service-specific health details"
        }
      },
      "required": ["status", "response_time", "last_check"],
      "additionalProperties": false
    }
  }
}
```

### GET /api/system/config
**Purpose**: Retrieve current system configuration

#### Response Contract - Success (200)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "System Configuration Response",
  "properties": {
    "success": {"type": "boolean", "const": true},
    "configuration": {
      "type": "object",
      "properties": {
        "detection": {
          "type": "object",
          "properties": {
            "confidence_threshold": {
              "type": "number",
              "minimum": 0.0,
              "maximum": 1.0
            },
            "model_path": {"type": "string"},
            "batch_size": {"type": "integer", "minimum": 1},
            "gpu_enabled": {"type": "boolean"},
            "max_detections_per_image": {"type": "integer", "minimum": 1}
          },
          "required": ["confidence_threshold", "model_path"],
          "additionalProperties": false
        },
        "camera": {
          "type": "object",
          "properties": {
            "default_resolution": {
              "type": "string",
              "pattern": "^\\d+x\\d+$"
            },
            "frame_rate": {"type": "integer", "minimum": 1, "maximum": 120},
            "timeout": {"type": "integer", "minimum": 1},
            "auto_reconnect": {"type": "boolean"}
          },
          "required": ["default_resolution", "frame_rate"],
          "additionalProperties": false
        },
        "storage": {
          "type": "object",
          "properties": {
            "save_images": {"type": "boolean"},
            "save_videos": {"type": "boolean"},
            "retention_days": {"type": "integer", "minimum": 1},
            "max_storage_gb": {"type": "integer", "minimum": 1},
            "compression_enabled": {"type": "boolean"}
          },
          "required": ["save_images", "retention_days"],
          "additionalProperties": false
        },
        "api": {
          "type": "object",
          "properties": {
            "rate_limit_per_minute": {"type": "integer", "minimum": 1},
            "max_file_size_mb": {"type": "integer", "minimum": 1},
            "cors_enabled": {"type": "boolean"},
            "api_key_required": {"type": "boolean"}
          },
          "additionalProperties": false
        }
      },
      "required": ["detection", "camera", "storage"],
      "additionalProperties": false
    },
    "last_updated": {
      "type": "string",
      "format": "date-time"
    },
    "config_version": {
      "type": "string"
    }
  },
  "required": ["success", "configuration", "last_updated"],
  "additionalProperties": false
}
```

---

## 4. Stream API Contracts

### WebSocket /ws/stream
**Purpose**: Real-time detection updates via WebSocket

#### Connection Requirements
```yaml
connection:
  protocol: "WebSocket"
  subprotocols: ["lpr-v1"]
  headers:
    authorization: "Bearer {api_token}"  # Optional
  query_parameters:
    camera_id: "string (optional)"
    subscribe_to: "detections,stats,alerts"
```

#### Message Contracts

##### Detection Update Message
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Detection Update Message",
  "properties": {
    "type": {
      "type": "string",
      "const": "detection_update"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "data": {
      "type": "object",
      "properties": {
        "camera_id": {"type": "string"},
        "session_id": {"type": "string"},
        "frame_number": {"type": "integer", "minimum": 0},
        "detections": {
          "type": "array",
          "items": {"$ref": "#/definitions/Detection"}
        },
        "frame_metadata": {
          "type": "object",
          "properties": {
            "fps": {"type": "number", "minimum": 0},
            "resolution": {"type": "string"},
            "processing_time": {"type": "number", "minimum": 0}
          }
        }
      },
      "required": ["camera_id", "detections"],
      "additionalProperties": false
    }
  },
  "required": ["type", "timestamp", "data"],
  "additionalProperties": false
}
```

##### System Stats Message
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "System Stats Message",
  "properties": {
    "type": {
      "type": "string",
      "const": "system_stats"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "data": {
      "type": "object",
      "properties": {
        "active_cameras": {"type": "integer", "minimum": 0},
        "detections_per_minute": {"type": "number", "minimum": 0},
        "average_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "system_load": {
          "type": "object",
          "properties": {
            "cpu": {"type": "number", "minimum": 0, "maximum": 100},
            "memory": {"type": "number", "minimum": 0, "maximum": 100},
            "gpu": {"type": ["number", "null"], "minimum": 0, "maximum": 100}
          }
        }
      },
      "required": ["active_cameras", "detections_per_minute"],
      "additionalProperties": false
    }
  },
  "required": ["type", "timestamp", "data"],
  "additionalProperties": false
}
```

##### Error Message
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "WebSocket Error Message",
  "properties": {
    "type": {
      "type": "string",
      "const": "error"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "data": {
      "type": "object",
      "properties": {
        "error_code": {
          "type": "string",
          "enum": [
            "AUTHENTICATION_FAILED",
            "INVALID_SUBSCRIPTION",
            "CAMERA_UNAVAILABLE",
            "RATE_LIMIT_EXCEEDED",
            "INTERNAL_ERROR"
          ]
        },
        "message": {"type": "string"},
        "details": {"type": "object"}
      },
      "required": ["error_code", "message"],
      "additionalProperties": false
    }
  },
  "required": ["type", "timestamp", "data"],
  "additionalProperties": false
}
```

---

## 5. Common Data Definitions

### Shared Schema Definitions
```json
{
  "definitions": {
    "Detection": {
      "type": "object",
      "properties": {
        "id": {"type": ["integer", "null"]},
        "license_plate": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "bbox": {
          "type": "array",
          "items": {"type": "integer", "minimum": 0},
          "minItems": 4,
          "maxItems": 4
        },
        "ocr_confidence": {"type": ["number", "null"], "minimum": 0.0, "maximum": 1.0},
        "plate_region": {"type": ["string", "null"]},
        "vehicle_type": {"type": ["string", "null"]},
        "enhanced_image_path": {"type": ["string", "null"]},
        "processing_metadata": {
          "type": "object",
          "properties": {
            "model_version": {"type": "string"},
            "processing_time": {"type": "number"},
            "enhancement_applied": {"type": "boolean"}
          }
        }
      },
      "required": ["license_plate", "confidence", "bbox"],
      "additionalProperties": false
    },
    
    "Pagination": {
      "type": "object",
      "properties": {
        "current_page": {"type": "integer", "minimum": 1},
        "per_page": {"type": "integer", "minimum": 1},
        "total_results": {"type": "integer", "minimum": 0},
        "total_pages": {"type": "integer", "minimum": 0},
        "has_next_page": {"type": "boolean"},
        "has_previous_page": {"type": "boolean"},
        "next_page_url": {"type": ["string", "null"], "format": "uri"},
        "previous_page_url": {"type": ["string", "null"], "format": "uri"}
      },
      "required": ["current_page", "per_page", "total_results", "total_pages", "has_next_page", "has_previous_page"],
      "additionalProperties": false
    },
    
    "ErrorResponse": {
      "type": "object",
      "properties": {
        "success": {"type": "boolean", "const": false},
        "error": {
          "type": "object",
          "properties": {
            "code": {"type": "string"},
            "message": {"type": "string"},
            "details": {"type": ["object", "array", "string", "null"]},
            "request_id": {"type": "string"},
            "documentation_url": {"type": "string", "format": "uri"}
          },
          "required": ["code", "message"],
          "additionalProperties": false
        },
        "timestamp": {"type": "string", "format": "date-time"}
      },
      "required": ["success", "error", "timestamp"],
      "additionalProperties": false
    }
  }
}
```

---

## 6. Error Code Standards

### HTTP Status Codes
| Status Code | Meaning | Usage |
|-------------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (duplicate) |
| 413 | Payload Too Large | File size exceeds limit |
| 415 | Unsupported Media Type | Invalid file format |
| 422 | Unprocessable Entity | Valid format but processing failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Application Error Codes
```yaml
error_codes:
  authentication:
    INVALID_API_KEY: "API key is invalid or expired"
    MISSING_AUTHORIZATION: "Authorization header is required"
    INSUFFICIENT_PERMISSIONS: "Insufficient permissions for this operation"
    
  validation:
    INVALID_FILE_FORMAT: "File format not supported"
    FILE_TOO_LARGE: "File size exceeds maximum limit"
    INVALID_PARAMETERS: "One or more parameters are invalid"
    MISSING_REQUIRED_FIELD: "Required field is missing"
    
  processing:
    DETECTION_FAILED: "License plate detection failed"
    OCR_PROCESSING_FAILED: "Text recognition failed"
    IMAGE_CORRUPTED: "Image file is corrupted or unreadable"
    CAMERA_UNAVAILABLE: "Camera source is not available"
    
  system:
    DATABASE_ERROR: "Database operation failed"
    STORAGE_ERROR: "File storage operation failed"
    SERVICE_UNAVAILABLE: "Required service is unavailable"
    RATE_LIMIT_EXCEEDED: "API rate limit exceeded"
    
  resource:
    RESOURCE_NOT_FOUND: "Requested resource not found"
    RESOURCE_ALREADY_EXISTS: "Resource already exists"
    RESOURCE_LOCKED: "Resource is locked by another operation"
```

---

## 7. Contract Testing Framework

### Testing Approach
```yaml
contract_testing:
  framework: "Pact" # Consumer-driven contract testing
  languages: 
    consumer: "Java (REST Assured)"
    provider: "Python (FastAPI)"
    
  test_structure:
    consumer_tests:
      - request_format_validation
      - response_schema_validation
      - error_handling_contracts
      
    provider_tests:
      - contract_compliance_verification
      - backward_compatibility_checks
      - schema_evolution_validation

  contract_versioning:
    strategy: "semantic_versioning"
    breaking_changes: "major_version_bump"
    new_features: "minor_version_bump"
    bug_fixes: "patch_version_bump"
```

### Contract Test Examples
```java
// Java consumer contract test example
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "lpr-api", port = "8080")
public class DetectionApiContractTest {
    
    @Pact(consumer = "automation-framework")
    public RequestResponsePact imageUploadContract(PactDslWithProvider builder) {
        return builder
            .given("valid image upload")
            .uponReceiving("upload image for detection")
            .path("/api/detect/upload")
            .method("POST")
            .headers("Content-Type", "multipart/form-data")
            .body(PactDslJsonBody.body()
                .object("settings")
                    .numberType("confidence_threshold", 0.7)
                    .booleanType("save_results", true)
                .closeObject())
            .willRespondWith()
            .status(200)
            .headers("Content-Type", "application/json")
            .body(PactDslJsonBody.body()
                .booleanValue("success", true)
                .uuid("request_id")
                .stringType("filename")
                .array("detections")
                    .object()
                        .stringType("license_plate")
                        .numberType("confidence")
                        .array("bbox").numberType().numberType().numberType().numberType().closeArray()
                    .closeObject()
                .closeArray()
                .numberType("processing_time"))
            .toPact();
    }
    
    @Test
    @PactTestFor(pactMethod = "imageUploadContract")
    void testImageUploadContract() {
        // Test implementation using REST Assured
        given()
            .multiPart("file", new File("test-image.jpg"))
            .multiPart("settings", "{\"confidence_threshold\": 0.7}", "application/json")
        .when()
            .post("/api/detect/upload")
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("detections", notNullValue());
    }
}
```

### Contract Validation Tools
```yaml
validation_tools:
  json_schema_validator:
    library: "everit-org/json-schema"
    purpose: "Request/response schema validation"
    
  openapi_validator:
    library: "swagger-api/swagger-core"
    purpose: "OpenAPI specification validation"
    
  contract_testing:
    library: "pact-foundation/pact-jvm"
    purpose: "Consumer-driven contract testing"
    
automation_integration:
  ci_cd_pipeline:
    - schema_validation_tests
    - contract_compliance_tests
    - backward_compatibility_tests
    - contract_versioning_checks
```

This comprehensive API contract documentation provides the foundation for robust contract testing and ensures consistent API behavior across all implementations and integrations.