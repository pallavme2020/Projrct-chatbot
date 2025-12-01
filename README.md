# Autoliv AI Knowledge Assistant

A Retrieval-Augmented Generation (RAG) chatbot system that intelligently retrieves and processes information from documents to provide accurate, context-aware responses.

## Purpose

The Autoliv AI Knowledge Assistant enables users to:
- Upload and index multiple document formats (PDF, Word, Excel, Markdown, HTML, CSV, JSON)
- Ask natural language questions about document content
- Receive intelligent, document-backed responses
- Choose between normal and detailed response modes
- Maintain conversation context across sessions

## Prerequisites

- **Python**: Version 3.8 or higher
- **pip**: Python package manager
- **Ollama**: Local LLM backend (optional, for offline inference)
- **4GB+ RAM**: For optimal model performance
- **Storage**: ~2GB for embedding models and databases

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/pallavme2020/Projrct-chatbot.git
cd Projrct-chatbot
```

### Step 2: Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Prepare Your Documents
Place your documents in the `documents/` directory. Supported formats:
- PDF files
- Word documents (.docx)
- Excel spreadsheets (.xlsx)
- Markdown files (.md)
- HTML files
- CSV files
- JSON files
- Plain text files

## How to Run

### Step 1: Build the Database
```bash
python makedatabase.py
```
This processes all documents in the `documents/` folder and creates embeddings for search optimization.

### Step 2: Start the Server
```bash
python server.py
```
The application will start on `http://localhost:8000`

### Step 3: Access the Web Interface
Open your browser and navigate to:
```
http://localhost:8000
```

### Step 4: Ask Questions
- Type your question in the input field
- Select response mode (Normal or Detailed)
- Click "Ask" or press Enter
- View the AI-generated response with source references

## Project Structure

```
├── server.py                    # Web server and UI handler
├── makedatabase.py              # Document processing and indexing
├── chat_v2_cleaneroutput.py    # Core RAG chat engine
├── query_classifier.py          # Query type classification
├── query_processor.py           # Query preprocessing
├── retrieval.py                 # Document retrieval logic
├── context_optimizer.py         # Response context optimization
├── session_manager.py           # Chat session management
├── logger.py                    # Logging utilities
├── requirements.txt             # Python dependencies
├── documents/                   # Input documents directory
├── db/                          # Database storage
└── #Code-Architecture-diagram/  # Architecture documentation
```

## Quick Start Example

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Add your documents to documents/ folder

# 3. Build database
python makedatabase.py

# 4. Start server
python server.py

# 5. Open browser to http://localhost:8000
```

## Troubleshooting

- **Port already in use**: Change port in `server.py` if port 8000 is occupied
- **Module not found**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **Slow response**: First database build may take time for large document sets
- **Memory issues**: Reduce batch size in `makedatabase.py` for large files

## License

This project is part of the Autoliv AI initiative.

---

For more details on architecture, see `#Code-Architecture-diagram/` folder.
