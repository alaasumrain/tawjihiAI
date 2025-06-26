#!/usr/bin/env python3
"""
Test OCR functionality locally without server dependencies
"""
import os
import sys
import io
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ocr_service import OCRService

def create_test_image_with_text(text: str, language: str = 'eng') -> bytes:
    """Create a test image with text"""
    # Create a white image
    width, height = 800, 200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font, fallback to basic if not available
    try:
        # For Arabic text, we might need a different approach
        if language == 'ara':
            font_size = 24
        else:
            font_size = 20
        # Use default font
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Draw text on image
    text_position = (50, 80)
    draw.text(text_position, text, fill='black', font=font)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr

def test_ocr_service():
    """Test OCR service functionality"""
    print("🧪 Testing OCR Service...")
    
    ocr_service = OCRService()
    
    # Test 1: English text
    print("\n📝 Test 1: English text extraction")
    english_text = "Solve for x: 2x + 5 = 15"
    english_image = create_test_image_with_text(english_text, 'eng')
    
    result = ocr_service.extract_text(english_image, 'eng')
    print(f"Original: {english_text}")
    print(f"Extracted: {result.get('text', 'No text found')}")
    print(f"Confidence: {result.get('confidence', 0):.1f}%")
    
    # Test 2: Arabic text
    print("\n📝 Test 2: Arabic text extraction")
    arabic_text = "احسب قيمة س: ٢س + ٥ = ١٥"
    arabic_image = create_test_image_with_text(arabic_text, 'ara')
    
    result = ocr_service.extract_text(arabic_image, 'ara')
    print(f"Original: {arabic_text}")
    print(f"Extracted: {result.get('text', 'No text found')}")
    print(f"Confidence: {result.get('confidence', 0):.1f}%")
    
    # Test 3: Bilingual extraction
    print("\n📝 Test 3: Bilingual text extraction")
    mixed_text = "Question: What is 2x + 5 = 15?"
    mixed_image = create_test_image_with_text(mixed_text, 'eng')
    
    result = ocr_service.extract_text_bilingual(mixed_image)
    print(f"Original: {mixed_text}")
    print(f"Primary language: {result.get('primary', {}).get('language', 'unknown')}")
    print(f"Primary text: {result.get('primary', {}).get('text', 'No text found')}")
    print(f"Primary confidence: {result.get('primary', {}).get('confidence', 0):.1f}%")
    
    # Test 4: Homework content extraction
    print("\n📝 Test 4: Homework content extraction")
    homework_text = "Math Problem: Find the derivative of f(x) = x^2 + 3x - 2"
    homework_image = create_test_image_with_text(homework_text, 'eng')
    
    result = ocr_service.extract_homework_content(homework_image)
    print(f"Original: {homework_text}")
    print(f"Extracted text: {result.get('primary', {}).get('text', 'No text found')}")
    print(f"Is mathematical: {result.get('is_math', False)}")
    print(f"Subject detected: {result.get('subject', 'unknown')}")
    print(f"Confidence: {result.get('primary', {}).get('confidence', 0):.1f}%")
    
    print("\n✅ OCR Service tests completed!")

if __name__ == "__main__":
    test_ocr_service()