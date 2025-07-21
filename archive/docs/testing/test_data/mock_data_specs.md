# Test Data Specifications - License Plate Recognition System

## Overview

This document specifies the test data requirements, formats, and generation strategies for comprehensive testing of the LPR system. All test data should be synthetic or properly anonymized to ensure privacy compliance.

## Test Data Categories

### 1. Image Test Data
### 2. Video Test Data  
### 3. Database Test Data
### 4. Configuration Test Data
### 5. Mock External Data
### 6. Performance Test Data
### 7. Security Test Data

---

## 1. Image Test Data

### License Plate Images

#### Format Specifications
```yaml
image_formats:
  primary: JPEG
  secondary: PNG
  supported: [JPG, JPEG, PNG, BMP, TIFF]
  
resolution_categories:
  low_res: 
    dimensions: 640x480
    use_case: "mobile_uploads"
    
  medium_res:
    dimensions: 1920x1080
    use_case: "standard_cameras"
    
  high_res:
    dimensions: 3840x2160
    use_case: "4k_cameras"
    
file_sizes:
  small: 100KB - 500KB
  medium: 500KB - 2MB
  large: 2MB - 10MB
  extra_large: 10MB - 50MB  # For stress testing
```

#### License Plate Variations
```yaml
us_license_plates:
  california:
    format: "7ABC123"
    pattern: "[0-9][A-Z]{3}[0-9]{3}"
    examples: ["1ABC123", "2XYZ789", "9DEF456"]
    
  texas:
    format: "ABC-1234"
    pattern: "[A-Z]{3}-[0-9]{4}"
    examples: ["ABC-1234", "XYZ-5678", "DEF-9012"]
    
  new_york:
    format: "ABC-1234"
    pattern: "[A-Z]{3}-[0-9]{4}"
    examples: ["ABC-1234", "XYZ-5678", "DEF-9012"]
    
  florida:
    format: "ABC 123"
    pattern: "[A-Z]{3} [0-9]{3}"
    examples: ["ABC 123", "XYZ 456", "DEF 789"]

international_plates:
  european:
    format: "AB-123-CD"
    pattern: "[A-Z]{2}-[0-9]{3}-[A-Z]{2}"
    examples: ["AB-123-CD", "XY-456-EF", "GH-789-IJ"]
    
  canadian:
    format: "ABC 123"
    pattern: "[A-Z]{3} [0-9]{3}"
    examples: ["ABC 123", "XYZ 456", "DEF 789"]
```

#### Image Quality Variations
```yaml
quality_levels:
  excellent:
    description: "Clear, well-lit, high contrast"
    confidence_range: [0.9, 1.0]
    use_cases: ["optimal_conditions", "baseline_testing"]
    
  good:
    description: "Slightly blurry, adequate lighting"
    confidence_range: [0.7, 0.9]
    use_cases: ["normal_conditions", "standard_testing"]
    
  fair:
    description: "Somewhat blurry, poor lighting"
    confidence_range: [0.5, 0.7]
    use_cases: ["challenging_conditions", "edge_case_testing"]
    
  poor:
    description: "Very blurry, bad lighting, obscured"
    confidence_range: [0.1, 0.5]
    use_cases: ["extreme_conditions", "error_handling"]
    
  no_plate:
    description: "Images with no license plates"
    confidence_range: [0.0, 0.1]
    use_cases: ["negative_testing", "false_positive_detection"]
```

#### Test Image Generation
```python
# Sample image generation script structure
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class TestImageGenerator:
    def __init__(self):
        self.fonts = self.load_license_plate_fonts()
        self.backgrounds = self.load_background_images()
    
    def generate_license_plate_image(self, 
                                   plate_text: str,
                                   state_format: str,
                                   quality_level: str,
                                   resolution: tuple) -> np.ndarray:
        """
        Generate synthetic license plate image
        
        Args:
            plate_text: License plate text (e.g., "ABC123")
            state_format: State format (e.g., "california")
            quality_level: Image quality (e.g., "good")
            resolution: Image dimensions (width, height)
            
        Returns:
            Generated image as numpy array
        """
        # Implementation details for image generation
        pass
    
    def apply_quality_effects(self, image: np.ndarray, quality: str) -> np.ndarray:
        """Apply quality degradation effects"""
        effects = {
            "excellent": [],
            "good": ["slight_blur"],
            "fair": ["blur", "noise", "low_contrast"],
            "poor": ["heavy_blur", "heavy_noise", "very_low_contrast"]
        }
        # Apply effects based on quality level
        return image
    
    def generate_test_dataset(self, count: int, specifications: dict) -> list:
        """Generate complete test dataset"""
        dataset = []
        for i in range(count):
            image_spec = self.select_random_spec(specifications)
            image = self.generate_license_plate_image(**image_spec)
            dataset.append({
                "image": image,
                "metadata": image_spec,
                "expected_result": self.calculate_expected_detection(image_spec)
            })
        return dataset
```

### Sample Image Manifest
```json
{
  "test_image_manifest": {
    "version": "1.0",
    "generated_date": "2024-01-15",
    "total_images": 1000,
    "categories": {
      "us_license_plates": {
        "count": 700,
        "subcategories": {
          "california": 200,
          "texas": 150,
          "new_york": 150,
          "florida": 100,
          "other_states": 100
        }
      },
      "international_plates": {
        "count": 200,
        "subcategories": {
          "european": 100,
          "canadian": 50,
          "other": 50
        }
      },
      "no_plates": {
        "count": 100,
        "subcategories": {
          "vehicles_no_plate": 50,
          "random_scenes": 50
        }
      }
    },
    "quality_distribution": {
      "excellent": 250,
      "good": 400,
      "fair": 250,
      "poor": 100
    },
    "resolution_distribution": {
      "low_res": 200,
      "medium_res": 600,
      "high_res": 200
    }
  }
}
```

---

## 2. Video Test Data

### Video Specifications
```yaml
video_formats:
  primary: MP4
  secondary: AVI
  supported: [MP4, AVI, MOV, MKV, WEBM]
  
video_properties:
  codecs:
    video: [H.264, H.265, VP9]
    audio: [AAC, MP3] # Optional for testing
    
  frame_rates:
    low: 15_fps
    standard: 30_fps
    high: 60_fps
    
  resolutions:
    sd: 640x480
    hd: 1280x720
    full_hd: 1920x1080
    ultra_hd: 3840x2160
    
  durations:
    short: 10_seconds
    medium: 60_seconds
    long: 300_seconds
    extended: 1800_seconds  # For endurance testing
```

### Video Content Scenarios
```yaml
traffic_scenarios:
  highway_traffic:
    description: "Multiple vehicles at highway speeds"
    vehicle_count: 10-20
    speed: "high"
    plate_visibility: "good"
    detection_rate: 0.8
    
  city_intersection:
    description: "Urban intersection with varied traffic"
    vehicle_count: 5-15
    speed: "medium"
    plate_visibility: "fair"
    detection_rate: 0.6
    
  parking_lot:
    description: "Stationary and slow-moving vehicles"
    vehicle_count: 3-8
    speed: "low"
    plate_visibility: "excellent"
    detection_rate: 0.95
    
  night_scene:
    description: "Low-light conditions with headlights"
    vehicle_count: 2-5
    speed: "medium"
    plate_visibility: "poor"
    detection_rate: 0.3
    
  weather_conditions:
    rain:
      visibility: "reduced"
      detection_rate: 0.4
    snow:
      visibility: "poor"
      detection_rate: 0.2
    fog:
      visibility: "very_poor"
      detection_rate: 0.1
```

### Video Generation Parameters
```python
class VideoTestDataGenerator:
    def __init__(self):
        self.vehicle_models = self.load_vehicle_database()
        self.license_plate_generator = LicensePlateGenerator()
    
    def generate_test_video(self, 
                          scenario: str,
                          duration: int,
                          resolution: tuple,
                          fps: int) -> str:
        """
        Generate synthetic test video
        
        Args:
            scenario: Traffic scenario type
            duration: Video length in seconds
            resolution: Video dimensions
            fps: Frames per second
            
        Returns:
            Path to generated video file
        """
        # Video generation implementation
        pass
    
    def add_license_plates_to_video(self, 
                                  video_path: str,
                                  plate_specifications: list) -> dict:
        """
        Add license plates to existing video and return ground truth
        
        Returns:
            Dictionary with frame-by-frame detection ground truth
        """
        ground_truth = {
            "video_path": video_path,
            "total_frames": 0,
            "detections": []  # Frame-by-frame detection data
        }
        return ground_truth
```

---

## 3. Database Test Data

### Detection Records Schema
```sql
-- Sample detection record structure
CREATE TABLE test_detections (
    id INTEGER PRIMARY KEY,
    license_plate VARCHAR(20),
    confidence DECIMAL(3,2),
    bbox_x1 INTEGER,
    bbox_y1 INTEGER,
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,
    image_path VARCHAR(255),
    camera_id VARCHAR(50),
    timestamp DATETIME,
    processed VARCHAR(10) DEFAULT 'pending',
    session_id VARCHAR(100),
    enhanced_image_path VARCHAR(255),
    ocr_confidence DECIMAL(3,2),
    plate_region VARCHAR(50),
    vehicle_type VARCHAR(30)
);
```

### Test Data Generation
```python
class DatabaseTestDataGenerator:
    def __init__(self):
        self.license_plate_patterns = self.load_state_patterns()
        self.camera_ids = ["cam_001", "cam_002", "cam_003", "cam_004"]
        
    def generate_detection_records(self, count: int, time_range: tuple) -> list:
        """
        Generate realistic detection records
        
        Args:
            count: Number of records to generate
            time_range: (start_date, end_date) for timestamp distribution
            
        Returns:
            List of detection record dictionaries
        """
        records = []
        for i in range(count):
            record = {
                "id": i + 1,
                "license_plate": self.generate_random_plate(),
                "confidence": random.uniform(0.5, 0.99),
                "bbox_x1": random.randint(50, 200),
                "bbox_y1": random.randint(50, 150),
                "bbox_x2": random.randint(300, 500),
                "bbox_y2": random.randint(200, 300),
                "image_path": f"/data/test_images/plate_{i:06d}.jpg",
                "camera_id": random.choice(self.camera_ids),
                "timestamp": self.generate_random_timestamp(time_range),
                "processed": random.choice(["pending", "completed", "failed"]),
                "session_id": f"session_{random.randint(1000, 9999)}",
                "enhanced_image_path": f"/data/enhanced/enhanced_{i:06d}.jpg",
                "ocr_confidence": random.uniform(0.6, 0.98),
                "plate_region": random.choice(["CA", "TX", "NY", "FL", "WA"]),
                "vehicle_type": random.choice(["sedan", "suv", "truck", "motorcycle"])
            }
            records.append(record)
        return records
```

### Database Test Scenarios
```yaml
test_datasets:
  small_dataset:
    record_count: 1000
    time_span: 7_days
    use_case: "unit_testing"
    
  medium_dataset:
    record_count: 50000
    time_span: 90_days
    use_case: "integration_testing"
    
  large_dataset:
    record_count: 1000000
    time_span: 365_days
    use_case: "performance_testing"
    
  historical_dataset:
    record_count: 5000000
    time_span: 3_years
    use_case: "volume_testing"

data_distribution:
  license_plate_uniqueness: 0.7  # 70% unique plates
  camera_distribution: "uniform"  # Equal distribution across cameras
  time_distribution: "business_hours_weighted"  # More activity during day
  confidence_distribution: "normal"  # Normal distribution around 0.8
  
quality_variations:
  high_confidence: 0.4  # 40% high confidence (>0.8)
  medium_confidence: 0.4  # 40% medium confidence (0.5-0.8)
  low_confidence: 0.2  # 20% low confidence (<0.5)
```

---

## 4. Configuration Test Data

### System Configuration Variations
```yaml
camera_configurations:
  usb_camera:
    type: "USB"
    device_id: 0
    resolution: "1920x1080"
    fps: 30
    auto_focus: true
    
  rtsp_camera:
    type: "RTSP"
    url: "rtsp://test-camera.local:554/stream"
    username: "test_user"
    password: "test_pass"
    timeout: 10
    
  file_input:
    type: "FILE"
    path: "/test_data/videos/test_video.mp4"
    loop: true
    
detection_configurations:
  high_accuracy:
    confidence_threshold: 0.8
    model: "yolo11m_best.pt"
    batch_size: 1
    gpu_enabled: true
    
  fast_processing:
    confidence_threshold: 0.6
    model: "yolo11n.pt"
    batch_size: 4
    gpu_enabled: true
    
  cpu_only:
    confidence_threshold: 0.7
    model: "yolo11m.pt"
    batch_size: 1
    gpu_enabled: false

storage_configurations:
  minimal_storage:
    save_images: false
    save_videos: false
    retention_days: 7
    
  full_storage:
    save_images: true
    save_videos: true
    retention_days: 365
    max_storage_gb: 1000
```

### Invalid Configuration Test Cases
```yaml
invalid_configurations:
  negative_confidence:
    confidence_threshold: -0.5
    expected_error: "ValueError: confidence must be between 0 and 1"
    
  exceeding_confidence:
    confidence_threshold: 1.5
    expected_error: "ValueError: confidence must be between 0 and 1"
    
  invalid_model_path:
    model_path: "/nonexistent/model.pt"
    expected_error: "FileNotFoundError: Model file not found"
    
  invalid_camera_id:
    camera_id: "invalid_camera"
    expected_error: "CameraNotFoundError"
    
  invalid_resolution:
    resolution: "invalid_resolution"
    expected_error: "ValueError: Invalid resolution format"
```

---

## 5. Mock External Data

### Webhook Test Data
```yaml
webhook_configurations:
  valid_webhook:
    url: "https://webhook-test.example.com/lpr"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer test_token"
    
  authenticated_webhook:
    url: "https://secure-webhook.example.com/lpr"
    method: "POST"
    auth_type: "basic"
    username: "test_user"
    password: "test_pass"
    
  failing_webhook:
    url: "https://failing-webhook.example.com/lpr"
    method: "POST"
    expected_response: 500
    
webhook_payloads:
  detection_event:
    event_type: "detection_created"
    timestamp: "2024-01-15T10:30:00Z"
    data:
      license_plate: "ABC123"
      confidence: 0.85
      camera_id: "cam_001"
      image_url: "https://api.example.com/images/detection_123.jpg"
```

### External API Mock Data
```yaml
mock_apis:
  license_validation_service:
    base_url: "https://api.license-validation.com"
    endpoints:
      validate_plate:
        path: "/v1/validate"
        method: "POST"
        request_format:
          license_plate: "string"
          state: "string"
        response_format:
          valid: "boolean"
          state: "string"
          expired: "boolean"
    
  vehicle_database_service:
    base_url: "https://api.vehicle-db.com"
    endpoints:
      lookup_vehicle:
        path: "/v1/lookup"
        method: "GET"
        parameters:
          plate: "query_parameter"
        response_format:
          make: "string"
          model: "string"
          year: "integer"
          color: "string"
```

---

## 6. Performance Test Data

### Load Testing Data Sets
```yaml
performance_datasets:
  api_load_test:
    concurrent_users: [10, 25, 50, 100, 200]
    test_duration: 300_seconds
    images_per_user: 50
    image_sizes: [500KB, 1MB, 2MB, 5MB]
    
  database_load_test:
    concurrent_connections: [20, 50, 100, 200]
    queries_per_connection: 1000
    query_types: ["select", "insert", "update", "delete"]
    query_complexity: ["simple", "complex", "join"]
    
  file_system_load_test:
    concurrent_operations: [10, 25, 50, 100]
    file_operations: ["read", "write", "delete"]
    file_sizes: [1MB, 10MB, 100MB, 1GB]
    operation_count: 10000

stress_test_data:
  memory_stress:
    large_images: 
      count: 100
      size: 50MB_each
    batch_processing:
      batch_size: 50
      concurrent_batches: 10
      
  cpu_stress:
    high_resolution_images:
      resolution: "4K"
      count: 500
    complex_detections:
      multiple_plates_per_image: 5
      difficult_angles: true
```

### Volume Testing Data
```yaml
volume_test_datasets:
  large_database:
    detection_records: 10000000  # 10 million
    time_span: 3_years
    storage_size: 100GB
    
  massive_file_system:
    image_files: 1000000  # 1 million images
    video_files: 10000    # 10K videos
    total_storage: 5TB
    
  high_throughput:
    requests_per_second: 1000
    concurrent_connections: 500
    test_duration: 3600_seconds  # 1 hour
```

---

## 7. Security Test Data

### Authentication Test Data
```yaml
authentication_scenarios:
  valid_credentials:
    api_key: "valid_test_api_key_12345"
    username: "test_user"
    password: "Test123!"
    role: "operator"
    
  invalid_credentials:
    expired_api_key: "expired_api_key_67890"
    wrong_password: "wrong_password"
    disabled_user: "disabled_user"
    
  malicious_inputs:
    sql_injection: "'; DROP TABLE detections; --"
    xss_attempt: "<script>alert('xss')</script>"
    path_traversal: "../../../../etc/passwd"
    
authorization_test_data:
  roles:
    admin:
      permissions: ["read", "write", "delete", "configure"]
      endpoints: ["all"]
      
    operator:
      permissions: ["read", "write"]
      endpoints: ["/api/detect", "/api/results", "/api/stream"]
      
    viewer:
      permissions: ["read"]
      endpoints: ["/api/results", "/api/system/health"]
```

### Input Validation Test Data
```yaml
malformed_requests:
  invalid_json:
    - "{"  # Incomplete JSON
    - '{"key": value}'  # Unquoted value
    - '{"key": "value",}'  # Trailing comma
    
  oversized_requests:
    large_image: 100MB  # Exceeds typical limits
    huge_json: 10MB     # Oversized JSON payload
    
  invalid_parameters:
    negative_confidence: -0.5
    string_as_number: "not_a_number"
    null_required_field: null
    empty_required_field: ""
```

---

## Test Data Management

### Data Generation Scripts
```python
# Master test data generation script
class TestDataManager:
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
        self.generators = {
            "images": ImageTestDataGenerator(),
            "videos": VideoTestDataGenerator(),
            "database": DatabaseTestDataGenerator(),
            "performance": PerformanceTestDataGenerator()
        }
    
    def generate_complete_test_suite(self) -> dict:
        """Generate all test data according to specifications"""
        results = {}
        for data_type, generator in self.generators.items():
            print(f"Generating {data_type} test data...")
            results[data_type] = generator.generate(self.config[data_type])
        return results
    
    def validate_test_data(self, data_path: str) -> bool:
        """Validate generated test data meets specifications"""
        # Implementation for data validation
        pass
    
    def cleanup_test_data(self, older_than_days: int = 7) -> None:
        """Clean up old test data files"""
        # Implementation for cleanup
        pass
```

### Data Storage Organization
```
test_data/
├── images/
│   ├── license_plates/
│   │   ├── us_states/
│   │   ├── international/
│   │   └── no_plates/
│   ├── quality_levels/
│   │   ├── excellent/
│   │   ├── good/
│   │   ├── fair/
│   │   └── poor/
│   └── resolutions/
│       ├── low_res/
│       ├── medium_res/
│       └── high_res/
├── videos/
│   ├── scenarios/
│   │   ├── highway/
│   │   ├── city/
│   │   ├── parking/
│   │   └── night/
│   ├── durations/
│   │   ├── short/
│   │   ├── medium/
│   │   └── long/
│   └── ground_truth/
├── database/
│   ├── small_dataset.sql
│   ├── medium_dataset.sql
│   ├── large_dataset.sql
│   └── schemas/
├── configurations/
│   ├── valid/
│   ├── invalid/
│   └── edge_cases/
└── mock_data/
    ├── webhooks/
    ├── api_responses/
    └── external_services/
```

### Data Version Control
```yaml
test_data_versioning:
  version_format: "YYYY.MM.DD.sequence"
  current_version: "2024.01.15.001"
  
  changelog:
    "2024.01.15.001":
      - "Initial test data generation"
      - "Added 1000 synthetic license plate images"
      - "Created performance test datasets"
      
  compatibility:
    automation_framework: ">=1.0.0"
    lpr_application: ">=2.0.0"
    
data_integrity:
  checksums: enabled
  validation_scripts: included
  corruption_detection: automated
```

### Test Data Documentation
```yaml
documentation_requirements:
  image_manifest:
    required_fields:
      - image_path
      - expected_license_plate
      - expected_confidence_range
      - quality_level
      - resolution
      - file_size
      
  video_manifest:
    required_fields:
      - video_path
      - duration
      - frame_count
      - detection_ground_truth
      - scenario_type
      
  database_manifest:
    required_fields:
      - record_count
      - time_range
      - data_distribution
      - generation_parameters
```

## Quality Assurance for Test Data

### Data Validation Rules
1. **Image Validation**: Format, size, readability verification
2. **Video Validation**: Playability, frame count, duration accuracy
3. **Database Validation**: Schema compliance, data integrity, constraint validation
4. **Configuration Validation**: Syntax correctness, parameter ranges
5. **Performance Data Validation**: Load profile accuracy, resource requirements

### Test Data Metrics
- **Coverage**: Percentage of test scenarios with adequate test data
- **Diversity**: Variety in test data to cover edge cases
- **Realism**: How closely test data mirrors real-world scenarios
- **Maintainability**: Ease of updating and extending test data
- **Performance**: Test data generation and loading times

### Continuous Data Improvement
- Regular review and update of test data specifications
- Addition of new test scenarios based on production findings
- Performance optimization of test data generation
- Community feedback integration for test data enhancement

This comprehensive test data specification provides the foundation for creating realistic, diverse, and comprehensive test datasets that will enable thorough testing of the License Plate Recognition system across all testing categories.