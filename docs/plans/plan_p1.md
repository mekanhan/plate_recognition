# Feature Plan: Phase1

## Summary
Integrate license plate recognition overlay feature into the Node.js frontend using data streamed from the FastAPI backend.

## Goals
- Display live video stream from FastAPI
- Overlay detected license plates on the video feed
- Check plate eligibility from the DB
- Trigger gate signal if match is valid
- Log detection events, eligibility, and gate status to DB

## Files
- `lpr/overlay.py` — handles visual overlay drawing
- `lpr/processor.py` — processes frame and plate results
- `frontend/components/Overlay.tsx` — displays video and overlays

## API Contracts
- `GET /lpr/stream` — MJPEG video stream
- `GET /lpr/results` — latest plate recognition results (JSON)
- `POST /gate/open` — trigger gate opening

## Database Schema
Table: `entry_logs`
| column         | type       | description                |
|----------------|------------|----------------------------|
| id             | UUID       | unique identifier          |
| plate_number   | TEXT       | recognized plate           |
| camera_id      | TEXT       | source camera              |
| timestamp      | TIMESTAMP  | when it was detected       |
| authorized     | BOOLEAN    | was it in allowlist?       |
| gate_status    | TEXT       | opened / denied / timeout  |
