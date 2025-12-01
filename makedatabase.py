"""
Enhanced Database Builder with LangChain Document Loaders
"""

import os
import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# LangChain Document Loaders
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
    JSONLoader,
    DirectoryLoader
)


class EnhancedDatabaseBuilder:
    """Build database with multi-vector support and LangChain loaders"""
    
    def __init__(self, db_path: str = "db/acc.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        
        # Small fast model for embeddings
        print("Loading embedding model...")
        self.model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
        
        # Document loaders mapping
        self.loader_mapping = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.doc': Docx2txtLoader,
            '.xlsx': UnstructuredExcelLoader,
            '.xls': UnstructuredExcelLoader,
            '.md': UnstructuredMarkdownLoader,
            '.html': UnstructuredHTMLLoader,
            '.htm': UnstructuredHTMLLoader,
            '.csv': CSVLoader,
            '.json': JSONLoader
        }
    
    def ensure_db_directory(self):
        """Create database directory if needed"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def initialize_database(self):
        """Create database tables"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Embeddings table (multi-vector support)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                embedding_type TEXT NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES docs(id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_source 
            ON docs(source)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embedding_doc 
            ON embeddings(doc_id, embedding_type)
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database initialized: {self.db_path}")
    
    def load_documents_with_langchain(self, path: str) -> List[Dict]:
        """Load documents using LangChain loaders"""
        
        documents = []
        path_obj = Path(path)
        
        if path_obj.is_file():
            # Single file
            docs = self.load_single_file(path)
            documents.extend(docs)
        
        elif path_obj.is_dir():
            # Directory - load all supported files
            print(f"📁 Scanning directory: {path}")
            
            for file_path in path_obj.rglob('*'):
                if file_path.is_file() and file_path.suffix in self.loader_mapping:
                    docs = self.load_single_file(str(file_path))
                    documents.extend(docs)
        
        else:
            print(f"❌ Path not found: {path}")
        
        return documents
    
    def load_single_file(self, file_path: str) -> List[Dict]:
        """Load a single file using appropriate loader"""
        
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()
        
        if extension not in self.loader_mapping:
            print(f"⚠️ Unsupported file type: {extension}")
            return []
        
        try:
            loader_class = self.loader_mapping[extension]
            
            # Special handling for JSON
            if extension == '.json':
                loader = loader_class(
                    file_path=file_path,
                    jq_schema='.',
                    text_content=False
                )
            else:
                loader = loader_class(file_path)
            
            # Load documents
            langchain_docs = loader.load()
            
            # Convert to our format
            documents = []
            for doc in langchain_docs:
                documents.append({
                    'content': doc.page_content,
                    'metadata': {
                        'source': str(file_path),
                        **doc.metadata
                    }
                })
            
            print(f"✅ Loaded: {file_path_obj.name} ({len(documents)} chunks)")
            return documents
        
        except Exception as e:
            print(f"❌ Error loading {file_path_obj.name}: {str(e)}")
            return []
    
    def chunk_document(self, text: str, chunk_size: int = 512,
                      overlap: int = 50) -> List[str]:
        """Chunk document with sentence-aware splitting"""
        
        from query_processor import split_into_sentences
        
        sentences = split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_size + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_size += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def create_multi_vector_embeddings(self, text: str) -> Dict[str, np.ndarray]:
        """Create multiple embeddings per chunk"""
        
        embeddings = {}
        
        # 1. Full text embedding
        embeddings['full'] = self.model.encode([text])[0]
        
        # 2. First sentence (often contains main idea)
        from query_processor import split_into_sentences
        sentences = split_into_sentences(text)
        
        if sentences:
            embeddings['first_sentence'] = self.model.encode([sentences[0]])[0]
        
        # 3. Key terms embedding
        from query_processor import QueryProcessor
        processor = QueryProcessor()
        key_terms = processor.extract_key_terms(text)
        
        if key_terms:
            embeddings['keywords'] = self.model.encode([' '.join(key_terms[:10])])[0]
        
        return embeddings
    
    def build_database(self, paths: List[str], chunk_size: int = 512):
        """Build database from document paths"""
        
        print("=" * 60)
        print("🚀 Starting Enhanced Database Build")
        print("=" * 60)
        
        # Initialize database
        self.initialize_database()
        
        # Load all documents
        all_documents = []
        for path in paths:
            docs = self.load_documents_with_langchain(path)
            all_documents.extend(docs)
        
        if not all_documents:
            print("❌ No documents loaded!")
            return
        
        print(f"\n📊 Total documents loaded: {len(all_documents)}")
        
        # Process and insert documents
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_chunks = 0
        
        for doc in tqdm(all_documents, desc="Processing documents"):
            content = doc['content']
            metadata = doc['metadata']
            source = metadata.get('source', 'unknown')
            
            # Chunk document
            chunks = self.chunk_document(content, chunk_size=chunk_size)
            
            for chunk_idx, chunk in enumerate(chunks):
                # Insert document chunk
                cursor.execute("""
                    INSERT INTO docs (source, chunk_text, chunk_index, metadata)
                    VALUES (?, ?, ?, ?)
                """, (source, chunk, chunk_idx, json.dumps(metadata)))
                
                doc_id = cursor.lastrowid
                
                # Create multi-vector embeddings
                embeddings = self.create_multi_vector_embeddings(chunk)
                
                # Insert embeddings
                for emb_type, emb_vector in embeddings.items():
                    cursor.execute("""
                        INSERT INTO embeddings (doc_id, embedding_type, embedding)
                        VALUES (?, ?, ?)
                    """, (doc_id, emb_type, emb_vector.astype(np.float32).tobytes()))
                
                total_chunks += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Database built successfully!")
        print(f"   📄 Documents: {len(all_documents)}")
        print(f"   📝 Chunks: {total_chunks}")
        print(f"   💾 Database: {self.db_path}")


def build_database_from_directory(directory: str, db_path: str = "db/acc.db"):
    """Convenience function to build database from directory"""
    
    builder = EnhancedDatabaseBuilder(db_path)
    builder.build_database([directory])


# Example usage
if __name__ == "__main__":
    # Example 1: Build from single directory
    build_database_from_directory("./documents")
    
    # Example 2: Build from multiple sources
    # builder = EnhancedDatabaseBuilder("db/acc.db")
    # builder.build_database([
    #     "./documents",
    #     "./pdfs/report.pdf",
    #     "./data/info.xlsx"
    # ])