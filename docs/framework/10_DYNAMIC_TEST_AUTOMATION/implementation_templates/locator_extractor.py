#!/usr/bin/env python3
"""
Dynamic Test Automation Framework - Locator Extractor
Automatically extracts UI element locators from frontend applications.
"""

import argparse
import ast
import json
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class UIElement:
    """Represents a UI element with its locator information."""
    name: str
    element_type: str
    locator_primary: str
    locator_fallbacks: List[str]
    confidence: float
    component: str
    page: str
    description: str

class LocatorExtractor:
    """Extract UI element locators from frontend code."""
    
    def __init__(self, framework: str = "react"):
        self.framework = framework.lower()
        self.elements = []
        self.component_map = {}
        
        # Framework-specific patterns
        self.patterns = {
            "react": {
                "file_extensions": [".jsx", ".tsx", ".js", ".ts"],
                "component_patterns": [
                    r'export\s+default\s+(?:function\s+)?(\w+)',
                    r'export\s+const\s+(\w+)\s*=',
                    r'function\s+(\w+)\s*\(',
                    r'const\s+(\w+)\s*=\s*\(\s*\)\s*=>'
                ],
                "element_patterns": {
                    "data-testid": r'data-testid=["\']([^"\']+)["\']',
                    "data-qa": r'data-qa=["\']([^"\']+)["\']',
                    "data-test": r'data-test=["\']([^"\']+)["\']',
                    "id": r'id=["\']([^"\']+)["\']',
                    "className": r'className=["\']([^"\']*)["\']',
                    "placeholder": r'placeholder=["\']([^"\']+)["\']',
                    "aria-label": r'aria-label=["\']([^"\']+)["\']'
                }
            },
            "vue": {
                "file_extensions": [".vue"],
                "component_patterns": [
                    r'name:\s*["\']([^"\']+)["\']',
                    r'export\s+default\s*\{\s*name:\s*["\']([^"\']+)["\']'
                ],
                "element_patterns": {
                    "data-testid": r'data-testid=["\']([^"\']+)["\']',
                    "id": r'id=["\']([^"\']+)["\']',
                    "class": r'class=["\']([^"\']*)["\']'
                }
            },
            "angular": {
                "file_extensions": [".component.ts", ".component.html"],
                "component_patterns": [
                    r'@Component\s*\(\s*\{\s*selector:\s*["\']([^"\']+)["\']'
                ],
                "element_patterns": {
                    "data-testid": r'data-testid=["\']([^"\']+)["\']',
                    "id": r'id=["\']([^"\']+)["\']'
                }
            }
        }
    
    def extract_from_directory(self, source_dir: str) -> List[UIElement]:
        """Extract locators from all files in directory."""
        
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        logger.info(f"Starting locator extraction from: {source_dir}")
        
        # Get all relevant files
        files = self._get_component_files(source_path)
        logger.info(f"Found {len(files)} component files to analyze")
        
        # Extract from each file
        for file_path in files:
            try:
                elements = self._extract_from_file(file_path)
                self.elements.extend(elements)
                logger.debug(f"Extracted {len(elements)} elements from {file_path}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Total elements extracted: {len(self.elements)}")
        return self.elements
    
    def _get_component_files(self, source_path: Path) -> List[Path]:
        """Get all component files based on framework."""
        
        extensions = self.patterns[self.framework]["file_extensions"]
        files = []
        
        for ext in extensions:
            pattern = f"**/*{ext}"
            files.extend(source_path.glob(pattern))
        
        return files
    
    def _extract_from_file(self, file_path: Path) -> List[UIElement]:
        """Extract UI elements from a single file."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return []
        
        elements = []
        component_name = self._extract_component_name(file_path, content)
        page_name = self._infer_page_name(file_path)
        
        # Extract elements using framework-specific patterns
        element_patterns = self.patterns[self.framework]["element_patterns"]
        
        for pattern_type, pattern in element_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                element = self._create_ui_element(
                    match, pattern_type, component_name, page_name, content
                )
                if element:
                    elements.append(element)
        
        return elements
    
    def _extract_component_name(self, file_path: Path, content: str) -> str:
        """Extract component name from file."""
        
        component_patterns = self.patterns[self.framework]["component_patterns"]
        
        for pattern in component_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Fallback to filename
        return file_path.stem.replace('.component', '').replace('.page', '')
    
    def _infer_page_name(self, file_path: Path) -> str:
        """Infer page name from file path."""
        
        path_parts = file_path.parts
        
        # Look for common page indicators
        page_indicators = ['pages', 'views', 'screens', 'routes']
        
        for i, part in enumerate(path_parts):
            if part.lower() in page_indicators and i + 1 < len(path_parts):
                return path_parts[i + 1]
        
        # Fallback to parent directory
        return file_path.parent.name if file_path.parent.name != 'src' else 'default'
    
    def _create_ui_element(self, value: str, pattern_type: str, 
                          component: str, page: str, content: str) -> Optional[UIElement]:
        """Create UIElement from extracted data."""
        
        # Skip empty or invalid values
        if not value or len(value.strip()) == 0:
            return None
        
        # Generate element name
        element_name = self._generate_element_name(value, pattern_type)
        
        # Create primary locator
        primary_locator = self._create_primary_locator(value, pattern_type)
        
        # Generate fallback locators
        fallback_locators = self._generate_fallback_locators(value, pattern_type, content)
        
        # Determine element type
        element_type = self._determine_element_type(value, content)
        
        # Calculate confidence
        confidence = self._calculate_confidence(pattern_type, value, content)
        
        # Generate description
        description = self._generate_description(element_name, element_type, component)
        
        return UIElement(
            name=element_name,
            element_type=element_type,
            locator_primary=primary_locator,
            locator_fallbacks=fallback_locators,
            confidence=confidence,
            component=component,
            page=page,
            description=description
        )
    
    def _generate_element_name(self, value: str, pattern_type: str) -> str:
        """Generate standardized element name."""
        
        if pattern_type in ["data-testid", "data-qa", "data-test"]:
            # Use the test ID as the name
            return value.replace('-', '_').replace(' ', '_').lower()
        elif pattern_type == "id":
            return value.replace('-', '_').lower()
        elif pattern_type == "className":
            # Extract semantic class name
            classes = value.split()
            semantic_keywords = ['btn', 'button', 'input', 'form', 'modal', 'nav', 'menu']
            for class_name in classes:
                if any(keyword in class_name.lower() for keyword in semantic_keywords):
                    return class_name.replace('-', '_').lower()
            return classes[0].replace('-', '_').lower() if classes else "element"
        else:
            # Generate name from value
            return re.sub(r'[^a-zA-Z0-9_]', '_', value).lower()
    
    def _create_primary_locator(self, value: str, pattern_type: str) -> str:
        """Create primary CSS selector."""
        
        if pattern_type in ["data-testid", "data-qa", "data-test"]:
            return f"[{pattern_type}='{value}']"
        elif pattern_type == "id":
            return f"#{value}"
        elif pattern_type == "className":
            # Use first semantic class
            classes = value.split()
            if classes:
                return f".{classes[0]}"
        elif pattern_type in ["placeholder", "aria-label"]:
            return f"[{pattern_type}='{value}']"
        
        return f"[{pattern_type}='{value}']"
    
    def _generate_fallback_locators(self, value: str, pattern_type: str, content: str) -> List[str]:
        """Generate fallback locator strategies."""
        
        fallbacks = []
        
        # Add XPath fallback
        if pattern_type in ["data-testid", "data-qa", "data-test"]:
            fallbacks.append(f"//*[@{pattern_type}='{value}']")
        
        # Add text-based fallback if it's a button or link
        if self._is_interactive_element(value, content):
            # Try to find associated text
            text_match = self._find_element_text(value, content)
            if text_match:
                fallbacks.append(f"text='{text_match}'")
        
        # Add partial class fallback for className
        if pattern_type == "className":
            classes = value.split()
            for class_name in classes[1:3]:  # Add up to 2 more class fallbacks
                fallbacks.append(f".{class_name}")
        
        return fallbacks
    
    def _determine_element_type(self, value: str, content: str) -> str:
        """Determine the semantic type of the element."""
        
        # Look for element type hints in the value or surrounding context
        value_lower = value.lower()
        
        if any(keyword in value_lower for keyword in ['btn', 'button']):
            return 'button'
        elif any(keyword in value_lower for keyword in ['input', 'field']):
            return 'input'
        elif any(keyword in value_lower for keyword in ['select', 'dropdown']):
            return 'select'
        elif any(keyword in value_lower for keyword in ['modal', 'dialog']):
            return 'modal'
        elif any(keyword in value_lower for keyword in ['nav', 'menu']):
            return 'navigation'
        elif any(keyword in value_lower for keyword in ['table', 'grid']):
            return 'table'
        elif any(keyword in value_lower for keyword in ['link']):
            return 'link'
        elif any(keyword in value_lower for keyword in ['title', 'heading']):
            return 'heading'
        elif any(keyword in value_lower for keyword in ['text', 'label']):
            return 'text'
        else:
            return 'element'
    
    def _calculate_confidence(self, pattern_type: str, value: str, content: str) -> float:
        """Calculate confidence score for the locator."""
        
        base_confidence = {
            "data-testid": 0.95,
            "data-qa": 0.95,
            "data-test": 0.95,
            "id": 0.90,
            "aria-label": 0.85,
            "placeholder": 0.80,
            "className": 0.70
        }
        
        confidence = base_confidence.get(pattern_type, 0.50)
        
        # Adjust based on value quality
        if len(value) < 3:
            confidence *= 0.8  # Very short values are less reliable
        elif len(value) > 50:
            confidence *= 0.9  # Very long values might be unstable
        
        # Boost confidence for semantic naming
        if any(keyword in value.lower() for keyword in ['test', 'qa', 'automation']):
            confidence = min(0.98, confidence * 1.1)
        
        return round(confidence, 2)
    
    def _generate_description(self, element_name: str, element_type: str, component: str) -> str:
        """Generate human-readable description."""
        
        return f"{element_type.title()} element '{element_name}' in {component} component"
    
    def _is_interactive_element(self, value: str, content: str) -> bool:
        """Check if element is likely interactive."""
        
        interactive_keywords = ['button', 'btn', 'click', 'submit', 'link', 'nav']
        return any(keyword in value.lower() for keyword in interactive_keywords)
    
    def _find_element_text(self, value: str, content: str) -> Optional[str]:
        """Try to find text content associated with element."""
        
        # Look for text near the element definition
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if value in line:
                # Look for text in surrounding lines
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    text_match = re.search(r'>([^<]{2,30})<', lines[j])
                    if text_match:
                        text = text_match.group(1).strip()
                        if len(text) > 1 and not text.isdigit():
                            return text
        
        return None
    
    def export_to_yaml(self, output_path: str) -> None:
        """Export extracted locators to YAML format."""
        
        # Group elements by page
        pages_data = {}
        
        for element in self.elements:
            page_name = element.page
            
            if page_name not in pages_data:
                pages_data[page_name] = {
                    "description": f"{page_name.title()} page elements",
                    "url_pattern": f"/{page_name.lower()}",
                    "elements": {}
                }
            
            # Group by component within page
            component_name = element.component
            if component_name not in pages_data[page_name]["elements"]:
                pages_data[page_name]["elements"][component_name] = {}
            
            # Add element data
            pages_data[page_name]["elements"][component_name][element.name] = {
                "primary": element.locator_primary,
                "fallbacks": element.locator_fallbacks,
                "confidence": element.confidence,
                "type": element.element_type,
                "description": element.description
            }
        
        # Create complete YAML structure
        yaml_data = {
            "version": "1.0.0",
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "application": "auto-extracted",
            "framework": self.framework,
            "pages": pages_data,
            "metadata": {
                "extraction_method": "automated",
                "framework_version": "1.0.0",
                "total_elements": len(self.elements),
                "pages_count": len(pages_data),
                "extraction_timestamp": time.time()
            }
        }
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, indent=2)
        
        logger.info(f"Exported {len(self.elements)} elements to {output_path}")
    
    def compare_with_previous(self, previous_path: str) -> Dict[str, Any]:
        """Compare with previous locator extraction."""
        
        if not Path(previous_path).exists():
            return {
                "new_elements": len(self.elements),
                "removed_elements": 0,
                "changed_elements": 0,
                "unchanged_elements": 0,
                "comparison_possible": False
            }
        
        try:
            with open(previous_path, 'r', encoding='utf-8') as f:
                previous_data = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Could not load previous data: {e}")
            return {"comparison_possible": False}
        
        # Build comparison
        current_elements = {elem.name: elem for elem in self.elements}
        previous_elements = {}
        
        # Extract previous elements
        for page_data in previous_data.get("pages", {}).values():
            for component_data in page_data.get("elements", {}).values():
                for elem_name, elem_data in component_data.items():
                    previous_elements[elem_name] = elem_data
        
        # Compare
        current_names = set(current_elements.keys())
        previous_names = set(previous_elements.keys())
        
        new_elements = current_names - previous_names
        removed_elements = previous_names - current_names
        common_elements = current_names & previous_names
        
        changed_elements = set()
        for name in common_elements:
            current_elem = current_elements[name]
            previous_elem = previous_elements[name]
            
            if (current_elem.locator_primary != previous_elem.get("primary") or
                current_elem.element_type != previous_elem.get("type")):
                changed_elements.add(name)
        
        return {
            "new_elements": list(new_elements),
            "removed_elements": list(removed_elements),
            "changed_elements": list(changed_elements),
            "unchanged_elements": list(common_elements - changed_elements),
            "comparison_possible": True,
            "summary": {
                "new_count": len(new_elements),
                "removed_count": len(removed_elements),
                "changed_count": len(changed_elements),
                "unchanged_count": len(common_elements - changed_elements)
            }
        }

def main():
    """Main entry point for the locator extractor."""
    
    parser = argparse.ArgumentParser(description="Extract UI locators from frontend code")
    parser.add_argument("--source-dir", required=True, help="Source directory to scan")
    parser.add_argument("--framework", default="react", choices=["react", "vue", "angular"], 
                       help="Frontend framework")
    parser.add_argument("--output", required=True, help="Output YAML file path")
    parser.add_argument("--previous", help="Previous locators file for comparison")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create extractor and run extraction
        extractor = LocatorExtractor(framework=args.framework)
        elements = extractor.extract_from_directory(args.source_dir)
        
        if not elements:
            logger.warning("No UI elements found!")
            return 1
        
        # Export to YAML
        extractor.export_to_yaml(args.output)
        
        # Compare with previous if provided
        if args.previous:
            comparison = extractor.compare_with_previous(args.previous)
            if comparison["comparison_possible"]:
                summary = comparison["summary"]
                logger.info("Comparison with previous extraction:")
                logger.info(f"  New elements: {summary['new_count']}")
                logger.info(f"  Removed elements: {summary['removed_count']}")
                logger.info(f"  Changed elements: {summary['changed_count']}")
                logger.info(f"  Unchanged elements: {summary['unchanged_count']}")
                
                # Write comparison report
                comparison_file = args.output.replace('.yml', '_comparison.json')
                with open(comparison_file, 'w') as f:
                    json.dump(comparison, f, indent=2)
                logger.info(f"Comparison report saved to: {comparison_file}")
        
        logger.info("Locator extraction completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())