# Project Folder Organization Plan

## Current Issues Identified

### 1. Root Directory Clutter
- Multiple test HTML files in root (`test_*.html`)
- Scattered markdown files
- Demo files in root

### 2. Duplicate/Nested Directories
- `recording_service/recording_service/` (nested)
- `recordings/` at root and `recording_service/recordings/`
- `logs/` and `recording_service/logs/`

### 3. Inconsistent Structure
- Mixed API versions (`api/v1/`, `api/v3/`, `api/routes/`, `api/endpoints/`)
- Storage scattered across multiple locations
- Test files in multiple locations

## Proposed Organization Structure

```
plate_recognition/
├── src/                          # Main source code
│   ├── api/                      # API layer
│   │   ├── v3/                   # Current v3 API
│   │   ├── legacy/               # v1/v2 endpoints (deprecated)
│   │   └── shared/               # Shared API utilities
│   ├── services/                 # Business logic services
│   │   ├── recording/            # Recording service
│   │   ├── detection/            # Detection service
│   │   └── camera/               # Camera management
│   ├── models/                   # Data models
│   ├── database/                 # Database layer
│   └── utils/                    # Shared utilities
├── frontend/                     # Web interface (keep as is)
├── ai_features/                  # AI/ML components (keep as is)
├── tests/                        # Test suite (organized)
│   ├── unit/
│   ├── integration/
│   ├── functional/
│   ├── fixtures/
│   └── demo/                     # Demo HTML files
├── config/                       # Configuration files
├── data/                         # Persistent data
│   ├── database/                 # Database files
│   ├── recordings/               # Video recordings
│   ├── detections/               # Detection images
│   └── backups/                  # Backup files
├── logs/                         # All log files
├── scripts/                      # Utility scripts
│   ├── deployment/
│   ├── maintenance/
│   └── development/
├── docs/                         # Documentation (organized)
│   ├── api/                      # API documentation
│   ├── deployment/               # Deployment guides
│   ├── development/              # Development guides
│   └── system/                   # System documentation
├── tools/                        # Development tools
├── bin/                          # Executable scripts
└── deployment/                   # Deployment configs
```

## Migration Steps

### Phase 1: Root Directory Cleanup
1. Move test HTML files to `tests/demo/`
2. Organize markdown files in `docs/`
3. Move utility scripts to `scripts/`

### Phase 2: Service Consolidation
1. Flatten `recording_service/recording_service/`
2. Consolidate recording directories
3. Merge log directories

### Phase 3: API Organization
1. Move legacy API endpoints to `api/legacy/`
2. Keep v3 as primary in `api/v3/`
3. Create shared API utilities

### Phase 4: Data Organization
1. Consolidate all recordings under `data/recordings/`
2. Move detection images to `data/detections/`
3. Organize database files in `data/database/`

## Benefits

1. **Clear Separation**: Source code, data, tests, docs clearly separated
2. **Version Control**: Clean API versioning strategy
3. **Maintainability**: Easier to find and modify components
4. **Scalability**: Structure supports future growth
5. **Development**: Better development experience
6. **Deployment**: Cleaner deployment structure