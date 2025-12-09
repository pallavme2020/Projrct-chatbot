"""
Enhanced Chat System with Professional CLI Interface
"""

import json
import ollama
import time
from typing import List, Dict, Tuple

from retrieval import ParallelAdvancedRetriever as AdvancedRetriever
from context_optimizer import ContextOptimizer
from query_classifier import QueryClassifier
from session_manager import SessionManager
from logger import RAGLogger
from response_modes import (
    MODE_CONFIGS, MODE_INSTRUCTIONS, ANALYSIS_PROMPT,
    ANSWER_PROMPT, SHORT_PROMPT
)
from cli_ui import ProfessionalCLI, StreamingSpinner


class EnhancedChatSystem:
    """RAG chat with professional CLI interface"""
    
    def __init__(self, db_path: str = "db/acc.db",
                 model_name: str = "granite4:micro-h"):
        
        # Initialize CLI
        self.cli = ProfessionalCLI()
        
        self.cli.show_info("Initializing enhanced chat system...")
        
        self.retriever = AdvancedRetriever(db_path)
        self.optimizer = ContextOptimizer()
        self.classifier = QueryClassifier()
        self.session_manager = SessionManager()
        self.logger = RAGLogger()
        
        self.model_name = model_name
        
        self.cli.show_success("Enhanced chat system ready!")
    
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
            'tell me about yourself': "I'm Autoliv AI Knowledge Assistant, designed to help you find information from your documents quickly and accurately.",
            'who are you': "I'm Autoliv AI Knowledge Assistant, your intelligent document search companion.",
            'what are you': "I'm Autoliv AI Knowledge Assistant, specialized in retrieving and analyzing information from your document collection.",
            'introduce yourself': "Hello! I'm Autoliv AI Knowledge Assistant. I help you search through documents and provide accurate answers with proper citations.",
            'what can you do': "I'm Autoliv AI Knowledge Assistant. I can search your documents, answer questions, provide detailed or concise responses, and cite my sources.",
            'what do you do': "As Autoliv AI Knowledge Assistant, I retrieve information from documents and provide you with accurate, cited answers."
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
        
        spinner = StreamingSpinner(self.cli.console, "🧠 Checking memory")
        spinner.start()
        
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
            
            spinner.stop()
            
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
        
        except Exception as error:
            spinner.stop()
            return self.error_response(str(error), query, start_time, session_id)
    
    def handle_document_question(self, query: str, mode: str, intent: str,
                                start_time: float, session_id: str = None) -> Dict:
        """Handle document questions with modes and two-stage CoT"""
        
        config = MODE_CONFIGS[mode]
        
        # Show mode banner
        self.cli.show_mode_banner(mode, config)
        
        spinner = StreamingSpinner(self.cli.console, f"{config['emoji']} Processing")
        spinner.start()
        
        try:
            # Retrieve documents
            num_docs = config['num_docs']
            search_mode = config['search_mode']
            
            self.cli.show_processing_stage("Searching documents", "🔍")
            results = self.retriever.search(query, top_k=num_docs, mode=search_mode)
            
            if not results:
                spinner.stop()
                answer = "I couldn't find relevant information in the documents for your query."
                return self.build_response(
                    answer, [], query, mode, intent, 0.3, start_time, session_id
                )
            
            documents = [r['chunk_text'] for r in results]
            
            # Two-stage or single-stage generation
            if config['use_two_stage']:
                spinner.stop()
                self.cli.show_processing_stage("Analyzing documents", "💭")
                answer, analysis = self.generate_two_stage(
                    query, documents, mode, intent, config
                )
            else:
                self.cli.show_processing_stage("Generating answer", "✍️")
                answer = self.generate_single_stage(
                    query, documents, mode, config
                )
                analysis = None
                spinner.stop()
            
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
        
        except Exception as error:
            spinner.stop()
            return self.error_response(str(error), query, start_time, session_id)
    
    def generate_two_stage(self, query: str, documents: List[str],
                          mode: str, intent: str, config: dict) -> Tuple[str, str]:
        """Two-stage generation: Analysis then Answer"""
        
        # Stage 1: Analysis
        doc_context = self.format_documents_for_prompt(documents)
        analysis_prompt = ANALYSIS_PROMPT.format(
            documents=doc_context,
            query=query
        )
        
        analysis = self.call_llm(analysis_prompt, temperature=0.1, max_tokens=800)
        
        # Show analysis if configured
        if config['show_cot']:
            self.cli.show_analysis(analysis)
        
        # Stage 2: Answer
        self.cli.show_processing_stage("Generating answer", "🔭")
        
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
        
        except Exception as error:
            return f"Error generating response: {str(error)}"
    
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
        """Display response with professional formatting"""
        
        # Stream the answer
        self.cli.stream_response(result['answer'])
        
        # Show analysis if available
        if result.get('show_cot') and result.get('analysis'):
            # Already shown during generation
            pass
        
        # Show metadata
        self.cli.show_response_metadata(result)
        
        # Show sources if available
        if result['sources']:
            self.cli.show_sources(result['sources'])
    
    def interactive_chat(self):
        """Main interactive chat loop"""
        
        # Clear screen and show welcome
        self.cli.clear_screen()
        self.cli.show_welcome_banner()
        self.cli.show_response_modes()
        self.cli.show_commands()
        
        while True:
            try:
                user_input = self.cli.get_user_input()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input == '/quit':
                    self.cli.show_goodbye()
                    break
                
                elif user_input == '/clear':
                    self.session_manager.clear_session()
                    self.cli.show_success("Session cleared")
                    continue
                
                elif user_input == '/sessions':
                    sessions = self.session_manager.list_sessions()
                    self.cli.show_sessions(sessions, self.session_manager.active_session)
                    continue
                
                elif user_input == '/new':
                    new_id = self.session_manager.create_session()
                    self.cli.show_success(f"New session created: {new_id}")
                    continue
                
                elif user_input.startswith('/switch'):
                    parts = user_input.split()
                    if len(parts) > 1:
                        self.session_manager.switch_session(parts[1])
                        self.cli.show_success(f"Switched to: {parts[1]}")
                    continue
                
                elif user_input == '/logs':
                    logs = self.logger.get_recent_logs(5)
                    self.cli.show_logs(logs)
                    continue
                
                elif user_input == '/help':
                    self.cli.show_help()
                    continue
                
                # Process question
                result = self.ask(user_input)
                
                # Display response
                self.display_response(result)
            
            except KeyboardInterrupt:
                self.cli.show_goodbye()
                break
            
            except Exception as error:
                self.cli.show_error(str(error))


if __name__ == "__main__":
    chat = EnhancedChatSystem("db/acc.db")
    chat.interactive_chat()
