import os
from supabase import create_client, Client
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv
import uuid
import logging

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set up logging
logger = logging.getLogger(__name__)

class TawjihiMemory:
    """Memory system for TawjihiAI using existing Supabase infrastructure"""
    
    def __init__(self):
        self.client = supabase
    
    def get_or_create_conversation(self, user_id: str, teacher_id: str, title: Optional[str] = None) -> str:
        """Get existing conversation or create new one"""
        try:
            # Try to find existing conversation
            result = self.client.table('conversations').select('id').match({
                'user_id': user_id,
                'teacher_id': teacher_id
            }).order('updated_at', desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new conversation
            new_conversation = self.client.table('conversations').insert({
                'user_id': user_id,
                'teacher_id': teacher_id,
                'title': title or f"Chat with {teacher_id.title()} Teacher"
            }).execute()
            
            return new_conversation.data[0]['id']
            
        except Exception as e:
            print(f"Error managing conversation: {e}")
            return None
    
    def save_message(self, conversation_id: str, content: str, role: str) -> bool:
        """Save a message to the conversation"""
        try:
            self.client.table('messages').insert({
                'conversation_id': conversation_id,
                'content': content,
                'role': role  # 'user' or 'assistant'
            }).execute()
            
            # Update conversation timestamp
            self.client.table('conversations').update({
                'updated_at': datetime.now().isoformat()
            }).eq('id', conversation_id).execute()
            
            return True
            
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        try:
            result = self.client.table('messages').select('content, role, created_at').eq(
                'conversation_id', conversation_id
            ).order('created_at', desc=False).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def create_study_session(self, user_id: str, subject: str) -> Optional[str]:
        """
        Create a new study session compatible with the actual database schema.
        This method handles the mismatch between expected simple schema and actual complex schema.
        """
        try:
            # First, try to get or create a subject for this user
            subject_id = self._get_or_create_subject(user_id, subject)
            if not subject_id:
                logger.warning(f"Failed to get or create subject for user {user_id}, subject {subject}")
                return None
            
            # Convert user_id to UUID format if it's not already
            user_uuid = self._ensure_uuid_format(user_id)
            if not user_uuid:
                logger.warning(f"Invalid user_id format: {user_id}")
                return None
                
            # Create study session with actual schema
            result = self.client.table('study_sessions').insert({
                'user_id': user_uuid,
                'subject_id': subject_id,
                'duration_minutes': 0,
                'topics_covered': [subject],  # Use subject name as initial topic
                'notes': f'Chat session with {subject} tutor',
                'score': None,  # No score for chat sessions
                'session_date': datetime.now().isoformat()
            }).execute()
            
            if result.data:
                logger.info(f"Created study session {result.data[0]['id']} for user {user_id}")
                return result.data[0]['id']
            else:
                logger.warning("Study session creation returned no data")
                return None
            
        except Exception as e:
            logger.error(f"Error creating study session for user {user_id}, subject {subject}: {e}")
            # Don't fail the entire conversation if study session creation fails
            return None
    
    def _get_or_create_subject(self, user_id: str, subject_name: str) -> Optional[str]:
        """Get existing subject or create new one for the user"""
        try:
            user_uuid = self._ensure_uuid_format(user_id)
            if not user_uuid:
                return None
                
            # Try to find existing subject
            result = self.client.table('subjects').select('id').match({
                'user_id': user_uuid,
                'name': subject_name
            }).limit(1).execute()
            
            if result.data:
                return result.data[0]['id']
            
            # Create new subject
            subject_mapping = {
                'math': {'name': 'Mathematics', 'description': 'Tawjihi Mathematics curriculum', 'grade_level': 'Grade 12'},
                'arabic': {'name': 'Arabic Language', 'description': 'Arabic language and literature', 'grade_level': 'Grade 12'},
                'english': {'name': 'English Language', 'description': 'English language skills', 'grade_level': 'Grade 12'}
            }
            
            subject_info = subject_mapping.get(subject_name.lower(), {
                'name': subject_name.title(),
                'description': f'{subject_name.title()} subject',
                'grade_level': 'Grade 12'
            })
            
            new_subject = self.client.table('subjects').insert({
                'user_id': user_uuid,
                'name': subject_info['name'],
                'description': subject_info['description'],
                'grade_level': subject_info['grade_level'],
                'difficulty_level': 'intermediate',
                'study_hours_target': 100  # Default target
            }).execute()
            
            if new_subject.data:
                logger.info(f"Created new subject {subject_info['name']} for user {user_id}")
                return new_subject.data[0]['id']
            else:
                logger.warning(f"Failed to create subject {subject_name} for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error managing subject {subject_name} for user {user_id}: {e}")
            return None
    
    def _ensure_uuid_format(self, user_id: str) -> Optional[str]:
        """
        Ensure user_id is in UUID format. 
        If it's a simple string, try to convert or create a deterministic UUID.
        """
        try:
            # Check if it's already a valid UUID
            uuid.UUID(user_id)
            return user_id
        except ValueError:
            # If not a UUID, create a deterministic UUID from the string
            # This ensures the same user_id always maps to the same UUID
            import hashlib
            namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
            deterministic_uuid = uuid.uuid5(namespace, user_id)
            logger.info(f"Converted user_id '{user_id}' to UUID '{deterministic_uuid}'")
            return str(deterministic_uuid)
    
    def get_user_subjects(self, user_id: str) -> List[Dict]:
        """Get all subjects for a user (new functionality)"""
        try:
            user_uuid = self._ensure_uuid_format(user_id)
            if not user_uuid:
                return []
                
            result = self.client.table('subjects').select('*').eq('user_id', user_uuid).execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting subjects for user {user_id}: {e}")
            return []
    
    def get_user_study_sessions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent study sessions for a user (new functionality)"""
        try:
            user_uuid = self._ensure_uuid_format(user_id)
            if not user_uuid:
                return []
                
            result = self.client.table('study_sessions').select(
                '*, subjects(name, description)'
            ).eq('user_id', user_uuid).order('session_date', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting study sessions for user {user_id}: {e}")
            return []

# Memory instance
memory = TawjihiMemory() 