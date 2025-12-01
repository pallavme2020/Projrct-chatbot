"""
Query Classification, Intent Detection, and Mode Extraction
"""

from typing import Tuple


class QueryClassifier:
    """Classify queries, detect intent, and extract modes"""
    
    def __init__(self):
        self.casual_phrases = [
            'how are you', 'hello', 'hi', 'hey', 'thanks', 
            'thank you', 'bye', 'goodbye', 'good morning', 
            'good night', 'what\'s up', 'sup', 'nice to meet',
            'how do you do', 'good evening', 'good afternoon',
            'tell me about yourself',
            'who are you',
            'what are you',
            'introduce yourself',
            'what can you do',
            'what do you do',
            'your name',
            'are you a bot',
            'are you ai',
            'are you human'
        ]
        
        self.memory_keywords = [
            'my name', 'i told you', 'i said', 'i mentioned',
            'remember', 'what did i', 'do you know my',
            'i am', "i'm", 'we discussed', 'earlier',
            'before', 'previous', 'you said', 'last time'
        ]
        
        self.intent_keywords = {
            'explain': ['explain', 'what is', 'what are', 'define', 'describe'],
            'compare': ['compare', 'difference', 'versus', 'vs', 'better'],
            'list': ['list', 'show me', 'give me', 'what are the'],
            'summarize': ['summarize', 'summary', 'overview', 'brief'],
            'howto': ['how to', 'how do', 'how can', 'steps to'],
            'factual': ['when', 'where', 'who', 'which']
        }
    
    def extract_mode_from_query(self, query: str) -> Tuple[str, str]:
        """Extract mode from query and return clean query"""
        
        query_lower = query.lower().strip()
        
        # Check for mode prefix
        if query_lower.startswith('/detail'):
            clean_query = query[7:].strip()
            return 'detail', clean_query
        
        elif query_lower.startswith('/shortconsize'):
            clean_query = query[13:].strip()
            return 'shortconsize', clean_query
        
        elif query_lower.startswith('/short'):
            clean_query = query[6:].strip()
            return 'shortconsize', clean_query
        
        elif query_lower.startswith('/normal'):
            clean_query = query[7:].strip()
            return 'normal', clean_query
        
        # Default mode
        return 'normal', query
    
    def is_casual_conversation(self, query: str) -> bool:
        """Detect casual chat - HIGHEST PRIORITY"""
        
        query_lower = query.lower().strip()
        
        # Check for exact matches or contains
        for phrase in self.casual_phrases:
            if phrase == query_lower or phrase in query_lower:
                return True
        
        return False
    
    def is_memory_question(self, query: str) -> bool:
        """Detect memory/history questions"""
        
        query_lower = query.lower().strip()
        
        for keyword in self.memory_keywords:
            if keyword in query_lower:
                return True
        
        return False
    
    def classify_query_type(self, query: str) -> str:
        """
        Classify query into: casual, memory, or document
        Priority: casual > memory > document
        """
        
        # Priority 1: Casual conversation
        if self.is_casual_conversation(query):
            return 'casual'
        
        # Priority 2: Memory question
        if self.is_memory_question(query):
            return 'memory'
        
        # Priority 3: Document question (default)
        return 'document'
    
    def detect_intent(self, query: str) -> str:
        """Detect user intent for document questions"""
        
        query_lower = query.lower()
        
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def classify_full(self, query: str) -> Tuple[str, str, str]:
        """
        Get query type, mode, and intent
        Returns: (query_type, mode, intent)
        """
        
        # Extract mode first
        mode, clean_query = self.extract_mode_from_query(query)
        
        # Classify type
        query_type = self.classify_query_type(clean_query)
        
        # Detect intent (only for document questions)
        if query_type == 'document':
            intent = self.detect_intent(clean_query)
        else:
            intent = 'general'
        
        return query_type, mode, intent
    
    def should_use_two_stage(self, query_type: str, mode: str) -> bool:
        """Decide if two-stage generation is needed"""
        
        # Never for casual or memory
        if query_type in ['casual', 'memory']:
            return False
        
        # Use two-stage for detail and normal modes
        if mode in ['detail', 'normal']:
            return True
        
        # Skip for short mode (speed priority)
        return False