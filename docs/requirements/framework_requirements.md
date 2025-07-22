# Framework Requirements

This document defines the framework requirements, coding standards, and architectural guidelines for the LPR System project.

## Project Structure

lpr-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── cameras.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── models/
│   │   │   │   └── camera.py
│   │   │   └── session.py
│   │   ├── schemas/
│   │   │   └── camera.py
│   │   ├── services/
│   │   │   └── camera_service.py
│   │   └── main.py
│   ├── tests/
│   │   └── test_cameras.py
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── cameras/
│   │   │   │   ├── CameraList.js
│   │   │   │   ├── CameraCard.js
│   │   │   │   ├── CameraModal.js
│   │   │   │   └── CameraFilters.js
│   │   │   └── layout/
│   │   │       ├── Sidebar.js
│   │   │       └── Header.js
│   │   ├── pages/
│   │   │   └── CamerasPage.js
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── styles/
│   │   └── utils/
│   ├── package.json
│   └── README.md
└── docs/
    ├── architecture/
    │   ├── backend.md
    │   └── frontend.md
    ├── features/
    │   └── camera_management.md
    └── api/
        └── cameras.md


## Backend (FastAPI)

- **Python**: 3.10+
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT with OAuth2
- **Conventions**:
  - Follow PEP 8
  - Use type hints
  - Document with Google-style docstrings
  - Structure models as Base/Create/Update/Response
  - Implement proper error handling
  - Use dependency injection

## Frontend (React)

- **JavaScript**: ES6+ with React 18
- **State**: React Context/Hooks
- **Styling**: CSS Modules
- **Conventions**:
  - Component-based architecture
  - Functional components with hooks
  - Prop validation
  - Consistent file structure
  - Responsive design

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