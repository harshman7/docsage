"""
Visual document overlay - highlight extracted fields on document images.
"""
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional, List, Tuple
import pytesseract
from pathlib import Path

# Optional imports for advanced features
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

def get_text_bounding_boxes(image_path: str, text_to_find: str) -> List[Tuple[int, int, int, int]]:
    """
    Find bounding boxes for specific text in an image using OCR.
    Returns list of (x, y, width, height) tuples.
    """
    try:
        # Use pytesseract to get detailed OCR data
        image = Image.open(image_path)
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        boxes = []
        words = text_to_find.lower().split()
        
        # Find all occurrences of the text
        for i, word in enumerate(ocr_data['text']):
            word_lower = word.lower().strip()
            if word_lower and any(w in word_lower for w in words):
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                if w > 0 and h > 0:
                    boxes.append((x, y, w, h))
        
        return boxes
    except Exception as e:
        print(f"Error getting bounding boxes: {e}")
        return []

def highlight_field_on_image(
    image_path: str,
    field_name: str,
    field_value: Any,
    output_path: Optional[str] = None
) -> Image.Image:
    """
    Highlight a specific field on the document image.
    
    Args:
        image_path: Path to original image
        field_name: Name of field (vendor, total, invoice_number, etc.)
        field_value: Value to highlight
        output_path: Optional path to save annotated image
        
    Returns:
        PIL Image with highlights
    """
    try:
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # Try to find the text and draw bounding box
        if field_value:
            boxes = get_text_bounding_boxes(image_path, str(field_value))
            
            # Color mapping for different fields
            colors = {
                "vendor": (255, 0, 0, 128),  # Red
                "total": (0, 255, 0, 128),   # Green
                "invoice_number": (0, 0, 255, 128),  # Blue
                "date": (255, 165, 0, 128),  # Orange
            }
            
            color = colors.get(field_name, (255, 255, 0, 128))  # Yellow default
            
            for x, y, w, h in boxes:
                # Draw rectangle
                draw.rectangle([x, y, x + w, y + h], outline=color[:3], width=3)
                # Draw semi-transparent overlay
                overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle([x, y, x + w, y + h], fill=color)
                image = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
        
        if output_path:
            image.save(output_path)
        
        return image
        
    except Exception as e:
        print(f"Error highlighting field: {e}")
        return Image.open(image_path)

def create_annotated_document(
    image_path: str,
    extracted_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> Image.Image:
    """
    Create a fully annotated document with all extracted fields highlighted.
    
    Args:
        image_path: Path to original document image
        extracted_data: Dictionary of extracted fields
        output_path: Optional path to save annotated image
        
    Returns:
        PIL Image with all fields highlighted
    """
    try:
        image = Image.open(image_path).convert('RGBA')
        draw = ImageDraw.Draw(image)
        
        # Colors for different field types
        field_colors = {
            "vendor": (255, 0, 0, 180),      # Red
            "total": (0, 255, 0, 180),      # Green
            "invoice_number": (0, 0, 255, 180),  # Blue
            "dates": (255, 165, 0, 180),     # Orange
        }
        
        # Highlight each field
        for field_name, field_value in extracted_data.items():
            if not field_value:
                continue
            
            # Get color for this field
            color = field_colors.get(field_name, (255, 255, 0, 180))
            
            # Find text in image
            if isinstance(field_value, list):
                for val in field_value[:3]:  # Limit to first 3 items
                    boxes = get_text_bounding_boxes(image_path, str(val))
                    for x, y, w, h in boxes:
                        draw.rectangle([x, y, x + w, y + h], outline=color[:3], width=2)
            else:
                boxes = get_text_bounding_boxes(image_path, str(field_value))
                for x, y, w, h in boxes:
                    draw.rectangle([x, y, x + w, y + h], outline=color[:3], width=2)
        
        # Convert back to RGB
        image = image.convert('RGB')
        
        if output_path:
            image.save(output_path)
        
        return image
        
    except Exception as e:
        print(f"Error creating annotated document: {e}")
        return Image.open(image_path)

def get_extraction_confidence(extracted_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate confidence scores for each extracted field.
    Returns dict mapping field_name -> confidence (0-100).
    """
    confidence = {}
    
    # Simple heuristics - can be improved with ML models
    for field_name, field_value in extracted_data.items():
        score = 0.0
        
        if field_value:
            if field_name == "vendor":
                # Longer vendor names are more reliable
                if isinstance(field_value, str) and len(field_value) > 3:
                    score = min(90, 50 + len(field_value) * 2)
            elif field_name == "total":
                # Amounts that are reasonable are more reliable
                if isinstance(field_value, (int, float)) and 0.01 <= field_value <= 1000000:
                    score = 85
            elif field_name == "invoice_number":
                # Invoice numbers with alphanumeric are more reliable
                if isinstance(field_value, str) and len(field_value) > 3:
                    score = 80
            elif field_name == "dates":
                # Dates that are valid are more reliable
                if isinstance(field_value, list) and len(field_value) > 0:
                    score = 75
        
        confidence[field_name] = score
    
    return confidence

