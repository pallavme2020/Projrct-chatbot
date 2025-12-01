"""
Simple Logging System for RAG
"""

import json
from datetime import datetime
from pathlib import Path


class RAGLogger:
    """Log queries, responses, and system events"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"rag_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def log_query(self, query: str, answer: str, sources: list, 
                  confidence: float, response_time: float, session_id: str = "default"):
        """Log a query-response pair"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'query': query,
            'answer': answer,
            'num_sources': len(sources),
            'confidence': confidence,
            'response_time': response_time,
            'sources': [s.get('document', 'unknown') for s in sources]
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_error(self, error_message: str, query: str = ""):
        """Log errors"""
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'query': query,
            'error': error_message
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry) + '\n')
    
    def get_recent_logs(self, num_entries: int = 10) -> list:
        """Get recent log entries"""
        
        if not self.log_file.exists():
            return []
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        recent = lines[-num_entries:]
        return [json.loads(line) for line in recent]