import os
from supabase import create_client, Client
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    
    def create_study_session(self, user_id: str, subject: str) -> str:
        """Create a new study session"""
        try:
            result = self.client.table('study_sessions').insert({
                'user_id': user_id,
                'session_type': 'chat',
                'subject': subject,
                'questions_answered': 0,
                'correct_answers': 0
            }).execute()
            
            return result.data[0]['id']
            
        except Exception as e:
            print(f"Error creating study session: {e}")
            return None

# Memory instance
memory = TawjihiMemory() 