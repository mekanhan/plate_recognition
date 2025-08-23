Recommended Implementation: Recordings-First Approach
Why Recordings Should Come First

Data Persistence: Recordings are the actual data that users want to access. Cameras are just metadata about the source.
Orphaned Recordings: When a camera is deleted, its recordings still exist on disk but become inaccessible through a camera-first approach.
Historical Accuracy: Users need to view footage from cameras that may no longer exist in the system.
Storage Management: Administrators need visibility into all storage usage, including orphaned recordings.

Recommended Architecture
1. Query Available Recordings (First)
   ├── Scan filesystem for all recording directories
   ├── Extract camera IDs from directory names
   └── Build recording inventory

2. Enrich with Camera Metadata (Second)
   ├── Match recordings to existing cameras
   ├── Mark orphaned recordings (deleted cameras)
   └── Provide fallback display names
Implementation Strategy
1. Recording Discovery Service
pythonclass RecordingDiscoveryService:
    def get_all_recording_sources(self):
        """
        Returns all cameras that have recordings,
        regardless of database status
        """
        sources = []
        for camera_dir in recordings_directory:
            camera_id = extract_camera_id(camera_dir)
            sources.append({
                'camera_id': camera_id,
                'has_recordings': True,
                'is_active': camera_exists_in_db(camera_id),
                'display_name': get_camera_name(camera_id) or f"Deleted Camera ({camera_id})",
                'recording_count': count_recordings(camera_dir),
                'date_range': get_date_range(camera_dir)
            })
        return sources
2. Playback UI Flow
User Opens Playback
    ↓
1. Load ALL Recording Sources
   - Active cameras with recordings ✓
   - Deleted cameras with recordings ✓
   - Show storage usage for each
    ↓
2. User Selects Camera(s)
   - Can select deleted cameras
   - Show warning icon for deleted
    ↓
3. Load Timeline/Calendar
   - Based on actual files
   - Not database records
3. API Endpoints to Modify
python# New endpoint
GET /api/recordings/sources
{
  "sources": [
    {
      "camera_id": "camera_946701d3",
      "display_name": "Front Entrance",
      "status": "active",
      "has_recordings": true,
      "storage_used_mb": 2048,
      "first_recording": "2025-01-01T00:00:00",
      "last_recording": "2025-08-22T14:30:00"
    },
    {
      "camera_id": "camera_deleted_123",
      "display_name": "Deleted Camera (camera_deleted_123)",
      "status": "deleted",
      "has_recordings": true,
      "storage_used_mb": 1024,
      "first_recording": "2025-01-15T00:00:00",
      "last_recording": "2025-08-20T23:50:00"
    }
  ]
}

# Modify existing endpoints to accept any camera_id
GET /api/recordings/cameras/{camera_id}/calendar
GET /api/recordings/cameras/{camera_id}/timeline
# Should work even if camera doesn't exist in database
Key Considerations

Storage Cleanup

Provide UI to identify and clean up orphaned recordings
Show storage usage per camera (active and deleted)
Allow bulk deletion of old recordings


Performance

Cache recording inventory (refresh periodically)
Use filesystem metadata for quick scanning
Implement pagination for large recording sets


User Experience

Clearly mark deleted cameras in UI
Show last known camera name if available
Provide filters: "Active Only", "Deleted Only", "All"


Data Integrity

Never auto-delete recordings when camera is deleted
Provide explicit "Delete Camera and Recordings" option
Log all deletion operations for audit trail



Benefits of This Approach

Complete Visibility: Users can access all recorded footage
Storage Management: Administrators can manage orphaned data
Forensic Capability: Historical footage remains accessible
Flexibility: Can handle cameras that go offline/online
Future-Proof: Works even if database is corrupted/lost

Implementation Priority

Phase 1: Modify recording service to scan filesystem
Phase 2: Update playback UI to show all sources
Phase 3: Add storage management features
Phase 4: Implement cleanup policies

This recordings-first approach ensures that your valuable video data is never lost due to metadata changes, while still providing a good user experience for accessing footage from both active and deleted cameras.