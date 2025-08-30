# User Guides

Operational guides for deploying, managing, and troubleshooting the LPR system.

## 📁 Directory Contents

### Deployment & Management
- **[deployment/](deployment/)** - Deployment and service management guides
  - [service-management.md](deployment/service-management.md) - Service control scripts and commands
  - Production deployment procedures and configurations

### Troubleshooting
- **[troubleshooting/](troubleshooting/)** - Issue resolution guides
  - [postman-troubleshooting.md](troubleshooting/postman-troubleshooting.md) - API testing troubleshooting
  - Common issues and their solutions

### Validation & Testing
- **[validation-steps.md](validation-steps.md)** - System validation procedures and checklists

## 🚀 Quick Start

### For System Administrators
1. **Service Management**: [deployment/service-management.md](deployment/service-management.md)
2. **Validation**: [validation-steps.md](validation-steps.md)
3. **Troubleshooting**: [troubleshooting/](troubleshooting/)

### For Support Personnel
1. **Common Issues**: Check [troubleshooting/](troubleshooting/) first
2. **System Validation**: Use [validation-steps.md](validation-steps.md) procedures
3. **Service Control**: Reference [deployment/service-management.md](deployment/service-management.md)

## 🛠️ Essential Commands

Quick reference for common tasks:

```bash
# Service management
python3 bin/start_lpr.py          # Start all services
python3 bin/check_services.py     # Health check
python3 bin/stop_all_services.py  # Stop all services

# System validation
curl http://localhost:8001/api/system/health
curl http://localhost:8002/health
```

## 🆘 Emergency Procedures

1. **Service Issues**: Use [deployment/service-management.md](deployment/service-management.md)
2. **API Problems**: Check [troubleshooting/postman-troubleshooting.md](troubleshooting/postman-troubleshooting.md)
3. **Complete System Reset**: Follow [validation-steps.md](validation-steps.md)

## 📝 Maintenance Guidelines

**Update guides when:**
- New deployment procedures are established
- Service management changes are implemented
- Common issues are identified and resolved
- System validation procedures change

**Review frequency:** After each deployment or when new operational issues are discovered