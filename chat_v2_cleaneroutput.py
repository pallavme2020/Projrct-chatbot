"""
Enhanced Chat System with Smart Routing, Modes, and Two-Stage CoT
"""

import json
import ollama
import sys
import time
import threading
from typing import List, Dict, Tuple
from retrieval import ParallelAdvancedRetriever as AdvancedRetriever
from context_optimizer import ContextOptimizer
from query_classifier import QueryClassifier
from session_manager import SessionManager
from logger import RAGLogger
from response_modes import (
    MODE_CONFIGS, MODE_INSTRUCTIONS, ANALYSIS_PROMPT,
    ANSWER_PROMPT, SHORT_PROMPT, get_mode_banner, format_analysis_display
)


class ThinkingAnimation:
    """Show thinking animation while processing"""
    
    def __init__(self, message: str = "🤔 Processing"):
        self.message = message
        self.is_running = False
        self.thread = None
    
    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self.animate)
        self.thread.start()
    
    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
    
    def animate(self):
        dots = ['   ', '.  ', '.. ', '...']
        idx = 0
        
        while self.is_running:
            sys.stdout.write(f'\r{self.message}{dots[idx]}')
            sys.stdout.flush()
            idx = (idx + 1) % len(dots)
            time.sleep(0.3)


class EnhancedChatSystem:
    """RAG chat with smart routing and enterprise features"""
    
    def __init__(self, db_path: str = "db/acc.db",
                 model_name: str = "granite4:micro-h"):
        
        print("🔧 Initializing enhanced chat system...")
        
        self.retriever = AdvancedRetriever(db_path)
        self.optimizer = ContextOptimizer()
        self.classifier = QueryClassifier()
        self.session_manager = SessionManager()
        self.logger = RAGLogger()
        
        self.model_name = model_name
        
        print("✅ Enhanced chat system ready!\n")
    
    def ask(self, question: str, session_id: str = None) -> Dict:
        """Main ask method with smart routing"""
        
        start_time = time.time()
        
        # Step 1: Classify query (casual > memory > document)
        query_type, mode, intent = self.classifier.classify_full(question)
        
        # Get clean query (without mode prefix)
        _, clean_query = self.classifier.extract_mode_from_query(question)
        
        # Step 2: Route based on query type
        if query_type == 'casual':
            return self.handle_casual_chat(clean_query, start_time, session_id)
        
        elif query_type == 'memory':
            return self.handle_memory_question(clean_query, start_time, session_id)
        
        else:  # document
            return self.handle_document_question(
                clean_query, mode, intent, start_time, session_id
            )
    
    def handle_casual_chat(self, query: str, start_time: float, 
                          session_id: str = None) -> Dict:
        """Handle casual conversation - Fast path"""
        
        casual_responses = {
            'how are you': "I'm doing well, thank you for asking! How can I help you today?",
            'hello': "Hello! How can I assist you?",
            'hi': "Hi there! What can I help you with?",
            'hey': "Hey! What would you like to know?",
            'thanks': "You're welcome! Let me know if you need anything else.",
            'thank you': "You're very welcome! Happy to help anytime.",
            'bye': "Goodbye! Feel free to come back if you have more questions.",
            'goodbye': "Goodbye! Have a great day!",
            'good morning': "Good morning! How can I help you today?",
            'good night': "Good night! Sleep well!",
            'good evening': "Good evening! What can I do for you?",
            'good afternoon': "Good afternoon! How may I assist you?",
            'tell me about yourself': "I'm an AI assistant here to help you with your questions.",

            # Identity questions
            'tell me about yourself': "I'm Autoliv AI Knowledge Assistant, designed to help you find information from your documents quickly and accurately.",
            'who are you': "I'm Autoliv AI Knowledge Assistant, your intelligent document search companion.",
            'what are you': "I'm Autoliv AI Knowledge Assistant, specialized in retrieving and analyzing information from your document collection.",
            'introduce yourself': "Hello! I'm Autoliv AI Knowledge Assistant. I help you search through documents and provide accurate answers with proper citations.",
            'what can you do': "I'm Autoliv AI Knowledge Assistant. I can search your documents, answer questions, provide detailed or concise responses, and cite my sources.",
            'what do you do': "As Autoliv AI Knowledge Assistant, I retrieve information from documents and provide you with accurate, cited answers.",

            # Existing greetings...
            'how are you': "I'm doing well, thank you! I'm Autoliv AI Knowledge Assistant, ready to help you.",
            'hello': "Hello! I'm Autoliv AI Knowledge Assistant. How can I assist you today?"

        }
        
        query_lower = query.lower().strip()
        
        # Find matching response
        answer = None
        for phrase, response in casual_responses.items():
            if phrase in query_lower:
                answer = response
                break
        
        if not answer:
            answer = "I'm here to help! What would you like to know?"
        
        # Save to session
        sid = session_id or self.session_manager.active_session
        self.session_manager.add_to_history(query, answer, sid)
        
        # Log
        response_time = time.time() - start_time
        self.logger.log_query(query, answer, [], 1.0, response_time, sid)
        
        return {
            'answer': answer,
            'sources': [],
            'num_sources': 0,
            'query_type': 'casual',
            'confidence': 1.0,
            'response_time': response_time
        }
    
    def handle_memory_question(self, query: str, start_time: float,
                               session_id: str = None) -> Dict:
        """Handle memory questions - Session history"""
        
        thinking = ThinkingAnimation("⚛️  Checking memory")
        thinking.start()
        
        try:
            # Get conversation history
            history = self.session_manager.get_history(last_n=10)
            
            if not history:
                answer = "I don't have any previous conversation history to reference."
                confidence = 0.5
            else:
                # Generate answer from memory
                answer = self.generate_from_memory(query, history)
                confidence = 0.85
            
            thinking.stop()
            
            # Save to session
            sid = session_id or self.session_manager.active_session
            self.session_manager.add_to_history(query, answer, sid)
            
            # Log
            response_time = time.time() - start_time
            self.logger.log_query(query, answer, [], confidence, response_time, sid)
            
            return {
                'answer': answer,
                'sources': [],
                'num_sources': 0,
                'query_type': 'memory',
                'confidence': confidence,
                'response_time': response_time,
                'used_memory': True
            }
        
        except Exception as e:
            thinking.stop()
            return self.error_response(str(e), query, start_time, session_id)
    
    def handle_document_question(self, query: str, mode: str, intent: str,
                                start_time: float, session_id: str = None) -> Dict:
        """Handle document questions with modes and two-stage CoT"""
        
        config = MODE_CONFIGS[mode]
        
        # Show mode banner
        print(f"\n{get_mode_banner(mode, config)}\n")
        
        thinking = ThinkingAnimation(f"{config['emoji']} Processing")
        thinking.start()
        
        try:
            # Retrieve documents
            num_docs = config['num_docs']
            search_mode = config['search_mode']
            
            results = self.retriever.search(query, top_k=num_docs, mode=search_mode)
            
            if not results:
                thinking.stop()
                answer = "I couldn't find relevant information in the documents for your query."
                return self.build_response(
                    answer, [], query, mode, intent, 0.3, start_time, session_id
                )
            
            documents = [r['chunk_text'] for r in results]
            
            # Two-stage or single-stage generation
            if config['use_two_stage']:
                thinking.stop()
                answer, analysis = self.generate_two_stage(
                    query, documents, mode, intent, config
                )
            else:
                answer = self.generate_single_stage(
                    query, documents, mode, config
                )
                analysis = None
                thinking.stop()
            
            # Citation verification
            citation_check = self.optimizer.verify_citations(answer, documents)
            
            # Confidence scoring
            confidence = self.calculate_confidence(query, answer, results, citation_check)
            
            # Save to session
            sid = session_id or self.session_manager.active_session
            self.session_manager.add_to_history(query, answer, sid)
            
            # Log
            response_time = time.time() - start_time
            self.logger.log_query(
                query, answer, self.format_sources(results),
                confidence, response_time, sid
            )
            
            return {
                'answer': answer,
                'analysis': analysis,
                'sources': self.format_sources(results),
                'num_sources': len(results),
                'query_type': 'document',
                'mode': mode,
                'intent': intent,
                'confidence': confidence,
                'citation_check': citation_check,
                'response_time': response_time,
                'show_cot': config['show_cot']
            }
        
        except Exception as e:
            thinking.stop()
            return self.error_response(str(e), query, start_time, session_id)
    
    def generate_two_stage(self, query: str, documents: List[str],
                          mode: str, intent: str, config: dict) -> Tuple[str, str]:
        """Two-stage generation: Analysis then Answer"""
        
        # Stage 1: Analysis
        print("⚛️  Stage 1: Analyzing documents...\n")
        
        doc_context = self.format_documents_for_prompt(documents)
        analysis_prompt = ANALYSIS_PROMPT.format(
            documents=doc_context,
            query=query
        )
        
        analysis = self.call_llm(analysis_prompt, temperature=0.1, max_tokens=800)
        
        # Show analysis if configured
        if config['show_cot']:
            print(format_analysis_display(analysis))
            print()
        
        # Stage 2: Answer
        print("🔭 Stage 2: Generating answer...\n")
        
        answer_prompt = ANSWER_PROMPT.format(
            analysis=analysis,
            mode=mode.upper(),
            mode_instructions=MODE_INSTRUCTIONS[mode]
        )
        
        answer = self.call_llm(answer_prompt, temperature=0.2, max_tokens=1000)
        
        return answer, analysis
    
    def generate_single_stage(self, query: str, documents: List[str],
                             mode: str, config: dict) -> str:
        """Single-stage generation for short mode"""
        
        doc_context = self.format_documents_for_prompt(documents)
        
        prompt = SHORT_PROMPT.format(
            documents=doc_context,
            query=query,
            mode_instructions=MODE_INSTRUCTIONS[mode]
        )
        
        answer = self.call_llm(prompt, temperature=0.2, max_tokens=300)
        
        return answer
    
    def generate_from_memory(self, query: str, history: List[dict]) -> str:
        """Generate answer from conversation memory"""
        
        conversation_context = self.format_history(history)
        
        prompt = f"""Based on our conversation history:

{conversation_context}

Question: {query}

Answer the question using only information from our conversation history.
Be natural and conversational."""
        
        answer = self.call_llm(prompt, temperature=0.3, max_tokens=300)
        
        return answer
    
    def call_llm(self, prompt: str, temperature: float = 0.2,
                 max_tokens: int = 500) -> str:
        """Call LLM with error handling"""
        
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )
            return response['response'].strip()
        
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def format_documents_for_prompt(self, documents: List[str]) -> str:
        """Format documents with numbering"""
        
        formatted = []
        for i, doc in enumerate(documents, 1):
            formatted.append(f"[{i}] {doc}")
        
        return "\n\n".join(formatted)
    
    def format_history(self, history: List[dict]) -> str:
        """Format conversation history"""
        
        formatted = []
        for exchange in history:
            formatted.append(f"User: {exchange['question']}")
            formatted.append(f"Assistant: {exchange['answer']}")
        
        return "\n".join(formatted)
    
    def calculate_confidence(self, question: str, answer: str,
                           sources: List[Dict], citation_check: dict) -> float:
        """Calculate confidence score"""
        
        confidence = 1.0
        
        if not sources:
            confidence *= 0.5
        
        if citation_check.get('has_citations'):
            citation_accuracy = citation_check.get('citation_accuracy', 0)
            confidence *= citation_accuracy
        
        word_count = len(answer.split())
        if word_count < 10:
            confidence *= 0.6
        elif word_count > 300:
            confidence *= 0.9
        
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(question_words & answer_words)
        
        if overlap < 2:
            confidence *= 0.7
        
        return round(confidence, 2)
    
    def format_sources(self, results: List[Dict]) -> List[Dict]:
        """Format source information"""
        
        formatted_sources = []
        
        for idx, result in enumerate(results, 1):
            source_info = {
                'number': idx,
                'document': result.get('source', 'Unknown'),
                'relevance_score': round(result.get('score', 0.0), 2),
                'preview': result.get('chunk_text', '')[:100] + '...'
            }
            formatted_sources.append(source_info)
        
        return formatted_sources
    
    def build_response(self, answer: str, sources: List, query: str,
                      mode: str, intent: str, confidence: float,
                      start_time: float, session_id: str) -> Dict:
        """Build standardized response"""
        
        sid = session_id or self.session_manager.active_session
        self.session_manager.add_to_history(query, answer, sid)
        
        response_time = time.time() - start_time
        self.logger.log_query(query, answer, sources, confidence, response_time, sid)
        
        return {
            'answer': answer,
            'sources': sources,
            'num_sources': len(sources),
            'query_type': 'document',
            'mode': mode,
            'intent': intent,
            'confidence': confidence,
            'response_time': response_time
        }
    
    def error_response(self, error: str, query: str, start_time: float,
                      session_id: str = None) -> Dict:
        """Generate error response"""
        
        self.logger.log_error(error, query)
        
        return {
            'answer': f"Sorry, I encountered an error: {error}",
            'sources': [],
            'num_sources': 0,
            'confidence': 0.0,
            'response_time': time.time() - start_time
        }
    
    def display_response(self, result: Dict):
        """Display response with metadata"""
        
        # Show answer
        print(f"🟣▶ Answer:\n{result['answer']}\n")
        
        # Show analysis if available
        if result.get('show_cot') and result.get('analysis'):
            # Already shown during generation
            pass
        
        # Show confidence
        confidence = result.get('confidence', 0)
        confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
        print(f"{confidence_emoji} Confidence: {confidence*100:.0f}%")
        
        # Show sources or memory indicator
        if result['sources']:
            print(f"📚 {result['num_sources']} sections used")
        elif result.get('used_memory'):
            print("⚛️  (Answered from conversation memory)")
        
        # Show response time
        response_time = result.get('response_time', 0)
        print(f"⏱️  Response time: {response_time:.1f}s")
        
        print()
    
    def interactive_chat(self):
        
        print("═" * 60)
        print("🔭 Autoliv AI Knowledge Assistant")
        print("   Smart Document Search & Retrieval")
        print("═" * 60)
        print("\n📋 Response Modes:")
        print("  /detail        - Comprehensive analysis (400-600 words)")
        print("  /normal        - Balanced response (150-250 words) [DEFAULT]")
        print("  /shortconsize  - Brief answer (30-80 words)")
        print("\n⚙️  Commands:")
        print("  /clear     - Clear current session")
        print("  /sessions  - List all sessions")
        print("  /new       - Create new session")
        print("  /switch ID - Switch to session")
        print("  /logs      - Show recent logs")
        print("  /help      - Show this help")
        print("  /quit      - Exit")
        print("\n" + "═" * 60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input == '/quit':
                    print("\n👋 Goodbye!")
                    break
                
                elif user_input == '/clear':
                    self.session_manager.clear_session()
                    print("🗑️  Session cleared\n")
                    continue
                
                elif user_input == '/sessions':
                    sessions = self.session_manager.list_sessions()
                    print(f"\n📋 Sessions: {', '.join(sessions)}")
                    print(f"Active: {self.session_manager.active_session}\n")
                    continue
                
                elif user_input == '/new':
                    new_id = self.session_manager.create_session()
                    print(f"✨ New session created: {new_id}\n")
                    continue
                
                elif user_input.startswith('/switch'):
                    parts = user_input.split()
                    if len(parts) > 1:
                        self.session_manager.switch_session(parts[1])
                        print(f"🔄 Switched to: {parts[1]}\n")
                    continue
                
                elif user_input == '/logs':
                    logs = self.logger.get_recent_logs(5)
                    print("\n📊 Recent Logs:")
                    for log in logs:
                        print(f"  Q: {log.get('query', '')[:50]}...")
                        print(f"  Confidence: {log.get('confidence', 0)*100:.0f}%\n")
                    continue
                
                elif user_input == '/help':
                    print("\n📋 Response Modes:")
                    print("  /detail       - Comprehensive (400-600 words, 2-stage)")
                    print("  /normal       - Balanced (150-250 words, 2-stage)")
                    print("  /shortconsize - Brief (30-80 words, 1-stage)")
                    print("\n⚙️  Commands: /clear, /sessions, /new, /switch, /logs, /quit\n")
                    continue
                
                # Process question
                result = self.ask(user_input)
                
                # Display response
                self.display_response(result)
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    chat = EnhancedChatSystem("db/acc.db")
    chat.interactive_chat()