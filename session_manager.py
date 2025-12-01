"""
Session Management for Multiple Conversations
"""

from typing import Dict, List
from datetime import datetime


class SessionManager:
    """Manage multiple conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self.active_session = "default"
    
    def create_session(self, session_id: str = None) -> str:
        """Create a new conversation session"""
        
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.sessions[session_id] = {
            'history': [],
            'created_at': datetime.now().isoformat(),
            'message_count': 0
        }
        
        self.active_session = session_id
        return session_id
    
    def switch_session(self, session_id: str):
        """Switch to a different session"""
        
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.active_session = session_id
    
    def add_to_history(self, question: str, answer: str, session_id: str = None):
        """Add exchange to session history"""
        
        sid = session_id or self.active_session
        
        if sid not in self.sessions:
            self.create_session(sid)
        
        self.sessions[sid]['history'].append({
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        })
        self.sessions[sid]['message_count'] += 1
    
    def get_history(self, session_id: str = None, last_n: int = 5) -> List[dict]:
        """Get conversation history"""
        
        sid = session_id or self.active_session
        
        if sid not in self.sessions:
            return []
        
        return self.sessions[sid]['history'][-last_n:]
    
    def clear_session(self, session_id: str = None):
        """Clear a session"""
        
        sid = session_id or self.active_session
        
        if sid in self.sessions:
            self.sessions[sid]['history'] = []
            self.sessions[sid]['message_count'] = 0
    
    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        return list(self.sessions.keys())
    
    def get_session_summary(self, session_id: str = None) -> dict:
        """Get session statistics"""
        
        sid = session_id or self.active_session
        
        if sid not in self.sessions:
            return {}
        
        session = self.sessions[sid]
        return {
            'session_id': sid,
            'message_count': session['message_count'],
            'created_at': session['created_at'],
            'is_active': sid == self.active_session
        }