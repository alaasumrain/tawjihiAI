"""
File Handler Service for TawjihiAI
Handles file uploads, validation, and processing
"""

import os
import uuid
import logging
from typing import Optional, Dict, List
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
import mimetypes

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, upload_dir: str = "uploads"):
        """Initialize file handler with upload directory"""
        self.upload_dir = upload_dir
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Supported file types
        self.supported_image_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'
        }
        self.supported_document_types = {
            'application/pdf', 'text/plain'
        }
        self.supported_types = self.supported_image_types | self.supported_document_types
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"File handler initialized with upload directory: {upload_dir}")

    def validate_file(self, file: UploadFile) -> Dict[str, any]:
        """
        Validate uploaded file
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'file_info': {
                'filename': file.filename,
                'content_type': file.content_type,
                'size': 0
            }
        }
        
        try:
            # Check if file exists
            if not file or not file.filename:
                validation_result['is_valid'] = False
                validation_result['errors'].append('No file provided')
                return validation_result
            
            # Read file content to check size
            file_content = file.file.read()
            file.file.seek(0)  # Reset file pointer
            
            file_size = len(file_content)
            validation_result['file_info']['size'] = file_size
            
            # Check file size
            if file_size > self.max_file_size:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f'File too large. Maximum size: {self.max_file_size // (1024*1024)}MB')
            
            # Check file type
            if file.content_type not in self.supported_types:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f'Unsupported file type: {file.content_type}')
            
            # Additional validation for images
            if file.content_type in self.supported_image_types:
                try:
                    image = Image.open(io.BytesIO(file_content))
                    validation_result['file_info']['image_size'] = image.size
                    validation_result['file_info']['image_mode'] = image.mode
                except Exception as e:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f'Invalid image file: {str(e)}')
            
            return validation_result
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            validation_result['is_valid'] = False
            validation_result['errors'].append(f'Validation error: {str(e)}')
            return validation_result

    def save_file(self, file: UploadFile, user_id: str) -> Dict[str, any]:
        """
        Save uploaded file to disk
        
        Args:
            file: FastAPI UploadFile object
            user_id: User identifier for organizing files
            
        Returns:
            File save result
        """
        try:
            # Validate file first
            validation = self.validate_file(file)
            if not validation['is_valid']:
                return {
                    'success': False,
                    'errors': validation['errors']
                }
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create user-specific directory
            user_dir = os.path.join(self.upload_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Full file path
            file_path = os.path.join(user_dir, unique_filename)
            
            # Save file
            file_content = file.file.read()
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Reset file pointer for potential further processing
            file.file.seek(0)
            
            logger.info(f"File saved: {file_path}")
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': unique_filename,
                'original_name': file.filename,
                'size': len(file_content),
                'content_type': file.content_type,
                'url': f"/uploads/{user_id}/{unique_filename}"
            }
            
        except Exception as e:
            logger.error(f"File save error: {e}")
            return {
                'success': False,
                'errors': [f'Failed to save file: {str(e)}']
            }

    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        Get information about a saved file
        """
        try:
            if not os.path.exists(file_path):
                return {'exists': False}
            
            stat = os.stat(file_path)
            
            # Detect mime type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'exists': True,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'mime_type': mime_type,
                'is_image': mime_type in self.supported_image_types if mime_type else False,
                'is_document': mime_type in self.supported_document_types if mime_type else False
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {'exists': False, 'error': str(e)}

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from disk
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def cleanup_user_files(self, user_id: str, older_than_days: int = 30) -> int:
        """
        Clean up old files for a user
        
        Args:
            user_id: User identifier
            older_than_days: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            user_dir = os.path.join(self.upload_dir, user_id)
            if not os.path.exists(user_dir):
                return 0
            
            import time
            current_time = time.time()
            cutoff_time = current_time - (older_than_days * 24 * 60 * 60)
            
            deleted_count = 0
            for filename in os.listdir(user_dir):
                file_path = os.path.join(user_dir, filename)
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        if self.delete_file(file_path):
                            deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

    def get_supported_types(self) -> Dict[str, List[str]]:
        """
        Get list of supported file types
        """
        return {
            'images': list(self.supported_image_types),
            'documents': list(self.supported_document_types),
            'all': list(self.supported_types)
        }

# Global file handler instance
file_handler = FileHandler()