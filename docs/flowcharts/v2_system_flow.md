# V2 System Workflow - License Plate Recognition

**Version:** 2.0  
**Last Updated:** 2025-06-10  
**Authors:** Development Team  

## Overview

This document presents the enhanced workflow diagrams for the V2 License Plate Recognition System, illustrating the improved data flow, video recording pipeline, and dual storage architecture.

## Main System Workflow

```mermaid
graph TB
    subgraph "Camera Input"
        A[Camera Service] --> B[Raw Frame Capture]
        B --> C[Frame Timestamp]
    end
    
    subgraph "Frame Processing Pipeline"
        C --> D[Frame Counter++]
        D --> E{Process Every 5th Frame?}
        E -->|Yes| F[Detection Service V2]
        E -->|No| G[Raw Frame to Buffer]
    end
    
    subgraph "Detection Processing"
        F --> H[YOLO License Plate Detection]
        H --> I[EasyOCR Text Recognition]
        I --> J[Enhanced Text Processing]
        J --> K[Character Confusion Correction]
        K --> L[State-Specific Validation]
        L --> M[Confidence Calculation]
    end
    
    subgraph "Overlay Generation"
        M --> N[Color-Code by Confidence]
        N --> O{Confidence Level}
        O -->|≥80%| P[Green Bounding Box]
        O -->|60-79%| Q[Yellow Bounding Box]
        O -->|<60%| R[Red Bounding Box]
        P --> S[Add Confidence Text]
        Q --> S
        R --> S
        S --> T[System Metrics Overlay]
        T --> U[Annotated Frame Ready]
    end
    
    subgraph "Storage Pipeline"
        U --> V[Composite Detection Repository]
        V --> W[SQL Repository Write]
        V --> X[JSON Repository Write]
        W --> Y[(SQLite Database)]
        X --> Z[(JSON Files)]
    end
    
    subgraph "Video Recording"
        U --> AA[Video Recording Service]
        G --> AB[Frame Buffer]
        AB --> AC[5-Second Rolling Buffer]
        U --> AD{High Confidence Detection?}
        AD -->|Yes| AE[Trigger Recording]
        AE --> AF[Write Pre-event Frames]
        AF --> AG[Record Live Frames]
        AG --> AH[Continue 15 Seconds]
        AH --> AI[Finalize MP4 File]
        AI --> AJ[(Video Files)]
    end
    
    subgraph "Enhancement Pipeline"
        U --> AK[Enhancement Service]
        AK --> AL[Known Plates Matching]
        AL --> AM[Confidence Boosting]
        AM --> AN[Enhanced Result]
        AN --> AO[Composite Enhancement Repository]
        AO --> AP[SQL Enhancement Write]
        AO --> AQ[JSON Enhancement Write]
        AP --> AR[(Enhanced SQLite)]
        AQ --> AS[(Enhanced JSON)]
    end
    
    subgraph "Stream Output"
        U --> AT[Stream Router V2]
        AT --> AU[MJPEG Encoding]
        AU --> AV[Web Browser Display]
    end
    
    subgraph "API Endpoints"
        Y --> AW[V2 Results API]
        Z --> AW
        AR --> AX[V2 Enhanced Results API]
        AS --> AX
        AJ --> AY[V2 Video API]
        AW --> AZ[Web UI]
        AX --> AZ
        AY --> AZ
    end
```

## Detection Processing Detail Flow

```mermaid
graph TB
    A[Raw Frame Input] --> B[YOLO Model Processing]
    B --> C[Bounding Box Detection]
    C --> D{License Plate Found?}
    
    D -->|No| E[Return Raw Frame]
    D -->|Yes| F[Extract Plate ROI]
    
    F --> G[EasyOCR Processing]
    G --> H[Text Elements with Bounding Boxes]
    H --> I[Size-Based Filtering]
    
    subgraph "Enhanced Text Processing"
        I --> J[Remove State Names]
        J --> K[Remove Dealer Text]
        K --> L[Remove State Slogans]
        L --> M[Score Text Elements]
        M --> N[Select Best Candidate]
    end
    
    subgraph "Text Scoring Algorithm"
        N --> O[Base OCR Confidence: 40%]
        O --> P[Size Bonus: 30%]
        P --> Q[Position Bonus: 15%]
        Q --> R[Length Bonus: 15%]
        R --> S[Pattern Match: 20%]
        S --> T[Character Mix: 10%]
        T --> U[Final Score]
    end
    
    subgraph "Character Correction"
        U --> V[Apply Confusion Matrix]
        V --> W{Texas Plate?}
        W -->|Yes| X[Texas-Specific Rules]
        W -->|No| Y[General Corrections]
        X --> Z[Corrected Text]
        Y --> Z
    end
    
    subgraph "Validation"
        Z --> AA[Pattern Validation]
        AA --> BB[State Pattern Check]
        BB --> CC[Length Validation]
        CC --> DD[Character Composition]
        DD --> EE[Final Confidence]
    end
    
    subgraph "Overlay Creation"
        EE --> FF[Calculate Average Confidence]
        FF --> GG{Confidence Threshold}
        GG -->|≥80%| HH[Green Color: #00FF00]
        GG -->|60-79%| II[Yellow Color: #FFFF00]
        GG -->|<60%| JJ[Red Color: #FF0000]
        HH --> KK[Draw Bounding Box]
        II --> KK
        JJ --> KK
        KK --> LL[Add Text: 'TX: ABC123 (87%/92%)']
        LL --> MM[Add Background Rectangle]
        MM --> NN[Annotated Frame Output]
    end
```

## Video Recording Workflow

```mermaid
graph TB
    subgraph "Continuous Operation"
        A[Camera Frames] --> B[Frame Buffer Service]
        B --> C[5-Second Rolling Buffer]
        C --> D[Buffer Management]
        D --> E{Buffer Full?}
        E -->|Yes| F[Remove Oldest Frame]
        E -->|No| G[Add New Frame]
        F --> G
        G --> C
    end
    
    subgraph "Detection Trigger"
        H[License Plate Detected] --> I{Confidence Check}
        I -->|≥ Threshold| J[Trigger Recording Event]
        I -->|< Threshold| K[Continue Buffering]
        K --> C
    end
    
    subgraph "Recording Process"
        J --> L[Create Video File Path]
        L --> M[Initialize MP4V Writer]
        M --> N[Write Buffer Frames]
        N --> O[Start Live Recording]
        O --> P[Add System Overlays]
        P --> Q[Write Annotated Frames]
        Q --> R{15 Seconds Elapsed?}
        R -->|No| S[Continue Recording]
        S --> P
        R -->|Yes| T[Finalize Video File]
    end
    
    subgraph "Metadata Management"
        T --> U[Calculate Video Duration]
        U --> V[Get File Size]
        V --> W[Update Database Record]
        W --> X[Link to Detection ID]
        X --> Y[Mark Recording Complete]
    end
    
    subgraph "File Management"
        Y --> Z[Verify File Integrity]
        Z --> AA[WSL Path Compatibility]
        AA --> BB[File System Sync]
        BB --> CC[Video Available for Playback]
    end
    
    subgraph "Concurrent Operations"
        CC --> DD{New Detection During Recording?}
        DD -->|Yes| EE[Extend Recording Duration]
        DD -->|No| FF[Complete Current Recording]
        EE --> GG[Add Detection ID to Metadata]
        GG --> H1[Reset 15-Second Timer]
        H1 --> P
        FF --> Y
    end
```

## Dual Storage Architecture Flow

```mermaid
graph TB
    subgraph "Data Input"
        A[Detection Result] --> B[Composite Repository]
        C[Enhanced Result] --> D[Composite Enhancement Repository]
    end
    
    subgraph "Parallel Storage Processing"
        B --> E[SQL Detection Repository]
        B --> F[JSON Detection Repository]
        D --> G[SQL Enhancement Repository]
        D --> H[JSON Enhancement Repository]
    end
    
    subgraph "SQL Storage Path"
        E --> I[Validate Data Schema]
        I --> J[Create SQLAlchemy Model]
        J --> K[Async Database Session]
        K --> L[Execute INSERT Query]
        L --> M[Commit Transaction]
        M --> N[(SQLite Database)]
        
        G --> O[Validate Enhancement Schema]
        O --> P[Create Enhancement Model]
        P --> Q[Async Enhancement Session]
        Q --> R[Execute Enhancement INSERT]
        R --> S[Commit Enhancement Transaction]
        S --> T[(SQLite Enhancement Tables)]
    end
    
    subgraph "JSON Storage Path"
        F --> U[Load Session File]
        U --> V[Add to Detections Array]
        V --> W[Generate Session Metadata]
        W --> X[Atomic File Write]
        X --> Y[Filesystem Sync]
        Y --> Z[(JSON Detection Files)]
        
        H --> AA[Load Enhancement Session]
        AA --> BB[Add to Enhanced Results Array]
        BB --> CC[Update Enhancement Metadata]
        CC --> DD[Atomic Enhancement Write]
        DD --> EE[Enhancement Filesystem Sync]
        EE --> FF[(JSON Enhancement Files)]
    end
    
    subgraph "Error Handling"
        N --> GG{SQL Success?}
        Z --> HH{JSON Success?}
        T --> II{Enhancement SQL Success?}
        FF --> JJ{Enhancement JSON Success?}
        
        GG -->|No| KK[Log SQL Error]
        HH -->|No| LL[Log JSON Error]
        II -->|No| MM[Log Enhancement SQL Error]
        JJ -->|No| NN[Log Enhancement JSON Error]
        
        GG -->|Yes| OO[Success Logged]
        HH -->|Yes| OO
        II -->|Yes| PP[Enhancement Success Logged]
        JJ -->|Yes| PP
    end
    
    subgraph "Data Retrieval"
        QQ[API Request] --> RR{Primary: SQL Available?}
        RR -->|Yes| SS[Query SQLite]
        RR -->|No| TT[Fallback to JSON]
        SS --> UU[Return SQL Results]
        TT --> VV[Parse JSON Files]
        VV --> WW[Return JSON Results]
        UU --> XX[API Response]
        WW --> XX
    end
```

## Service Factory Initialization Flow

```mermaid
graph TB
    subgraph "Application Startup"
        A[main_v2.py Start] --> B[Load Configuration]
        B --> C[Create Service Factory]
        C --> D[Set Factory Config]
    end
    
    subgraph "Repository Creation"
        D --> E[Create Detection Repository]
        E --> F[Initialize SQL Detection Repo]
        F --> G[Initialize JSON Detection Repo]
        G --> H[Create Composite Detection Repo]
        
        H --> I[Create Enhancement Repository]
        I --> J[Initialize SQL Enhancement Repo]
        J --> K[Initialize JSON Enhancement Repo]
        K --> L[Create Composite Enhancement Repo]
        
        L --> M[Create Video Repository]
        M --> N[Initialize SQL Video Repo]
    end
    
    subgraph "Service Creation"
        N --> O[Create Camera Service]
        O --> P[Create License Plate Detector]
        P --> Q[Create Enhancer Service]
        Q --> R[Create Video Recording Service]
        R --> S[Create Detection Service V2]
    end
    
    subgraph "Dependency Injection"
        S --> T[Inject Camera into Detection Service]
        T --> U[Inject Detector into Detection Service]
        U --> V[Inject Repositories into Detection Service]
        V --> W[Inject Enhancer into Detection Service]
        W --> X[Inject Video Service into Detection Service]
    end
    
    subgraph "Service Initialization"
        X --> Y[Initialize All Services]
        Y --> Z[Verify Dependencies]
        Z --> AA[Start Background Tasks]
        AA --> BB[Set App State Services]
    end
    
    subgraph "Router Configuration"
        BB --> CC[Configure V2 Routers]
        CC --> DD[Set Router Dependencies]
        DD --> EE[Enable V1 Compatibility]
        EE --> FF[Start FastAPI Application]
    end
    
    subgraph "Ready State"
        FF --> GG[System Ready]
        GG --> HH[Accept API Requests]
        HH --> II[Process Video Stream]
        II --> JJ[Handle Detection Events]
    end
```

## Performance Optimization Flow

```mermaid
graph TB
    subgraph "Frame Rate Management"
        A[30 FPS Camera Input] --> B[Frame Counter]
        B --> C{Frame % 5 == 0?}
        C -->|Yes| D[Process Frame]
        C -->|No| E[Skip Processing]
        E --> F[Direct to Stream]
        D --> G[Detection Pipeline]
    end
    
    subgraph "Processing Optimization"
        G --> H[Async Task Creation]
        H --> I[0.5 Second Timeout]
        I --> J{Processing Complete?}
        J -->|Yes| K[Use Processed Frame]
        J -->|No| L[Timeout - Use Raw Frame]
        K --> M[Calculate Processing Time]
        L --> N[Log Timeout Warning]
        M --> O[Update Performance Metrics]
        N --> O
    end
    
    subgraph "Memory Management"
        O --> P[Frame Buffer Management]
        P --> Q{Buffer > 75 Frames?}
        Q -->|Yes| R[Remove Oldest Frames]
        Q -->|No| S[Add New Frame]
        R --> S
        S --> T[Monitor Memory Usage]
    end
    
    subgraph "Storage Optimization"
        T --> U[Batch Detection Writes]
        U --> V[Async Parallel Storage]
        V --> W[SQL Write Task]
        V --> X[JSON Write Task]
        W --> Y[Await Both Tasks]
        X --> Y
        Y --> Z[Storage Complete]
    end
    
    subgraph "Video Optimization"
        Z --> AA[MP4V Codec Selection]
        AA --> BB[15 FPS Recording Rate]
        BB --> CC[Compress Video Stream]
        CC --> DD[Monitor File Size]
        DD --> EE[Cleanup Old Videos]
    end
```

## Error Handling and Recovery Flow

```mermaid
graph TB
    subgraph "Detection Errors"
        A[Detection Failure] --> B{Error Type}
        B -->|Model Load Error| C[Fallback to Placeholder]
        B -->|OCR Error| D[Skip Text Recognition]
        B -->|Timeout Error| E[Use Raw Frame]
        C --> F[Log Error Details]
        D --> F
        E --> F
    end
    
    subgraph "Storage Errors"
        G[Storage Failure] --> H{Storage Type}
        H -->|SQL Error| I[Continue with JSON]
        H -->|JSON Error| J[Continue with SQL]
        H -->|Both Failed| K[Cache in Memory]
        I --> L[Retry SQL Later]
        J --> M[Retry JSON Later]
        K --> N[Attempt Recovery]
    end
    
    subgraph "Video Recording Errors"
        O[Video Error] --> P{Error Category}
        P -->|Codec Error| Q[Try Alternative Codec]
        P -->|File Path Error| R[Use Fallback Directory]
        P -->|Write Error| S[Skip Current Frame]
        Q --> T[Continue Recording]
        R --> T
        S --> T
    end
    
    subgraph "Recovery Mechanisms"
        F --> U[Health Check]
        L --> U
        M --> U
        T --> U
        U --> V{System Healthy?}
        V -->|Yes| W[Continue Operation]
        V -->|No| X[Restart Services]
        X --> Y[Reinitialize Components]
        Y --> Z[Resume Normal Operation]
        W --> AA[Monitor Performance]
        Z --> AA
    end
```

This comprehensive workflow documentation provides a detailed view of the V2 system's enhanced capabilities, showing how the various components interact to provide robust license plate recognition with advanced video recording and dual storage features.