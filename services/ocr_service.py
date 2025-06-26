"""
OCR Service for TawjihiAI
Handles image text extraction with support for Arabic and English text
"""

import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import logging
from typing import Optional, Tuple, Dict
import os

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        """Initialize OCR service with Arabic and English language support"""
        self.supported_languages = ['ara', 'eng']  # Arabic and English
        self.tesseract_config = '--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
        
        # Check if tesseract is installed
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.error(f"Tesseract OCR not found: {e}")
            raise Exception("Tesseract OCR is required but not installed")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        """
        try:
            # Convert PIL image to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply thresholding to get better black and white image
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(thresh)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original image")
            return image

    def detect_language(self, image: Image.Image) -> str:
        """
        Detect the primary language in the image (Arabic or English)
        """
        try:
            # Try Arabic first
            arabic_text = pytesseract.image_to_string(image, lang='ara', config=self.tesseract_config)
            english_text = pytesseract.image_to_string(image, lang='eng', config=self.tesseract_config)
            
            # Simple heuristic: if we get more characters in Arabic, it's probably Arabic
            arabic_chars = len([c for c in arabic_text if c.strip()])
            english_chars = len([c for c in english_text if c.strip()])
            
            if arabic_chars > english_chars:
                return 'ara'
            else:
                return 'eng'
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'eng'

    def extract_text(self, image_data: bytes, language: Optional[str] = None) -> Dict[str, str]:
        """
        Extract text from image data
        
        Args:
            image_data: Raw image bytes
            language: Optional language hint ('ara' for Arabic, 'eng' for English)
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(image)
            
            # Detect language if not provided
            if not language:
                language = self.detect_language(processed_image)
            
            # Extract text with detected/specified language
            extracted_text = pytesseract.image_to_string(
                processed_image, 
                lang=language, 
                config=self.tesseract_config
            ).strip()
            
            # Get confidence scores
            try:
                data = pytesseract.image_to_data(processed_image, lang=language, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 0
            
            return {
                'text': extracted_text,
                'language': language,
                'confidence': round(avg_confidence, 2),
                'has_text': bool(extracted_text.strip()),
                'word_count': len(extracted_text.split()) if extracted_text else 0
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                'text': '',
                'language': 'unknown',
                'confidence': 0,
                'has_text': False,
                'word_count': 0,
                'error': str(e)
            }

    def extract_text_bilingual(self, image_data: bytes) -> Dict[str, any]:
        """
        Extract text in both Arabic and English for better coverage
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            processed_image = self.preprocess_image(image)
            
            # Extract in both languages
            arabic_result = self.extract_text(image_data, 'ara')
            english_result = self.extract_text(image_data, 'eng')
            
            # Choose the result with higher confidence or more text
            if arabic_result['confidence'] > english_result['confidence']:
                primary_result = arabic_result
                secondary_result = english_result
            else:
                primary_result = english_result
                secondary_result = arabic_result
            
            return {
                'primary': primary_result,
                'secondary': secondary_result,
                'combined_text': f"{primary_result['text']}\n{secondary_result['text']}".strip()
            }
            
        except Exception as e:
            logger.error(f"Bilingual OCR extraction failed: {e}")
            return {
                'primary': {'text': '', 'language': 'unknown', 'confidence': 0, 'has_text': False, 'word_count': 0},
                'secondary': {'text': '', 'language': 'unknown', 'confidence': 0, 'has_text': False, 'word_count': 0},
                'combined_text': '',
                'error': str(e)
            }

    def is_mathematical_content(self, text: str) -> bool:
        """
        Detect if the extracted text contains mathematical content
        """
        math_indicators = [
            '=', '+', '-', '×', '÷', '²', '³', '√', 'sin', 'cos', 'tan',
            'log', 'ln', '∫', '∑', 'π', 'α', 'β', 'γ', 'θ', 'x', 'y',
            'dx', 'dy', 'لم', 'جا', 'جتا', 'ظا'  # Arabic math terms
        ]
        
        return any(indicator in text.lower() for indicator in math_indicators)

    def extract_homework_content(self, image_data: bytes) -> Dict[str, any]:
        """
        Specialized extraction for homework problems
        """
        try:
            # Get bilingual extraction
            result = self.extract_text_bilingual(image_data)
            
            # Determine content type
            primary_text = result['primary']['text']
            is_math = self.is_mathematical_content(primary_text)
            
            # Add homework-specific metadata
            homework_result = {
                **result,
                'content_type': 'mathematics' if is_math else 'language',
                'is_homework': True,
                'extracted_at': None,  # Will be set by the calling service
                'processing_notes': []
            }
            
            # Add processing notes
            if result['primary']['confidence'] < 50:
                homework_result['processing_notes'].append('Low confidence extraction - image quality may be poor')
            
            if not result['primary']['has_text']:
                homework_result['processing_notes'].append('No text detected - image may not contain readable text')
            
            if is_math:
                homework_result['processing_notes'].append('Mathematical content detected - may require special formatting')
            
            return homework_result
            
        except Exception as e:
            logger.error(f"Homework content extraction failed: {e}")
            return {
                'primary': {'text': '', 'confidence': 0, 'has_text': False},
                'secondary': {'text': '', 'confidence': 0, 'has_text': False},
                'combined_text': '',
                'content_type': 'unknown',
                'is_homework': True,
                'error': str(e)
            }

# Global OCR service instance
ocr_service = OCRService()