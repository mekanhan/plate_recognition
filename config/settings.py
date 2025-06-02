# config/settings.py

# Validation settings
MIN_OCR_CONFIDENCE = 0.3
MATCH_THRESHOLD = 0.8
USE_KNOWN_PLATES_DB = True

# Database settings
KNOWN_PLATES_FILE = "data/known_plates.json"
RESULTS_OUTPUT_DIR = "data/license_plates"

# Processing settings
BATCH_SIZE = 10
PROCESS_INTERVAL = 0.5  # seconds