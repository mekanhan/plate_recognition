import asyncio
import json
import os
import time
import difflib
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional, Tuple

class EnhancerService:
    """Service for enhancing license plate detections"""
    
    def __init__(self):
        self.known_plates = []
        self.plates_by_group = defaultdict(list)
        self.enhanced_results = {}
        self.last_enhancement_time = 0
        self.group_counter = 0
        self.enhancement_lock = asyncio.Lock()
        self.similarity_threshold = 0.7
        self.time_window = 10.0  # seconds
        self.enhancement_interval = 1.0  # seconds
        
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
    
    async def initialize(self, known_plates_path: str) -> None:
        """Initialize the enhancer service"""
        # Load known plates database
        await self._load_known_plates(known_plates_path)
        
        # Start background task for periodic enhancement
        self.task = asyncio.create_task(self._enhancement_loop())
        
        print(f"Enhancer service initialized with {len(self.known_plates)} known plates")
    
    async def shutdown(self) -> None:
        """Shutdown the enhancer service"""
        if hasattr(self, 'task'):
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        print("Enhancer service shutdown")
    
    async def _load_known_plates(self, known_plates_path: str) -> None:
        """Load known plates from a JSON file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(known_plates_path), exist_ok=True)
            
            if os.path.exists(known_plates_path):
                async with asyncio.to_thread(open, known_plates_path, 'r') as f:
                    data = json.load(f)
                    self.known_plates = [plate["plate_number"] for plate in data.get("plates", [])]
                    self.full_data = data
                    print(f"Loaded {len(self.known_plates)} known plates")
            else:
                # Initialize with VBR7660 as requested
                self.known_plates = ["VBR7660"]
                self.full_data = {
                    "plates": [{"plate_number": "VBR7660", "first_seen": time.strftime("%Y-%m-%d"), "metadata": {}}],
                    "last_updated": time.strftime("%Y-%m-%d")
                }
                print("Created new plate database with VBR7660")
                await self._save_known_plates(known_plates_path)
        except Exception as e:
            print(f"Error loading known plates: {e}")
            self.known_plates = ["VBR7660"]  # Fallback
    
    async def _save_known_plates(self, known_plates_path: str) -> None:
        """Save known plates to a JSON file"""
        self.full_data["last_updated"] = time.strftime("%Y-%m-%d")
        async with asyncio.to_thread(open, known_plates_path, 'w') as f:
            json.dump(self.full_data, f, indent=2)
    
    async def _enhancement_loop(self) -> None:
        """Periodically enhance detections"""
        while True:
            current_time = time.time()
            
            # Check if it's time to enhance
            if current_time - self.last_enhancement_time >= self.enhancement_interval:
                async with self.enhancement_lock:
                    await self._cleanup_old_detections(current_time)
                    await self._enhance_all_groups()
                    self.last_enhancement_time = current_time
            
            # Sleep to prevent CPU hogging
            await asyncio.sleep(0.1)
    
    async def enhance_detection(self, detection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new detection and return enhanced result if available
        
        Args:
            detection: New detection to add
            
        Returns:
            Enhanced detection or None
        """
        plate_text = detection["plate_text"]
        current_time = time.time()
        
        async with self.enhancement_lock:
            # Find best matching group
            best_group_id = None
            best_similarity = 0
            
            for group_id, detections in self.plates_by_group.items():
                if not detections:
                    continue
                    
                # Compare with the first detection in the group
                group_plate = detections[0]["plate_text"]
                similarity = self._calculate_similarity(plate_text, group_plate)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_group_id = group_id
            
            # If no matching group found, create a new one
            if best_group_id is None:
                best_group_id = f"group_{self.group_counter}"
                self.group_counter += 1
                
            # Add to the group
            self.plates_by_group[best_group_id].append(detection)
            
            # Return the enhanced result for this group if available
            return self.enhanced_results.get(best_group_id)
    
    async def _cleanup_old_detections(self, current_time: float) -> None:
        """Remove detections that are older than the time window"""
        for group_id, detections in list(self.plates_by_group.items()):
            # Filter out old detections
            recent_detections = [d for d in detections 
                                if current_time - d["unix_timestamp"] <= self.time_window]
            
            if recent_detections:
                self.plates_by_group[group_id] = recent_detections
            else:
                # Remove empty groups and their enhanced results
                del self.plates_by_group[group_id]
                if group_id in self.enhanced_results:
                    del self.enhanced_results[group_id]
    
    async def _enhance_all_groups(self) -> None:
        """Enhance all detection groups"""
        for group_id, detections in self.plates_by_group.items():
            if not detections:
                continue
                
            # Enhance this group
            enhanced = self._enhance_detections(detections)
            if enhanced:
                self.enhanced_results[group_id] = enhanced
    
    def _enhance_detections(self, detections: List[Dict[str, Any]], min_confidence: float = 0.3) -> Dict[str, Any]:
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
            for variation in self._get_plate_variations(plate_text):
                votes[variation] += weight
        
        # Get top candidates
        top_candidates = votes.most_common(3)
        
        # Second pass: check against known plates
        for candidate, vote_count in top_candidates:
            known_match, match_score = self._match_with_known_plates(candidate)
            if known_match and match_score >= 0.8:
                # We found a strong match with a known plate
                consensus_confidence = match_score
                return {
                    "plate_text": known_match,
                    "confidence": consensus_confidence,
                    "confidence_category": self._get_confidence_category(consensus_confidence),
                    "match_type": "known_plate",
                    "original_detections": [d["plate_text"] for d in detections]
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
                "original_detections": [d["plate_text"] for d in detections]
            }
            
        # Fallback to the highest confidence detection
        best_detection = max(detections, key=lambda x: x["ocr_confidence"])
        return {
            "plate_text": best_detection["plate_text"],
            "confidence": best_detection["ocr_confidence"],
            "confidence_category": self._get_confidence_category(best_detection["ocr_confidence"]),
            "match_type": "single_best",
            "original_detections": [d["plate_text"] for d in detections]
        }
    
    def _get_plate_variations(self, plate_text: str) -> List[str]:
        """Generate possible variations of a plate based on common OCR errors"""
        plate = plate_text.upper().strip()
        variations = [plate]
        
        # Generate variations with single character substitutions
        for i, char in enumerate(plate):
            if char in self.substitutions:
                new_plate = plate[:i] + self.substitutions[char] + plate[i+1:]
                variations.append(new_plate)
        
        return variations
    
    def _calculate_similarity(self, plate1: str, plate2: str) -> float:
        """Calculate string similarity between two plate texts"""
        return difflib.SequenceMatcher(None, plate1, plate2).ratio()
    
    def _match_with_known_plates(self, plate_text: str, threshold: float = 0.8) -> Tuple[Optional[str], float]:
        """Check if plate is similar to any known plate"""
        if not self.known_plates:
            return None, 0
            
        best_match = None
        best_score = 0
        
        # Check each variation of the input plate
        for variation in self._get_plate_variations(plate_text):
            for known_plate in self.known_plates:
                similarity = self._calculate_similarity(variation, known_plate)
                if similarity > best_score:
                    best_score = similarity
                    best_match = known_plate
        
        if best_score >= threshold:
            return best_match, best_score
        return None, best_score
    
    def _get_confidence_category(self, confidence: float) -> str:
        """Categorize confidence scores"""
        if confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def get_all_enhanced_results(self) -> List[Dict[str, Any]]:
        """Get all current enhanced results"""
        async with self.enhancement_lock:
            return list(self.enhanced_results.values())