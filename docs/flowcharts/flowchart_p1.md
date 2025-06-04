# Logic Flow for Smart Gate LPR Overlay

```mermaid
flowchart TD
    Start --> CaptureFrame
    CaptureFrame --> DetectPlate
    DetectPlate --> SendPlateToNode
    SendPlateToNode --> CheckDB
    CheckDB -->|Valid| OpenGate
    CheckDB -->|Invalid| DenyAccess
    OpenGate --> LogEntry
    DenyAccess --> LogEntry
    LogEntry --> End
```

## Explanation:
- `CaptureFrame`: FastAPI reads camera feed.
- `DetectPlate`: Frame processed via ML model to extract license plate.
- `SendPlateToNode`: Result sent as JSON to Node.js service.
- `CheckDB`: Node.js compares plate with access table.
- `OpenGate` / `DenyAccess`: Decides physical gate action.
- `LogEntry`: Saves event to `entry_logs` table.
