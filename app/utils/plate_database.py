import os
import json
import datetime
from typing import List, Dict, Any, Optional

class PlateDatabase:
    """Handler for the local plate database"""

    def __init__(self, db_file: str = "data/known_plates.json"):
        self.db_file = db_file
        self.plates: List[str] = []
        self.full_data: Dict[str, Any] = {}
        self._load_database()

    def _load_database(self) -> None:
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r") as f:
                    data = json.load(f)
                self.plates = [p["plate_number"] for p in data.get("plates", [])]
                self.full_data = data
            except (json.JSONDecodeError, KeyError):
                self.plates = []
                self.full_data = {"plates": [], "last_updated": datetime.datetime.now().strftime("%Y-%m-%d")}
        else:
            self.plates = ["VBR7660"]
            self.full_data = {
                "plates": [{"plate_number": "VBR7660", "first_seen": datetime.datetime.now().strftime("%Y-%m-%d"), "metadata": {}}],
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            self._save_database()

    def _save_database(self) -> None:
        self.full_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(self.db_file, "w") as f:
            json.dump(self.full_data, f, indent=2)

    def get_all_plates(self) -> List[str]:
        return self.plates

    def add_plate(self, plate_number: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        if plate_number in self.plates:
            return False
        self.full_data["plates"].append({
            "plate_number": plate_number,
            "first_seen": datetime.datetime.now().strftime("%Y-%m-%d"),
            "metadata": metadata or {}
        })
        self.plates.append(plate_number)
        self._save_database()
        return True

    def auto_add_high_confidence_plates(self, plate_text: str, confidence: float, min_confidence: float = 0.8) -> bool:
        if confidence >= min_confidence and plate_text not in self.plates:
            return self.add_plate(plate_text)
        return False
