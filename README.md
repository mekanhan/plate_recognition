● Here's how to run the backend and frontend for the LPR system:

  🚀 Running the LPR System

  Step 1: Start the Backend API Server

  Open a terminal and run:

  cd /home/mekanhan/github/learning/plate_recognition

  # Activate virtual environment (if you created one)
  source venv/bin/activate  # On Linux/Mac
  # or
  venv\Scripts\activate     # On Windows

  # Start the backend API
  python -m api.main

  You should see:
  INFO:     Started server process [xxxxx]
  INFO:     Waiting for application startup.
  INFO:     LPR System started successfully
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

  ✅ Backend is now running at: http://localhost:8000

  Step 2: Start the Frontend Server

  Open a new terminal (keep the backend running) and run:

  cd /home/mekanhan/github/learning/plate_recognition/frontend

  # Start a simple HTTP server
  python3 -m http.server 8080

  You should see:
  Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...

  ✅ Frontend is now running at: http://localhost:8080

  Step 3: Access the System

  Open your web browser and go to:

  1. Frontend Dashboard: http://localhost:8080
  2. API Documentation: http://localhost:8000/docs

  📋 Quick Commands Summary

  # Terminal 1 - Backend
  cd /home/mekanhan/github/learning/plate_recognition
  python -m api.main

  # Terminal 2 - Frontend  
  cd /home/mekanhan/github/learning/plate_recognition/frontend
  python3 -m http.server 8080

  # Terminal 3 - Testing (optional)
  cd /home/mekanhan/github/learning/plate_recognition
  python test_api.py

  🔍 What You Should See

  In the Backend Terminal:

  - Startup messages
  - Camera connection logs
  - Detection logs (when plates are detected)
  - API request logs

  In the Frontend (Browser):

  - Camera cards showing snapshots (updating every 5 seconds)
  - NO video streams (just images)
  - "Open in VLC" buttons for live viewing
  - Detection history
  - Analytics dashboard

  🛠️ Troubleshooting

  If Backend Won't Start:

  # Check if port 8000 is already in use
  lsof -i :8000  # Linux/Mac
  netstat -ano | findstr :8000  # Windows

  # Use a different port
  python -m api.main --port 8001

  If Frontend Won't Start:

  # Check if port 8080 is already in use
  lsof -i :8080  # Linux/Mac

  # Use a different port
  python3 -m http.server 8081

  If Dependencies are Missing:

  pip install -r requirements.txt

  🎯 Alternative: Use the Startup Helper

  I created a helper script that shows all the commands:

  python start_system.py

  This will:
  1. Check dependencies
  2. Show you exactly what commands to run
  3. Optionally start the API for you

  📌 Important Notes

  1. Keep both terminals open - Backend and frontend need to run simultaneously
  2. Camera snapshots - Will show offline image if no cameras configured
  3. Configure cameras - Edit config/cameras.yaml with your camera details
  4. Check logs - Backend terminal shows all processing activity
  5. No video in browser - Use VLC for live video viewing

  The system is designed to:
  - Show snapshots in browser (not video)
  - Process video locally on the server
  - Store detection results in database
  - Provide VLC integration for live viewing