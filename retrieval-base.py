"""
Advanced Retrieval System with Multi-Stage Pipeline
"""

import sqlite3
import numpy as np
from typing import List, Tuple, Dict
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Plus

from query_processor import QueryProcessor, split_into_sentences


class AdvancedRetriever:
    """Multi-stage retrieval with all advanced techniques"""
    
    def __init__(self, db_path: str = "db/acc.db"):
        self.db_path = db_path
        
        # Models
        print("Loading retrieval models...")
        self.embedder = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 50MB
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')  # 90MB
        
        # Query processor
        self.query_processor = QueryProcessor()
        
        print("✅ Retrieval system ready")
    
    def search(self, query: str, top_k: int = 3, mode: str = 'thorough') -> List[Dict]:
        """
        Main search interface with multiple modes
        
        Modes:
        - fast: Quick search (1 stage)
        - standard: Balanced (2 stages)
        - thorough: Full pipeline (all stages)
        """
        
        if mode == 'fast':
            return self.fast_search(query, top_k)
        elif mode == 'standard':
            return self.standard_search(query, top_k)
        else:
            return self.thorough_search(query, top_k)
    
    def fast_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Fast single-stage search"""
        
        print("🔍 Fast search mode...")
        
        # Just vector search
        results = self.vector_search(query, k=top_k)
        return results
    
    def standard_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Standard two-stage search"""
        
        print("🔍 Standard search mode...")
        
        # Stage 1: Hybrid retrieval
        print("  → Hybrid retrieval...")
        vector_results = self.vector_search(query, k=20)
        bm25_results = self.bm25_search(query, k=20)
        
        # Combine with RRF
        combined = self.reciprocal_rank_fusion([
            vector_results,
            bm25_results
        ])
        
        # Stage 2: Reranking
        print("  → Reranking...")
        reranked = self.rerank_with_cross_encoder(query, combined[:15], top_k)
        
        return reranked
    
    def thorough_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Thorough multi-stage search with all techniques"""
        
        print("🔍 Thorough search mode...")
        
        # Stage 1: Query Enhancement
        print("  → Enhancing query...")
        sub_queries = self.query_processor.decompose_query(query)
        search_variations = self.query_processor.generate_search_variations(query)
        hypothetical_doc = self.query_processor.create_hypothetical_document(query)
        
        all_queries = [query] + sub_queries + search_variations + [hypothetical_doc]
        all_queries = list(dict.fromkeys(all_queries))[:7]  # Limit to 7
        
        # Stage 2: Multi-source Retrieval
        print("  → Multi-source retrieval...")
        all_results = []
        
        for q in all_queries[:5]:  # Use top 5 variations
            # Vector search
            vec_results = self.vector_search(q, k=10)
            all_results.extend(vec_results)
            
            # BM25 search
            bm25_results = self.bm25_search(q, k=10)
            all_results.extend(bm25_results)
        
        # Deduplicate
        seen = set()
        unique_results = []
        for result in all_results:
            if result['chunk_text'] not in seen:
                seen.add(result['chunk_text'])
                unique_results.append(result)
        
        # Stage 3: Multi-Vector Retrieval
        print("  → Multi-vector scoring...")
        multi_vec_results = self.multi_vector_search(query, unique_results[:50], k=30)
        
        # Stage 4: Cross-Encoder Reranking
        print("  → Cross-encoder reranking...")
        reranked = self.rerank_with_cross_encoder(query, multi_vec_results, top_k=20)
        
        # Stage 5: Diversity Filtering
        print("  → Diversity filtering...")
        final_results = self.apply_diversity_filter(reranked, threshold=0.85, max_results=top_k)
        
        return final_results
    
    def vector_search(self, query: str, k: int = 10,
                     embedding_type: str = 'full') -> List[Dict]:
        """Dense vector search"""
        
        query_embedding = self.embedder.encode([query])[0]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all embeddings of specified type
        cursor.execute("""
            SELECT d.id, d.source, d.chunk_text, d.metadata, e.embedding
            FROM docs d
            JOIN embeddings e ON d.id = e.doc_id
            WHERE e.embedding_type = ?
        """, (embedding_type,))
        
        results = []
        for row in cursor.fetchall():
            doc_id, source, chunk_text, metadata, emb_bytes = row
            
            # Convert bytes to numpy array
            embedding = np.frombuffer(emb_bytes, dtype=np.float32)
            
            # Calculate similarity
            similarity = cosine_similarity(
                [query_embedding],
                [embedding]
            )[0][0]
            
            results.append({
                'id': doc_id,
                'source': source,
                'chunk_text': chunk_text,
                'metadata': metadata,
                'score': float(similarity)
            })
        
        conn.close()
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]
    
    def bm25_search(self, query: str, k: int = 10) -> List[Dict]:
        """Keyword-based BM25 search"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all documents
        cursor.execute("""
            SELECT id, source, chunk_text, metadata
            FROM docs
        """)
        
        all_docs = cursor.fetchall()
        conn.close()
        
        if not all_docs:
            return []
        
        # Tokenize
        corpus = [doc[2].lower().split() for doc in all_docs]
        
        # Build BM25 index
        bm25 = BM25Plus(corpus)
        
        # Search
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
        
        # Get top-k
        top_indices = np.argsort(scores)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            doc_id, source, chunk_text, metadata = all_docs[idx]
            results.append({
                'id': doc_id,
                'source': source,
                'chunk_text': chunk_text,
                'metadata': metadata,
                'score': float(scores[idx])
            })
        
        return results
    
    def multi_vector_search(self, query: str, candidates: List[Dict],
                           k: int = 10) -> List[Dict]:
        """Late interaction multi-vector search"""
        
        query_embedding = self.embedder.encode([query])[0]
        
        scores = []
        for candidate in candidates:
            text = candidate['chunk_text']
            
            # Split into sentences
            sentences = split_into_sentences(text)
            
            if not sentences:
                scores.append((0.0, candidate))
                continue
            
            # Encode all sentences
            sentence_embeddings = self.embedder.encode(sentences)
            
            # Calculate max similarity (late interaction)
            similarities = cosine_similarity(
                [query_embedding],
                sentence_embeddings
            )[0]
            
            max_similarity = float(np.max(similarities))
            scores.append((max_similarity, candidate))
        
        # Sort by max similarity
        scores.sort(key=lambda x: x[0], reverse=True)
        
        # Update scores in results
        results = []
        for score, candidate in scores[:k]:
            candidate['multi_vec_score'] = score
            results.append(candidate)
        
        return results
    
    def rerank_with_cross_encoder(self, query: str, documents: List[Dict],
                                  top_k: int = 3) -> List[Dict]:
        """Rerank using cross-encoder"""
        
        if not documents:
            return []
        
        # Create query-document pairs
        texts = [doc['chunk_text'] for doc in documents]
        pairs = [[query, text] for text in texts]
        
        # Score with cross-encoder
        scores = self.reranker.predict(pairs, show_progress_bar=False)
        
        # Sort by cross-encoder score
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Update scores
        results = []
        for doc, score in doc_scores[:top_k]:
            doc['rerank_score'] = float(score)
            results.append(doc)
        
        return results
    
    def reciprocal_rank_fusion(self, result_lists: List[List[Dict]],
                               k: int = 60) -> List[Dict]:
        """Combine multiple result lists using RRF"""
        
        scores = {}
        
        for result_list in result_lists:
            for rank, result in enumerate(result_list, 1):
                doc_id = result['chunk_text']  # Use text as ID
                
                if doc_id not in scores:
                    scores[doc_id] = {'score': 0, 'result': result}
                
                scores[doc_id]['score'] += 1.0 / (k + rank)
        
        # Sort by RRF score
        sorted_items = sorted(
            scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [item['result'] for item in sorted_items]
    
    def apply_diversity_filter(self, documents: List[Dict],
                               threshold: float = 0.85,
                               max_results: int = 5) -> List[Dict]:
        """Remove near-duplicate documents"""
        
        if len(documents) <= 1:
            return documents
        
        # Get embeddings
        texts = [doc['chunk_text'] for doc in documents]
        embeddings = self.embedder.encode(texts)
        
        diverse_docs = [documents[0]]
        diverse_embeddings = [embeddings[0]]
        
        for i in range(1, len(documents)):
            doc = documents[i]
            doc_embedding = embeddings[i]
            
            # Check similarity with selected docs
            similarities = cosine_similarity(
                [doc_embedding],
                diverse_embeddings
            )[0]
            
            if max(similarities) < threshold:
                diverse_docs.append(doc)
                diverse_embeddings.append(doc_embedding)
            
            if len(diverse_docs) >= max_results:
                break
        
        return diverse_docs


# Example usage
if __name__ == "__main__":
    retriever = AdvancedRetriever("db/acc.db")
    
    # Fast search
    results = retriever.search("What is machine learning?", top_k=3, mode='fast')
    
    # Thorough search
    results = retriever.search("Explain neural networks", top_k=3, mode='thorough')
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['source']}")
        print(f"   {result['chunk_text'][:200]}...")