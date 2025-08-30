# Development Documentation

Resources and guides for LPR system developers.

## 📁 Directory Contents

### API Documentation
- **[api/](api/)** - API reference and development guides
  - [api-reference.md](api/api-reference.md) - Complete API endpoint documentation
  - [LPR_System_API_Collection.postman_collection.json](api/LPR_System_API_Collection.postman_collection.json) - Postman collection for testing

### Testing Resources
- **[testing/](testing/)** - Testing guides, scenarios, and frameworks
  - Test scenarios, expected values, and testing methodologies
  - Camera testing and validation procedures

### Development Notes
- **[development-notes.md](development-notes.md)** - Development decisions, patterns, and lessons learned

## 🛠️ Quick Start for Developers

1. **API Development**: Start with [api/api-reference.md](api/api-reference.md)
2. **Testing**: Check [testing/](testing/) for test scenarios and procedures  
3. **Guidelines**: Review [../../CLAUDE.md](../../CLAUDE.md) for core development principles

## 🔧 Development Tools

### API Testing
- Import [api/LPR_System_API_Collection.postman_collection.json](api/LPR_System_API_Collection.postman_collection.json) into Postman
- Follow API testing guidelines in [api/](api/)

### Testing Framework
- Use test scenarios in [testing/](testing/)
- Follow testing checklist in [../../CLAUDE.md](../../CLAUDE.md)

## 📝 Maintenance Guidelines

**Update API documentation when:**
- New endpoints are added or modified
- Request/response formats change
- Authentication requirements change

**Update test documentation when:**
- New test scenarios are identified
- Test procedures are modified
- New testing tools are introduced

**Review frequency:** After each API change or monthly sprint review