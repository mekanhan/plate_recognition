# Framework Requirements

This document defines the framework requirements, coding standards, and architectural guidelines for the LPR System project.

## Project Structure

plate_recognition/
├── app/                    # FastAPI monolithic backend
│   ├── main.py            # FastAPI application entry
│   ├── database.py        # SQLAlchemy async database
│   ├── models.py          # Pydantic & SQLAlchemy models
│   ├── dependencies/      # Dependency injection
│   ├── factories/         # Service factories
│   ├── interfaces/        # Abstract base classes
│   ├── repositories/      # Data access layer
│   ├── routers/           # FastAPI route handlers
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── backend/               # Additional FastAPI structure (empty)
│   └── app/
│       ├── api/v1/endpoints/cameras.py
│       ├── core/
│       ├── db/models/
│       ├── schemas/
│       └── services/
├── frontend/
│   ├── src/
│   │   ├── app.js         # Main LPRApplication class
│   │   ├── components/    # Modular ES6 components
│   │   │   ├── cameras/
│   │   │   │   ├── CameraCard.js
│   │   │   │   ├── CameraFilters.js
│   │   │   │   ├── CameraList.js
│   │   │   │   └── CameraModal.js
│   │   │   ├── common/
│   │   │   │   ├── CameraSetupModal.js
│   │   │   │   └── Modal.js
│   │   │   └── layout/
│   │   │       ├── Header.js
│   │   │       └── Sidebar.js
│   │   ├── pages/         # Page components
│   │   │   ├── CamerasPage.js
│   │   │   ├── Dashboard.js
│   │   │   └── [other pages]
│   │   ├── services/
│   │   │   └── api.js
│   │   └── styles/
│   └── drafts/            # Legacy prototypes
├── data/                  # SQLite database & files
├── scripts/               # Python utility scripts
├── tests/                 # Test files
└── docs/

## Backend (FastAPI)

- **Framework**: FastAPI monolithic application
- **Database**: SQLite with async SQLAlchemy
- **Python**: 3.10+
- **Models**: YOLO (YOLOv11/v8) + EasyOCR
- **Conventions**:
  - Follow PEP 8
  - Use type hints
  - Async/await patterns
  - Service layer architecture
  - Repository pattern for data access

## Frontend (Vanilla JavaScript)

- **Framework**: None - Pure ES6+ with modules
- **Architecture**: Class-based SPA with component system
- **Main App**: LPRApplication class orchestrates all components
- **Styling**: CSS with component-specific stylesheets
- **Conventions**:
  - ES6 modules and classes
  - Component-based architecture
  - Event-driven communication
  - Responsive design
  - No build process - direct browser execution

## Development Practices

- **Version Control**: Git with feature branches
- **Testing**: Unit and integration tests required
- **Documentation**: Document code and APIs
- **Code Reviews**: Required for all changes
- **CI/CD**: Automated testing and deployment

## File Naming

- **Backend**: snake_case for files and functions
- **Frontend**: PascalCase for components, camelCase for functions
- **Documentation**: kebab-case for filenames

See additional documents for detailed coding standards and development workflow.