import asyncio
import difflib
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple
import time
import logging

logger = logging.getLogger(__name__)

class EnhancerService:
    """Simplified enhancer service for initial setup"""
    def __init__(self):
        self.known_plates = ["VBR7660"]  # Start with a default known plate
        self.storage_service = None  # Will be set by main.py

    async def initialize(self, known_plates_path: str = None, storage_service = None) -> None:
        """Initialize the enhancer service"""
        if storage_service:
            self.storage_service = storage_service
            logger.info("EnhancerService connected to StorageService")

        print(f"Enhancer service initialized with {len(self.known_plates)} known plates")
    
    async def enhance_detection(self, detection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Simplified enhancer that just returns the detection with a confidence level"""
        if not detection:
            return None
            
        # Very simple enhancement - just check if it's in known plates
        plate_text = detection.get("plate_text", "").upper()

        if not plate_text:
            logger.debug("Skipping enhancement: No plate text")
            return None
        enhanced_result = None
        if plate_text in self.known_plates:
            enhanced_result = {
                "plate_text": plate_text,
                "confidence": 0.9,
                "confidence_category": "HIGH",
                "match_type": "known_plate",
                "original_detection_id": detection.get("detection_id", "unknown"),
                "timestamp": time.time()
            }
        else:
            # Apply some basic enhancement - improve confidence slightly
            original_confidence = detection.get("confidence", 0.0)
            enhanced_confidence = min(original_confidence + 0.1, 1.0)  # Boost confidence slightly

            enhanced_result = {
                "plate_text": plate_text,
                "confidence": enhanced_confidence,
                "confidence_category": self._get_confidence_category(enhanced_confidence),
                "match_type": "enhanced",
                "original_detection_id": detection.get("detection_id", "unknown"),
                "timestamp": time.time()
            }

        # Save the enhanced result if storage service is available
        if enhanced_result and self.storage_service:
            try:
                # Create a record for storage
                enhanced_record = {
                    "enhanced_id": f"enh-{time.time()}",
                    "plate_text": enhanced_result["plate_text"],
                    "confidence": enhanced_result["confidence"],
                    "confidence_category": enhanced_result["confidence_category"],
                    "match_type": enhanced_result["match_type"],
                    "original_detection_id": enhanced_result["original_detection_id"],
                    "timestamp": enhanced_result["timestamp"],
                    "enhanced_at": time.time()
                }

                # Save to storage
                await self.storage_service.add_enhanced_results([enhanced_record])
                logger.info(f"Enhanced result saved for plate: {plate_text}")
            except Exception as e:
                logger.error(f"Error saving enhanced result: {e}")

        return enhanced_result

    def _get_confidence_category(self, confidence: float) -> str:
        """Categorize confidence scores"""
        if confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

class LicensePlateValidator:
    """
    Validates and improves license plate detection accuracy
    using multiple techniques and a known plates database.
    """

    def __init__(self, known_plates=None, storage_service=None):
        """Initialize with optional known plates database"""
        self.known_plates = known_plates or []
        self.storage_service = storage_service
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

    async def enhance_detections(self, detections: List[Dict[str, Any]], min_confidence: float = 0.3) -> Dict[str, Any]:
        """
        Process multiple detections and determine the most likely plate
        with confidence levels
        """
        if not detections:
            return None

        # First pass: weight by confidence and find consensus
        valid_detections = [d for d in detections if d.get("ocr_confidence", 0) >= min_confidence]

        if not valid_detections:
            valid_detections = detections  # Fall back to all detections

        # Create weighted votes based on OCR confidence
        votes = Counter()
        for detection in valid_detections:
            weight = max(1, int(detection.get("ocr_confidence", 0) * 10))
            plate_text = detection.get("plate_text", "").upper().strip()

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
                enhanced_result = {
                    "plate_text": known_match,
                    "confidence": consensus_confidence,
                    "confidence_category": self._get_confidence_category(consensus_confidence),
                    "match_type": "known_plate",
                    "original_detections": [d.get("detection_id", "unknown") for d in detections],
                    "timestamp": time.time()
                }

                # Save the enhanced result if storage service is available
                if self.storage_service:
                    try:
                        await self.storage_service.add_enhanced_results([enhanced_result])
                        logger.info(f"Enhanced result saved for plate: {known_match}")
                    except Exception as e:
                        logger.error(f"Error saving enhanced result: {e}")

                return enhanced_result

        # If no known match, use the consensus from votes
        if top_candidates:
            best_plate = top_candidates[0][0]
            vote_confidence = top_candidates[0][1] / sum(votes.values())

            enhanced_result = {
                "plate_text": best_plate,
                "confidence": vote_confidence,
                "confidence_category": self._get_confidence_category(vote_confidence),
                "match_type": "consensus",
                "original_detections": [d.get("detection_id", "unknown") for d in detections],
                "timestamp": time.time()
            }

            # Save the enhanced result if storage service is available
            if self.storage_service:
                try:
                    await self.storage_service.add_enhanced_results([enhanced_result])
                    logger.info(f"Enhanced result saved for plate: {best_plate}")
                except Exception as e:
                    logger.error(f"Error saving enhanced result: {e}")

            return enhanced_result

        # Fallback to the highest confidence detection
        best_detection = max(detections, key=lambda x: x.get("ocr_confidence", 0))
        enhanced_result = {
            "plate_text": best_detection.get("plate_text", ""),
            "confidence": best_detection.get("ocr_confidence", 0),
            "confidence_category": self._get_confidence_category(best_detection.get("ocr_confidence", 0)),
            "match_type": "single_best",
            "original_detections": [d.get("detection_id", "unknown") for d in detections],
            "timestamp": time.time()
        }

        # Save the enhanced result if storage service is available
        if self.storage_service:
            try:
                await self.storage_service.add_enhanced_results([enhanced_result])
                logger.info(f"Enhanced result saved for plate: {best_detection.get('plate_text', '')}")
            except Exception as e:
                logger.error(f"Error saving enhanced result: {e}")

        return enhanced_result

    def _get_confidence_category(self, confidence: float) -> str:
        """Categorize confidence scores"""
        if confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
