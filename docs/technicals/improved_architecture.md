# Improved License Plate Recognition Architecture

This document describes the improved architecture for the License Plate Recognition system.

## Overview

The new architecture is built around the following key principles:

1. **Interface-Based Design**: All major components define interfaces to abstract their functionality
2. **Dependency Injection**: Components receive their dependencies through initialization rather than directly referencing them
3. **Repository Pattern**: Data storage is abstracted behind repository interfaces
4. **Service Factory**: A central factory manages the creation and lifecycle of services

## Key Components

### Interfaces

The system defines the following interfaces:

- `Camera`: Interface for camera operations
- `LicensePlateDetector`: Interface for license plate detection
- `LicensePlateEnhancer`: Interface for license plate enhancement
- `DetectionRepository`: Interface for detection storage
- `EnhancementRepository`: Interface for enhancement storage

### Repositories

The system includes the following repository implementations:

- `JSONDetectionRepository`: Stores detections in JSON files
- `JSONEnhancementRepository`: Stores enhanced results in JSON files

### Services

The system includes the following service implementations:

- `CameraService`: Manages camera operations
- `DetectionServiceV2`: Improved detection service using interfaces
- `LicensePlateRecognitionService`: Detects and recognizes license plates
- `EnhancerService`: Enhances license plate detections
- `StorageServiceV2`: Improved storage service using repositories

### Factory

The `ServiceFactory` class manages the creation and lifecycle of services:

- Configures services based on application settings
- Creates services with their dependencies
- Provides a centralized point for service management
- Handles proper shutdown of services

## API Versioning

The improved architecture is available through a new API version (v2):

- `/v2/stream/*`: Streaming endpoints
- `/v2/detection/*`: Detection endpoints
- `/v2/results/*`: Results endpoints

The original API (v1) remains available for backward compatibility.

## Class Diagram

```
+----------------+    +--------------------+    +-------------------+
| Camera         |<---| CameraService      |<---| DetectionServiceV2|
+----------------+    +--------------------+    +-------------------+
                                                         |
+----------------+    +--------------------+             |
| LicensePlate   |<---| LicensePlateRecog- |<------------+
| Detector       |    | nitionService      |             |
+----------------+    +--------------------+             |
                                                         |
+----------------+    +--------------------+             |
| LicensePlate   |<---| EnhancerService    |<------------+
| Enhancer       |    |                    |             |
+----------------+    +--------------------+             |
                                                         |
+----------------+    +--------------------+             |
| Detection      |<---| JSONDetection      |<------------+
| Repository     |    | Repository         |             |
+----------------+    +--------------------+             |
                                                         |
+----------------+    +--------------------+             |
| Enhancement    |<---| JSONEnhancement    |<------------+
| Repository     |    | Repository         |
+----------------+    +--------------------+
```

## Benefits of the New Architecture

1. **Testability**: Services can be tested in isolation with mock dependencies
2. **Flexibility**: Implementations can be changed without affecting client code
3. **Maintainability**: Clear separation of concerns makes the code easier to understand and modify
4. **Scalability**: Components can be scaled independently

## Migration Path

To migrate from the old architecture to the new one:

1. Use the v2 API endpoints for new code
2. Gradually migrate existing code to use the new interfaces
3. Eventually deprecate the v1 API

## Configuration

The improved architecture uses the same configuration settings as the original one but processes them through the `ServiceFactory` instead of directly in the services.

## Running the New Version

To run the new version of the application:

```
python -m app.main_v2
```

The application will be available at:

- http://localhost:8001/ - Original UI
- http://localhost:8001/v2 - Improved UI for v2 API