# Archive Directory - LPR Architecture Transformation

This directory contains archived files from the License Plate Recognition system's transformation from **edge device architecture** to **centralized processing architecture**.

## 📁 Directory Structure

### `edge_architecture_v1/`
Contains the complete edge device implementation that was replaced by the centralized system.

**Key Features of Edge Architecture:**
- Single camera per edge device
- Local processing with cloud synchronization
- Device registration and identity management
- Offline-first operation with batch sync
- Background processing for autonomous operation

**Archived Components:**
- `app/main.py` - Edge device main application with sync services
- `app/models.py` - Edge data models with sync queue and device config
- `app/services/` - Edge-specific services (device, sync, background processing)
- `app/routers/` - Edge API endpoints (headless, sync)
- `config/` - Edge device configuration and settings
- `tests/` - Edge-specific test files
- `docs/` - Edge device setup and deployment documentation

### `migration_data/`
Contains edge device data files and configuration that may need migration.

**Files:**
- `device.key` - Edge device authentication key
- `device_config.json` - Device identity and configuration
- `application_state.json` - Edge device application state

## 🔄 Architecture Transformation

### What Changed

| Aspect | Edge Architecture (Archived) | Centralized Architecture (Current) |
|--------|------------------------------|-----------------------------------|
| **Processing Model** | Distributed edge processing | Centralized processing unit |
| **Camera Support** | Single camera per device | Multiple IP cameras |
| **Data Flow** | Local → Cloud sync | Direct centralized processing |
| **Deployment** | Multiple edge devices | Single central server |
| **Database** | Local SQLite + sync | Centralized multi-tenant database |
| **Management** | Cloud-based device management | Direct web UI management |

### Key Benefits of Transformation

1. **Simplified Deployment**: Single central unit vs multiple edge devices
2. **Better Resource Utilization**: Centralized GPU processing vs distributed CPU
3. **Unified Management**: Single web interface for all cameras
4. **Scalability**: Easier to add cameras without new hardware
5. **Maintenance**: Centralized updates and monitoring

## 📝 Migration Guide

### For Users Upgrading from Edge to Centralized

1. **Data Migration**: 
   - Export detection data from edge devices
   - Import into centralized database with location mapping

2. **Camera Configuration**:
   - Convert edge device camera configs to IP camera configs
   - Group cameras by physical location

3. **User Management**:
   - Migrate from cloud-based user management to local user accounts
   - Map device access permissions to location-based permissions

### Code Migration

If you need to reference edge implementation:

```python
# Edge Architecture (Archived)
from app.services.device_service import DeviceService
from app.services.sync_service import SyncService

# Centralized Architecture (Current)  
from app.services.multi_camera_service import MultiCameraService
from app.services.location_service import LocationService
from app.services.camera_registry_service import CameraRegistryService
```

## 🗓️ Archive Information

- **Archive Date**: January 2025
- **Edge Architecture Version**: v1.x
- **Centralized Architecture Version**: v2.x
- **Reason for Archive**: Architecture transformation from edge to centralized processing

## ⚠️ Important Notes

1. **Do Not Use Archived Files**: These files are for reference only and are not compatible with the current centralized system.

2. **No Support**: The edge architecture is no longer maintained or supported.

3. **Security**: Archived device keys and credentials should be considered compromised and not reused.

4. **Testing**: Archived test files are not compatible with the current system architecture.

## 📞 Support

For questions about the architecture transformation or migration assistance:
- Review current documentation in `/docs/`
- Check migration scripts in `/scripts/migration/`
- Refer to centralized architecture documentation

---

**LPR System - Centralized Architecture v2.x**  
*Archived Edge Architecture v1.x - January 2025*