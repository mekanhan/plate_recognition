# LPR System Documentation

Welcome to the License Plate Recognition (LPR) system documentation. This documentation is organized by topic for easy navigation.

## 📋 Quick Links

- [Main System README](../README.md) - Getting started and system overview
- [Development Guidelines](../CLAUDE.md) - Core principles and testing requirements
- [Service Management Guide](guides/deployment/service-management.md) - Service control and monitoring

## 📁 Documentation Structure

### 🏗️ System Documentation
Core system components and functionality:

- **[system/detection/](system/detection/)** - License plate detection system
  - [detection-system.md](system/detection/detection-system.md) - Detection pipeline overview
  - [todo-detection.md](system/detection/todo-detection.md) - Detection system improvements needed
  
- **[system/video-recording/](system/video-recording/)** - Video recording and playback
  - [video-recording-guide.md](system/video-recording/video-recording-guide.md) - Recording system guide

- **[system/architecture/](system/architecture/)** - System architecture documentation
  - Architecture guides, pipeline documentation, and system design

### 💻 Development Documentation
Resources for developers:

- **[development/api/](development/api/)** - API documentation
  - [api-reference.md](development/api/api-reference.md) - API endpoints and usage
  - API guides and endpoint documentation

- **[development/testing/](development/testing/)** - Testing resources
  - Testing guides, scenarios, and test data

- **[development/development-notes.md](development/development-notes.md)** - Development notes and decisions

### 📖 User Guides
Operational and deployment guides:

- **[guides/deployment/](guides/deployment/)** - Deployment and service management
  - [service-management.md](guides/deployment/service-management.md) - Service control scripts and commands

- **[guides/troubleshooting/](guides/troubleshooting/)** - Troubleshooting resources

- **[guides/validation-steps.md](guides/validation-steps.md)** - System validation procedures

### 🔧 Utilities & Tools
Supporting documentation:

- **[performance/](performance/)** - Performance optimization guides
- **[prompt-engineering/](prompt-engineering/)** - AI/ML prompt engineering resources
- **[next-steps/](next-steps/)** - Future development plans

### 📚 Archive
Historical documentation kept for reference:

- **[archive/](archive/)** - Archived documentation
  - [archive/README.md](archive/README.md) - Archive index and policies

## 🎯 Getting Started

1. **New to the system?** Start with the [main README](../README.md)
2. **Setting up development?** Check [CLAUDE.md](../CLAUDE.md) for development guidelines
3. **Running services?** See the [service management guide](guides/deployment/service-management.md)
4. **Troubleshooting issues?** Check [guides/troubleshooting/](guides/troubleshooting/)

## 📝 Documentation Conventions

### File Naming
- Use lowercase with hyphens: `my-document.md`
- Be descriptive: `camera-setup-guide.md` not `setup.md`
- Use consistent suffixes: `-guide.md`, `-reference.md`, `-overview.md`

### Directory Structure
- Group by topic/function, not file type
- Keep depth reasonable (max 3 levels preferred)
- Use clear, descriptive directory names

### Content Guidelines
- Start with overview/purpose
- Include practical examples
- Link to related documentation
- Keep information current and accurate

## 🔄 Maintenance

This documentation is actively maintained. If you find:
- Outdated information
- Broken links
- Missing documentation
- Unclear instructions

Please update the relevant files or create an issue.

## 📊 Status

- ✅ **Phase 1 Complete**: Archived historical documentation
- ✅ **Phase 2 Complete**: Reorganized by topic, standardized naming
- 🔄 **Phase 3 In Progress**: Content validation and accuracy review