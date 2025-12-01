"""
Context Optimization Module - With Citation Verification
"""

from typing import List, Tuple
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from query_processor import split_into_sentences


class ContextOptimizer:
    """Optimize retrieved context for better LLM generation"""
    
    def __init__(self, model_name: str = 'paraphrase-MiniLM-L3-v2'):
        self.model = SentenceTransformer(model_name)
    
    def compress_documents(self, query: str, documents: List[str], 
                          sentences_per_doc: int = 3) -> List[str]:
        """Extract only relevant sentences from each document"""
        
        query_embedding = self.model.encode([query])[0]
        compressed = []
        
        for doc in documents:
            sentences = split_into_sentences(doc)
            
            if len(sentences) <= sentences_per_doc:
                compressed.append(doc)
                continue
            
            sentence_embeddings = self.model.encode(sentences)
            similarities = cosine_similarity([query_embedding], sentence_embeddings)[0]
            
            top_indices = np.argsort(similarities)[-sentences_per_doc:]
            top_indices = sorted(top_indices)
            
            relevant_sentences = [sentences[i] for i in top_indices]
            compressed.append(' '.join(relevant_sentences))
        
        return compressed
    
    def reorder_lost_in_middle(self, documents: List[str]) -> List[str]:
        """Reorder docs to avoid lost-in-the-middle effect"""
        
        if len(documents) <= 2:
            return documents
        
        reordered = []
        for i in range(len(documents)):
            if i % 2 == 0:
                reordered.insert(0, documents[i])
            else:
                reordered.append(documents[i])
        
        return reordered
    
    def apply_diversity_filter(self, documents: List[str], 
                               similarity_threshold: float = 0.85,
                               max_docs: int = 10) -> List[str]:
        """Remove near-duplicate documents"""
        
        if len(documents) <= 1:
            return documents
        
        doc_embeddings = self.model.encode(documents)
        diverse_docs = [documents[0]]
        diverse_embeddings = [doc_embeddings[0]]
        
        for i in range(1, len(documents)):
            doc_embedding = doc_embeddings[i]
            similarities = cosine_similarity([doc_embedding], diverse_embeddings)[0]
            
            if max(similarities) < similarity_threshold:
                diverse_docs.append(documents[i])
                diverse_embeddings.append(doc_embedding)
            
            if len(diverse_docs) >= max_docs:
                break
        
        return diverse_docs
    
    def create_hierarchical_context(self, query: str, documents: List[str],
                                    metadata: List[dict] = None) -> str:
        """Format context hierarchically"""
        
        context = f"# Query: {query}\n\n"
        context += "## Summary\n"
        summary_text = ' '.join([doc[:200] + '...' for doc in documents[:3]])
        context += f"{summary_text}\n\n"
        context += "## Detailed Sources\n\n"
        
        for i, doc in enumerate(documents, 1):
            context += f"### Source {i}"
            
            if metadata and i - 1 < len(metadata):
                meta = metadata[i - 1]
                if 'source' in meta:
                    context += f" - {meta['source']}"
            
            context += f"\n{doc}\n\n"
        
        return context
    
    def verify_citations(self, answer: str, sources: List[str]) -> dict:
        """Verify if citations in answer actually exist in sources"""
        
        citation_pattern = r'\[(\d+)\]'
        cited_numbers = re.findall(citation_pattern, answer)
        
        if not cited_numbers:
            return {
                'has_citations': False,
                'valid_citations': [],
                'invalid_citations': [],
                'citation_accuracy': 0.0
            }
        
        cited_numbers = [int(n) for n in cited_numbers]
        valid_citations = [n for n in cited_numbers if 1 <= n <= len(sources)]
        invalid_citations = [n for n in cited_numbers if n > len(sources) or n < 1]
        
        accuracy = len(valid_citations) / len(cited_numbers) if cited_numbers else 0.0
        
        return {
            'has_citations': True,
            'valid_citations': valid_citations,
            'invalid_citations': invalid_citations,
            'citation_accuracy': accuracy,
            'total_citations': len(cited_numbers)
        }
    
    def check_answer_quality(self, query: str, answer: str, 
                            context: str) -> dict:
        """Check answer quality and identify issues"""
        
        issues = []
        
        if '[' not in answer or ']' not in answer:
            issues.append("No source citations found")
        
        word_count = len(answer.split())
        if word_count < 20:
            issues.append("Answer too brief (less than 20 words)")
        elif word_count > 500:
            issues.append("Answer too verbose (over 500 words)")
        
        from query_processor import QueryProcessor
        processor = QueryProcessor()
        
        context_terms = set(processor.extract_key_terms(context[:1000]))
        answer_terms = set(processor.extract_key_terms(answer))
        
        overlap = len(context_terms & answer_terms)
        if overlap < 2:
            issues.append("Answer doesn't use provided context")
        
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        query_coverage = len(query_words & answer_words) / max(len(query_words), 1)
        
        if query_coverage < 0.2:
            issues.append("Answer doesn't address query terms")
        
        quality_score = max(0.0, 1.0 - (len(issues) * 0.2))
        
        return {
            'has_issues': len(issues) > 0,
            'issues': issues,
            'quality_score': quality_score,
            'word_count': word_count
        }
    
    def optimize_full_context(self, query: str, documents: List[str],
                             metadata: List[dict] = None) -> Tuple[str, List[str]]:
        """Apply all optimization techniques"""
        
        compressed = self.compress_documents(query, documents)
        diverse = self.apply_diversity_filter(compressed)
        reordered = self.reorder_lost_in_middle(diverse)
        formatted_context = self.create_hierarchical_context(query, reordered, metadata)
        
        return formatted_context, reordered