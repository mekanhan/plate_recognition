# Camera ID System - Simple Solution Documentation

## Overview

This document outlines a simple, user-friendly solution for camera identification that maintains recording continuity across camera reconfigurations while avoiding complex hardware dependencies.

## Solution: Location-Based ID with User Override

### Core Concept
- Use a **stable identifier** that persists across camera reconfigurations
- Default to **location/name** but allow **manual override**
- Keep recording folders organized by this stable identifier
- Maintain internal dynamic IDs for database operations

### Implementation Components

#### 1. Camera Configuration Fields

**New Required Field:**
```
stable_camera_id: String (unique, persistent)
- Purpose: Folder name for recordings
- Format: Alphanumeric + underscores only
- Example: "front_door", "parking_lot_1", "warehouse_entrance"
```

**Existing Fields (unchanged):**
```
id: String (auto-generated, internal use)
name: String (display name)
ip_address: String
... other configuration fields ...
```

#### 2. ID Generation Logic

```
When creating a new camera:
1. IF user provides stable_camera_id:
   - Validate format (alphanumeric + underscores)
   - Check uniqueness
   - Use as provided
   
2. ELSE (auto-generate from name):
   - Take camera name
   - Convert to lowercase
   - Replace spaces with underscores
   - Remove special characters
   - Ensure uniqueness (append number if needed)
   
Example:
- Name: "Front Door Camera" → stable_camera_id: "front_door_camera"
- Name: "Parking Lot #1" → stable_camera_id: "parking_lot_1"
```

#### 3. Recording Folder Structure

```
recordings/
├── front_door/           # Using stable_camera_id
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── 15/
│   │   │   │   └── *.mp4
│   │   └── ...
│   └── metadata.json     # Camera history file
├── parking_lot_1/
│   └── ...
└── warehouse_entrance/
    └── ...
```

#### 4. Camera Metadata File

Each camera folder contains a `metadata.json` file tracking camera history:

```json
{
  "stable_camera_id": "front_door",
  "created_date": "2025-01-01T00:00:00Z",
  "camera_history": [
    {
      "camera_id": "camera_a171d280fdc7",
      "name": "Front Door Camera",
      "ip_address": "192.168.1.100",
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "added_date": "2025-01-01T00:00:00Z",
      "removed_date": "2025-01-10T00:00:00Z"
    },
    {
      "camera_id": "camera_b2c3d4e5f6g7",
      "name": "Front Door HD",
      "ip_address": "192.168.1.101",
      "mac_address": "11:22:33:44:55:66",
      "added_date": "2025-01-15T00:00:00Z",
      "removed_date": null
    }
  ]
}
```

### User Workflows

#### Adding a New Camera

1. **User enters camera details** (name, IP, credentials)
2. **System suggests stable ID** based on camera name
3. **User can accept or modify** the suggested ID
4. **System validates:**
   - Format correctness
   - Uniqueness (no existing folder with same ID)
5. **If ID exists:** System asks if user wants to:
   - Use existing recordings folder (camera replacement)
   - Create new folder with modified ID (new location)

#### Replacing a Camera

1. **User selects "Replace Camera"** option
2. **System shows list** of existing camera folders
3. **User selects** which camera they're replacing
4. **New camera uses** the same stable_camera_id
5. **Recording continuity maintained**

#### Viewing Archived Recordings

1. **Recordings page shows:**
   - Active cameras (currently configured)
   - Archived recordings (folders without active camera)
2. **Each entry displays:**
   - Folder name (stable_camera_id)
   - Recording date range
   - Storage used
   - Status (Active/Archived)

### UI Mockup Concepts

#### Camera Setup Form
```
┌─ Add New Camera ────────────────────────────┐
│                                             │
│ Camera Name: [Front Door Camera        ]   │
│                                             │
│ Recording Folder ID:                        │
│ [front_door_camera    ] ℹ️                  │
│ This ID determines where recordings are     │
│ saved. Use the same ID when replacing      │
│ this camera to keep recording history.      │
│                                             │
│ ⚠️ A folder with this ID already exists:    │
│ • 45 GB of recordings from 2024-01-01      │
│ • Last recording: 2025-01-10                │
│                                             │
│ ○ Continue using this folder               │
│ ○ Create new folder (will add number)      │
│                                             │
│ IP Address: [192.168.1.100        ]        │
│ Username:   [admin                ]        │
│ Password:   [••••••••             ]        │
│                                             │
│ [Cancel]                    [Save Camera]   │
└─────────────────────────────────────────────┘
```

#### Recordings List View
```
┌─ Cameras & Recordings ──────────────────────┐
│                                             │
│ 🟢 Active Cameras                           │
│ ┌─────────────────────────────────────────┐ │
│ │ 📹 Front Door Camera                    │ │
│ │ ID: front_door | 45 GB | 30 days       │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ 📹 Parking Lot Camera                   │ │
│ │ ID: parking_lot_1 | 120 GB | 30 days   │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ 📁 Archived Recordings                      │
│ ┌─────────────────────────────────────────┐ │
│ │ 📁 Warehouse Entrance (Removed)         │ │
│ │ ID: warehouse_entrance | 80 GB | 60 days│ │
│ │ Last recording: 2024-12-15              │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Database Schema Changes

#### cameras table
```sql
-- Add new column
ALTER TABLE cameras ADD COLUMN stable_camera_id VARCHAR(100) UNIQUE;

-- Add index for performance
CREATE INDEX idx_stable_camera_id ON cameras(stable_camera_id);
```

### Migration Strategy

#### For Existing Systems

1. **Add stable_camera_id column** to database
2. **Populate with normalized names** for existing cameras
3. **Create symbolic links** from old folders to new structure (optional)
4. **Update recording service** to use stable_camera_id
5. **Maintain backward compatibility** for 1-2 versions

#### Migration Script Logic
```
For each existing camera:
1. Generate stable_camera_id from camera name
2. Check if recording folder exists:
   - If camera_{dynamic_id} exists → link to new structure
   - If conflicts exist → append number
3. Update database record
4. Create metadata.json in recording folder
```

### Benefits

1. **Simple Implementation**: No complex hardware detection
2. **User Control**: Clear, predictable behavior
3. **Recording Continuity**: Maintains history across camera changes
4. **Backward Compatible**: Works with existing folder structure
5. **Future-Proof**: Can add hardware detection later if needed

### Limitations & Considerations

1. **Unique Names Required**: Users must use unique location names
2. **Manual Process**: Requires user to specify when replacing camera
3. **Name Changes**: Changing stable_camera_id requires folder migration

### Best Practices

1. **Naming Convention**: Encourage descriptive location names
   - Good: `front_entrance`, `loading_dock_north`
   - Avoid: `camera1`, `cam2`, `test`

2. **Documentation**: Provide clear user guides for:
   - Choosing good camera IDs
   - Replacing cameras
   - Managing archived recordings

3. **Validation**: Implement strict validation for stable_camera_id:
   - Minimum 3 characters
   - Maximum 50 characters
   - Only letters, numbers, underscores
   - Cannot start with number

### Future Enhancements

1. **Auto-Detection** (Phase 2):
   - Detect MAC address when available
   - Suggest existing folder if MAC matches

2. **Bulk Operations** (Phase 3):
   - Import/export camera configurations
   - Batch rename recording folders

3. **Recording Management** (Phase 4):
   - Archive old recordings
   - Transfer recordings between cameras
   - Merge recording folders

## Implementation Checklist

- [ ] Add `stable_camera_id` field to camera model
- [ ] Update camera creation form with ID field
- [ ] Implement ID validation and uniqueness check
- [ ] Modify recording service to use stable_camera_id
- [ ] Update recordings page to show all folders
- [ ] Add "Replace Camera" workflow
- [ ] Create metadata.json generation
- [ ] Write migration script for existing systems
- [ ] Update user documentation
- [ ] Add API endpoint for checking ID availability

## Summary

This simple solution provides a clean, user-friendly approach to camera identification that solves the recording fragmentation problem without introducing complex dependencies. It gives users control while maintaining system flexibility for future enhancements.