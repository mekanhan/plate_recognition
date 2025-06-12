"""
Text normalization utilities for license plate recognition
Handles OCR errors, character substitutions, and fuzzy matching
"""
import re
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher

# Common OCR character substitution patterns for license plates
OCR_SUBSTITUTIONS = {
    '0': ['O', '0', 'Q'],
    'O': ['0', 'O', 'Q'],
    'Q': ['0', 'O', 'Q'],
    '1': ['I', 'L', '1', '|'],
    'I': ['1', 'L', 'I', '|'],
    'L': ['1', 'I', 'L', '|'],
    '5': ['S', '5'],
    'S': ['5', 'S'],
    '6': ['G', '6'],
    'G': ['6', 'G'],
    '8': ['B', '8'],
    'B': ['8', 'B'],
    '2': ['Z', '2'],
    'Z': ['2', 'Z'],
    '4': ['A', '4'],
    'A': ['4', 'A'],
    '9': ['g', '9'],
    'g': ['9', 'g'],
}

# Common license plate format patterns
PLATE_PATTERNS = [
    r'^[A-Z0-9]{2,3}[A-Z0-9]{3,4}$',  # Standard format: ABC123, AB1234
    r'^[A-Z0-9]{1,2}\s[A-Z0-9]{3,4}$',  # Spaced format: A 123, AB 1234
    r'^[A-Z0-9]{3}\s[A-Z0-9]{3}$',      # Three-three format: ABC 123
    r'^[A-Z0-9]{7}$',                   # Seven character format
]

class TextNormalizer:
    """Handles text normalization for license plate search"""
    
    def __init__(self):
        self.substitution_map = OCR_SUBSTITUTIONS
        self.plate_patterns = [re.compile(pattern) for pattern in PLATE_PATTERNS]
    
    def normalize_plate_text(self, text: str) -> str:
        """
        Normalize license plate text for consistent searching
        
        Args:
            text: Raw license plate text
            
        Returns:
            Normalized text (uppercase, no spaces/special chars)
        """
        if not text:
            return ""
        
        # Convert to uppercase
        normalized = text.upper()
        
        # Remove spaces, dashes, and other non-alphanumeric characters
        normalized = re.sub(r'[^A-Z0-9]', '', normalized)
        
        return normalized
    
    def generate_search_variants(self, text: str, max_variants: int = 50) -> List[str]:
        """
        Generate search variants for OCR error tolerance
        
        Args:
            text: Input license plate text
            max_variants: Maximum number of variants to generate
            
        Returns:
            List of text variants including original and substitutions
        """
        if not text:
            return []
        
        normalized = self.normalize_plate_text(text)
        variants = set([normalized])
        
        # Generate single character substitutions
        for i, char in enumerate(normalized):
            if char in self.substitution_map:
                for substitute in self.substitution_map[char]:
                    if substitute != char:  # Don't include the original character
                        variant = normalized[:i] + substitute + normalized[i+1:]
                        variants.add(variant)
                        
                        # Stop if we've generated enough variants
                        if len(variants) >= max_variants:
                            return list(variants)
        
        # Generate combinations of two character substitutions for short plates
        if len(normalized) <= 6 and len(variants) < max_variants:
            base_variants = list(variants)
            for variant in base_variants[:10]:  # Limit base variants to avoid explosion
                for i, char in enumerate(variant):
                    if char in self.substitution_map:
                        for substitute in self.substitution_map[char]:
                            if substitute != char:
                                new_variant = variant[:i] + substitute + variant[i+1:]
                                variants.add(new_variant)
                                
                                if len(variants) >= max_variants:
                                    return list(variants)
        
        return list(variants)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two license plate texts using fuzzy matching
        
        Args:
            text1: First text to compare
            text2: Second text to compare
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        norm1 = self.normalize_plate_text(text1)
        norm2 = self.normalize_plate_text(text2)
        
        if norm1 == norm2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Apply bonus for common OCR substitutions
        ocr_bonus = self._calculate_ocr_bonus(norm1, norm2)
        
        # Combine similarity with OCR bonus (max 1.0)
        return min(1.0, similarity + ocr_bonus)
    
    def _calculate_ocr_bonus(self, text1: str, text2: str) -> float:
        """
        Calculate bonus score for OCR-like character substitutions
        
        Args:
            text1: First normalized text
            text2: Second normalized text
            
        Returns:
            Bonus score (0.0 to 0.3)
        """
        if len(text1) != len(text2):
            return 0.0
        
        ocr_matches = 0
        total_chars = len(text1)
        
        for i, (c1, c2) in enumerate(zip(text1, text2)):
            if c1 != c2:
                # Check if characters are OCR substitutes
                if (c1 in self.substitution_map and c2 in self.substitution_map[c1]) or \
                   (c2 in self.substitution_map and c1 in self.substitution_map[c2]):
                    ocr_matches += 1
        
        # Return bonus based on OCR matches (max 0.3)
        return min(0.3, (ocr_matches / total_chars) * 0.5)
    
    def is_valid_plate_format(self, text: str) -> bool:
        """
        Check if text matches common license plate formats
        
        Args:
            text: License plate text to validate
            
        Returns:
            True if text matches a valid plate format
        """
        if not text:
            return False
        
        normalized = self.normalize_plate_text(text)
        
        # Check length constraints
        if len(normalized) < 2 or len(normalized) > 8:
            return False
        
        # Check against common patterns
        for pattern in self.plate_patterns:
            if pattern.match(normalized):
                return True
        
        # Fallback: check if it's mostly alphanumeric with reasonable length
        return len(normalized) >= 3 and normalized.isalnum()

class FuzzySearchEngine:
    """Enhanced search engine with fuzzy matching capabilities"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.normalizer = TextNormalizer()
        self.similarity_threshold = similarity_threshold
    
    def prepare_search_terms(self, query: str) -> Dict[str, any]:
        """
        Prepare search terms for database query
        
        Args:
            query: User search query
            
        Returns:
            Dictionary with search variants and parameters
        """
        if not query or len(query.strip()) < 2:
            return {
                'exact_match': None,
                'variants': [],
                'normalized': '',
                'use_fuzzy': False
            }
        
        normalized = self.normalizer.normalize_plate_text(query)
        variants = self.normalizer.generate_search_variants(normalized)
        
        return {
            'exact_match': normalized,
            'variants': variants[:20],  # Limit for performance
            'normalized': normalized,
            'use_fuzzy': len(normalized) >= 3,  # Only use fuzzy for 3+ chars
            'original_query': query.strip()
        }
    
    def build_sql_conditions(self, search_terms: Dict[str, any]) -> Tuple[str, List[str]]:
        """
        Build SQL WHERE conditions for fuzzy search
        
        Args:
            search_terms: Prepared search terms from prepare_search_terms
            
        Returns:
            Tuple of (SQL condition string, list of parameters)
        """
        if not search_terms['exact_match']:
            return "1=1", []
        
        conditions = []
        params = []
        
        # Exact match (highest priority)
        conditions.append("UPPER(REPLACE(plate_text, ' ', '')) = UPPER(?)")
        params.append(search_terms['normalized'])
        
        # Variant matches (OCR substitutions)
        if search_terms['variants']:
            variant_conditions = []
            for variant in search_terms['variants'][:10]:  # Limit for performance
                variant_conditions.append("UPPER(REPLACE(plate_text, ' ', '')) = UPPER(?)")
                params.append(variant)
            
            if variant_conditions:
                conditions.append(f"({' OR '.join(variant_conditions)})")
        
        # Contains match for partial searches
        conditions.append("UPPER(plate_text) LIKE UPPER(?)")
        params.append(f"%{search_terms['normalized']}%")
        
        # Combine with OR
        final_condition = f"({' OR '.join(conditions)})"
        
        return final_condition, params
    
    def rank_results(self, results: List[Dict], original_query: str) -> List[Dict]:
        """
        Rank search results by relevance
        
        Args:
            results: List of detection results from database
            original_query: Original user search query
            
        Returns:
            Ranked list of results with similarity scores
        """
        if not results or not original_query:
            return results
        
        ranked_results = []
        
        for result in results:
            plate_text = result.get('plate_text', '')
            
            # Calculate similarity score
            similarity = self.normalizer.calculate_similarity(original_query, plate_text)
            
            # Add similarity score to result
            result['search_similarity'] = similarity
            
            # Determine match type
            normalized_query = self.normalizer.normalize_plate_text(original_query)
            normalized_plate = self.normalizer.normalize_plate_text(plate_text)
            
            if normalized_query == normalized_plate:
                result['match_type'] = 'exact'
                result['search_score'] = 1.0
            elif normalized_query in normalized_plate or normalized_plate in normalized_query:
                result['match_type'] = 'contains'
                result['search_score'] = 0.8 + (similarity * 0.2)
            else:
                result['match_type'] = 'fuzzy'
                result['search_score'] = similarity * 0.6
            
            ranked_results.append(result)
        
        # Sort by search score (descending), then by confidence, then by timestamp
        ranked_results.sort(key=lambda x: (
            -x.get('search_score', 0),
            -x.get('confidence', 0),
            -x.get('timestamp', 0)
        ))
        
        return ranked_results

# Global instances for easy import
normalizer = TextNormalizer()
fuzzy_engine = FuzzySearchEngine()