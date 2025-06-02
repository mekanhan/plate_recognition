#!/usr/bin/env python3
"""
enhance_plates.py - Automatic License Plate Enhancement

This script monitors the license plate detection files produced by lpr_live.py
and enhances the detection accuracy using validation techniques and a known plates database.

Usage:
  python enhance_plates.py --watch
  python enhance_plates.py --file path/to/detection.json
"""

import os
import json
import time
import difflib
import argparse
import datetime
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LicensePlateValidator:
    """Validates and improves license plate detection accuracy"""
    
    def __init__(self, known_plates=None):
        self.known_plates = known_plates or []
        # Common OCR substitution patterns
        self.substitutions = {
            '0': 'O', 'O': '0',
            '1': 'I', 'I': '1', 
            '8': 'B', 'B': '8',
            '5': 'S', 'S': '5',
            '2': 'Z', 'Z': '2',
            'D': '0', 'Q': '0',
            'U': 'V', 'V': 'U'
        }
        
    def add_known_plate(self, plate: str) -> None:
        """Add a known plate to the local DB"""
        if plate not in self.known_plates:
            self.known_plates.append(plate)
            
    def get_plate_variations(self, plate_text: str) -> List[str]:
        """Generate possible variations of a plate based on common OCR errors"""
        plate = plate_text.upper().strip()
        variations = [plate]
        
        # Generate variations with single character substitutions
        for i, char in enumerate(plate):
            if char in self.substitutions:
                new_plate = plate[:i] + self.substitutions[char] + plate[i+1:]
                variations.append(new_plate)
        
        return variations
    
    def calculate_similarity(self, plate1: str, plate2: str) -> float:
        """Calculate string similarity between two plate texts"""
        return difflib.SequenceMatcher(None, plate1, plate2).ratio()
    
    def match_with_known_plates(self, plate_text: str, threshold: float = 0.8) -> Tuple[Optional[str], float]:
        """Check if plate is similar to any known plate"""
        if not self.known_plates:
            return None, 0
            
        best_match = None
        best_score = 0
        
        # Check each variation of the input plate
        for variation in self.get_plate_variations(plate_text):
            for known_plate in self.known_plates:
                similarity = self.calculate_similarity(variation, known_plate)
                if similarity > best_score:
                    best_score = similarity
                    best_match = known_plate
        
        if best_score >= threshold:
            return best_match, best_score
        return None, best_score
    
    def enhance_detections(self, detections: List[Dict[str, Any]], min_confidence: float = 0.3) -> Dict[str, Any]:
        """Process multiple detections and determine the most likely plate"""
        if not detections:
            return None
            
        # First pass: weight by confidence and find consensus
        valid_detections = [d for d in detections if d["ocr_confidence"] >= min_confidence]
        
        if not valid_detections:
            valid_detections = detections  # Fall back to all detections
            
        # Create weighted votes based on OCR confidence
        votes = Counter()
        for detection in valid_detections:
            weight = max(1, int(detection["ocr_confidence"] * 10))
            plate_text = detection["plate_text"].upper().strip()
            
            # Add votes for this plate and its variations
            for variation in self.get_plate_variations(plate_text):
                votes[variation] += weight
        
        # Get top candidates
        top_candidates = votes.most_common(3)
        
        # Second pass: check against known plates
        for candidate, vote_count in top_candidates:
            known_match, match_score = self.match_with_known_plates(candidate)
            if known_match and match_score >= 0.8:
                # We found a strong match with a known plate
                consensus_confidence = match_score
                return {
                    "plate_text": known_match,
                    "confidence": consensus_confidence,
                    "confidence_category": self._get_confidence_category(consensus_confidence),
                    "match_type": "known_plate",
                    "original_detections": detections
                }
        
        # If no known match, use the consensus from votes
        if top_candidates:
            best_plate = top_candidates[0][0]
            vote_confidence = top_candidates[0][1] / sum(votes.values())
            
            return {
                "plate_text": best_plate,
                "confidence": vote_confidence,
                "confidence_category": self._get_confidence_category(vote_confidence),
                "match_type": "consensus",
                "original_detections": detections
            }
            
        # Fallback to the highest confidence detection
        best_detection = max(detections, key=lambda x: x["ocr_confidence"])
        return {
            "plate_text": best_detection["plate_text"],
            "confidence": best_detection["ocr_confidence"],
            "confidence_category": self._get_confidence_category(best_detection["ocr_confidence"]),
            "match_type": "single_best",
            "original_detections": detections
        }
    
    def _get_confidence_category(self, confidence: float) -> str:
        """Categorize confidence scores"""
        if confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

class LicensePlateProcessor:
    """Processes license plate detection files and enhances accuracy"""
    
    def __init__(self, input_dir: str = "data/license_plates", 
                output_dir: str = "data/enhanced_plates"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
        # Create directories if they don't exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize database and validator
        self.db = PlateDatabase()
        self.validator = LicensePlateValidator(known_plates=self.db.get_all_plates())
        
        # Track processed files
        self.processed_files = set()
        
    def process_file(self, file_path: str) -> bool:
        """Process a detection file and enhance plates"""
        if file_path in self.processed_files:
            return False
            
        if not file_path.endswith('.json'):
            return False
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Check if this is a valid detection file
            if "detections" not in data:
                print(f"Skipping {file_path}: Not a valid detection file")
                self.processed_files.add(file_path)
                return False
                
            # Create enhanced result structure
            enhanced_data = {
                "source_file": os.path.basename(file_path),
                "processed_at": datetime.datetime.now().isoformat(),
                "enhanced_results": []
            }
            
            if "session_start" in data:
                enhanced_data["session_start"] = data["session_start"]
            
            # Enhance each detection
            for detection in data["detections"]:
                enhanced_result = self.validator.enhance_detections([detection])
                enhanced_data["enhanced_results"].append(enhanced_result)
                
            # Save enhanced results
            enhanced_file_path = os.path.join(self.output_dir, f"enhanced_{os.path.basename(file_path)}")
            with open(enhanced_file_path, 'w') as f:
                json.dump(enhanced_data, f, indent=2)
                
            self.processed_files.add(file_path)  # Mark file as processed
            return True
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return False

class LicensePlateFileHandler(FileSystemEventHandler):
    """Handler for monitoring file system events."""
    
    def __init__(self, processor: LicensePlateProcessor):
        self.processor = processor
    
    def on_created(self, event):
        """Called when a new detection file is created."""
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")
            self.processor.process_file(event.src_path)

def main():
    """Main function to handle command-line arguments and process files."""
    parser = argparse.ArgumentParser(description="Automatic License Plate Enhancement")
    
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")
    
    # Watch mode
    watch_parser = subparsers.add_parser("watch", help="Monitor for new detection files")
    watch_parser.add_argument("--input_dir", default="data/license_plates", 
                               help="Directory to watch for new detection files")
    
    # File mode
    file_parser = subparsers.add_parser("file", help="Process a specific detection file")
    file_parser.add_argument("--file", required=True, help="Path to the detection JSON file")
    
    args = parser.parse_args()
    
    # Initialize the processing object
    processor = LicensePlateProcessor(input_dir=args.input_dir)

    if args.mode == "watch":
        observer = Observer()
        event_handler = LicensePlateFileHandler(processor)
        observer.schedule(event_handler, args.input_dir, recursive=False)
        observer.start()
        print(f"Monitoring {args.input_dir} for new arrivals...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    elif args.mode == "file":
        processor.process_file(args.file)

if __name__ == "__main__":
    main()