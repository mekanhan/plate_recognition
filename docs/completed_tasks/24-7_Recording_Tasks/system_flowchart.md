# 24/7 Recording System - Flow Diagrams

This document contains detailed flowcharts and process diagrams for the 24/7 recording system.

## 🔄 System Overview Flowchart

```mermaid
graph TB
    A[System Startup] --> B[Load Configuration]
    B --> C[Initialize Storage Manager]
    C --> D[Create Recording Manager]
    D --> E[Start Camera Recordings]
    
    E --> F{Camera Available?}
    F -->|Yes| G[Establish RTSP Connection]
    F -->|No| H[Log Error & Retry]
    H --> I[Wait with Exponential Backoff]
    I --> F
    
    G --> J[Start Capture Thread]
    J --> K[Start Recording Thread]
    K --> L[Start Cleanup Thread]
    
    L --> M[Continuous Operation]
    M --> N[Health Check Every 30s]
    N --> O{Recording Healthy?}
    O -->|Yes| M
    O -->|No| P[Restart Failed Recording]
    P --> M
    
    M --> Q[Storage Cleanup Every Hour]
    Q --> R[Monitor Disk Usage]
    R --> M
```

## 📹 Recording Process Flow

```mermaid
graph TB
    A[Camera RTSP Stream] --> B[Capture Thread]
    B --> C[Read Frame from Stream]
    C --> D{Frame Valid?}
    D -->|No| E[Log Error]
    E --> F[Attempt Reconnection]
    F --> C
    
    D -->|Yes| G[Add to Frame Queue]
    G --> H{Queue Full?}
    H -->|Yes| I[Drop Oldest Frame]
    I --> G
    H -->|No| J[Recording Thread Processes]
    
    J --> K{New Segment Needed?}
    K -->|Yes| L[Finalize Current Segment]
    L --> M[Update SQLite Index]
    M --> N[Start New Segment]
    
    K -->|No| O[Write Frame to Current Segment]
    N --> O
    O --> J
    
    L --> P[Create Date/Time Directory]
    P --> Q[Initialize Video Writer]
    Q --> R[Test Codec Compatibility]
    R --> S{Codec Works?}
    S -->|No| T[Try Next Codec]
    T --> R
    S -->|Yes| U[Begin Recording Segment]
    U --> O
```

## 🗄️ Storage Management Flow

```mermaid
graph TB
    A[Storage Manager Startup] --> B[Load Retention Policy]
    B --> C[Start Cleanup Loop]
    C --> D[Wait Cleanup Interval]
    D --> E[Scan Camera Directories]
    
    E --> F[For Each Camera]
    F --> G[Connect to SQLite Index]
    G --> H[Query Old Segments]
    H --> I{Segments Found?}
    I -->|No| J[Next Camera]
    J --> F
    
    I -->|Yes| K[For Each Old Segment]
    K --> L[Delete Video File]
    L --> M[Remove from Database]
    M --> N[Update Statistics]
    N --> O{More Segments?}
    O -->|Yes| K
    O -->|No| P[Cleanup Empty Directories]
    
    P --> Q[Log Cleanup Results]
    Q --> J
    
    F --> R[Monitor Disk Usage]
    R --> S{Disk Space Low?}
    S -->|Yes| T[Log Warning]
    S -->|No| U[Continue Monitoring]
    T --> U
    U --> D
```

## 🔧 API Service Flow

```mermaid
graph TB
    A[API Request] --> B{Endpoint Type}
    
    B -->|/health| C[Health Check]
    C --> D[Check Recording Directories]
    D --> E[Query SQLite Databases]
    E --> F[Calculate Storage Stats]
    F --> G[Check Disk Usage]
    G --> H[Return Health Status]
    
    B -->|/recordings/status| I[Get All Camera Status]
    I --> J[For Each Camera Directory]
    J --> K[Read SQLite Index]
    K --> L[Calculate Recording Stats]
    L --> M[Check Recent Activity]
    M --> N[Aggregate Results]
    N --> O[Return Status JSON]
    
    B -->|/recordings/{id}/segments| P[Get Camera Segments]
    P --> Q[Validate Camera ID]
    Q --> R{Camera Exists?}
    R -->|No| S[Return 404 Error]
    R -->|Yes| T[Parse Time Parameters]
    T --> U[Query SQLite Database]
    U --> V[Filter by Time Range]
    V --> W[Format Segment Data]
    W --> X[Return Segments JSON]
    
    B -->|/storage/report| Y[Generate Storage Report]
    Y --> Z[Scan All Cameras]
    Z --> AA[Aggregate Statistics]
    AA --> BB[Calculate Disk Usage]
    BB --> CC[Format Report]
    CC --> DD[Return Comprehensive Report]
```

## ⚡ Error Recovery Flow

```mermaid
graph TB
    A[Error Detected] --> B{Error Type}
    
    B -->|Connection Lost| C[Camera Disconnection]
    C --> D[Release Current Connection]
    D --> E[Wait Backoff Delay]
    E --> F[Increment Retry Count]
    F --> G[Attempt Reconnection]
    G --> H{Connection Success?}
    H -->|Yes| I[Reset Retry Count]
    I --> J[Resume Recording]
    H -->|No| K{Max Retries?}
    K -->|No| L[Increase Backoff Delay]
    L --> E
    K -->|Yes| M[Log Permanent Failure]
    
    B -->|Storage Full| N[Disk Space Error]
    N --> O[Trigger Emergency Cleanup]
    O --> P[Delete Oldest Segments]
    P --> Q{Space Available?}
    Q -->|Yes| R[Resume Recording]
    Q -->|No| S[Alert Administrator]
    
    B -->|Codec Error| T[Video Encoding Error]
    T --> U[Try Next Codec]
    U --> V{More Codecs?}
    V -->|Yes| W[Initialize with New Codec]
    W --> X[Test Encoding]
    X --> Y{Encoding Works?}
    Y -->|Yes| J
    Y -->|No| U
    V -->|No| Z[Fallback to Basic Format]
    
    B -->|Database Error| AA[SQLite Error]
    AA --> BB[Close Database Connection]
    BB --> CC[Backup Current Database]
    CC --> DD[Recreate Database]
    DD --> EE[Restore Recent Data]
    EE --> J
```

## 🔄 Service Lifecycle

```mermaid
graph TB
    A[Service Start] --> B[Load Configuration Files]
    B --> C[Initialize Logging]
    C --> D[Create Storage Directories]
    D --> E[Setup Signal Handlers]
    
    E --> F[Start Storage Manager]
    F --> G[Initialize Recording Manager]
    G --> H[Load Camera Configurations]
    H --> I[For Each Enabled Camera]
    
    I --> J[Create Continuous Recorder]
    J --> K[Start Recording Threads]
    K --> L{All Cameras Started?}
    L -->|No| I
    L -->|Yes| M[Enter Service Loop]
    
    M --> N[Health Check Timer]
    N --> O[Check All Recordings]
    O --> P[Restart Failed Cameras]
    P --> Q[Update Statistics]
    Q --> R[Log Status]
    R --> S[Wait 30 Seconds]
    S --> N
    
    M --> T[Shutdown Signal]
    T --> U[Stop All Recordings]
    U --> V[Finalize Current Segments]
    V --> W[Close Database Connections]
    W --> X[Stop Storage Manager]
    X --> Y[Log Shutdown Complete]
    Y --> Z[Service Exit]
```

## 📊 Data Flow Diagram

```mermaid
graph LR
    A[RTSP Camera Stream] --> B[OpenCV Capture]
    B --> C[Frame Queue]
    C --> D[Video Writer]
    D --> E[AVI File Segment]
    
    E --> F[File System Storage]
    F --> G[Date/Time Directory Structure]
    
    D --> H[SQLite Database]
    H --> I[Segment Metadata]
    I --> J[Index for Fast Queries]
    
    J --> K[REST API Queries]
    K --> L[Health Status]
    K --> M[Storage Reports]
    K --> N[Segment Lists]
    
    F --> O[Cleanup Process]
    O --> P[Retention Policy Check]
    P --> Q[Delete Old Segments]
    Q --> R[Update Database]
```

## 🏗️ Component Architecture

```mermaid
graph TB
    subgraph "Recording Service Process"
        A[main_recording_service.py]
        A --> B[RecordingManager]
        B --> C[StorageManager]
        B --> D[ContinuousRecorder 1]
        B --> E[ContinuousRecorder N]
        
        D --> F[Capture Thread]
        D --> G[Recording Thread]
        D --> H[Cleanup Thread]
        
        C --> I[Cleanup Loop]
        C --> J[Monitoring Loop]
    end
    
    subgraph "API Service Process"
        K[recording_api_service.py]
        K --> L[FastAPI Application]
        L --> M[Health Endpoints]
        L --> N[Status Endpoints]
        L --> O[Storage Endpoints]
    end
    
    subgraph "Storage Layer"
        P[File System]
        P --> Q[Video Segments]
        P --> R[SQLite Databases]
        P --> S[Configuration Files]
    end
    
    F --> Q
    G --> Q
    G --> R
    I --> Q
    I --> R
    
    M --> R
    N --> R
    O --> P
```

---

**Note:** These flowcharts represent the actual implemented system behavior based on the production code running since July 26, 2025.