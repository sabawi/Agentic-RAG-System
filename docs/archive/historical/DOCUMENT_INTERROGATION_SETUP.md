# Document Interrogation System Setup

## Overview
The Document Interrogation System adds **Stage 0 RAG Retrieval** to your existing 2-stage LLM architecture, enabling natural language queries over local document collections.

## Architecture Integration
```
📁 User Question → Stage 0 (RAG) → Stage 1 (Tools) → Stage 2 (LLM) → Answer
                     ↑
                 FAISS Search + Document Context
```

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements_document_interrogation.txt
```

### 2. Verify Installation
```bash
# Check if server starts without errors
./start_complete.sh

# Check document system status
curl -X GET http://localhost:5000/documents/stats
```

## Usage

### 1. Index Documents
```bash
# Index a directory of documents
curl -X POST http://localhost:5000/documents/index-directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "/path/to/documents", "recursive": true}'
```

### 2. Search Documents
```bash
# Search for specific information
curl -X POST http://localhost:5000/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "quarterly results", "k": 5}'
```

### 3. Interrogate Documents (Full Pipeline)
```bash
# Ask natural language questions
curl -X POST http://localhost:5000/documents/interrogate \
  -H "Content-Type: application/json" \
  -d '{"question": "What were the main findings in the research documents?", "model": "qwen3:8b"}'
```

### 4. Directory Watching (Auto-indexing)
```bash
# Start watching for new documents
curl -X POST http://localhost:5000/documents/watch-directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "/path/to/documents"}'
```

## Supported File Types
- **Text**: `.txt`, `.md`
- **Web**: `.html`
- **Documents**: `.pdf`, `.docx`
- **Spreadsheets**: `.xlsx`
- **Images**: `.jpg`, `.png`, `.bmp`, `.tiff` (with OCR)

## API Endpoints

| Endpoint | Method | Purpose |
|----------|---------|----------|
| `/documents/index-directory` | POST | Index all documents in a directory |
| `/documents/search` | POST | Search for relevant document chunks |
| `/documents/interrogate` | POST | Ask questions using full 2-stage LLM |
| `/documents/watch-directory` | POST | Start auto-indexing new documents |
| `/documents/stop-watching` | POST | Stop directory watching |
| `/documents/stats` | GET | Get system statistics |

## Tool Integration

The system also provides a `document_search` tool for the existing tool system:

```json
{
  "name": "document_search",
  "description": "Search through indexed documents to find relevant information",
  "parameters": {
    "query": "search terms or question",
    "max_results": 5
  }
}
```

## Storage

- **FAISS Index**: `document_store/faiss.index` (vector similarities)
- **Metadata**: `document_store/metadata.db` (SQLite with document info)
- **Automatic**: Creates storage directory on first use

## Performance Tips

1. **Batch Processing**: Index directories rather than individual files
2. **Chunk Size**: Default 1000 chars with 200 overlap works well
3. **Search Results**: Start with k=5, increase if needed
4. **Memory**: FAISS loads entire index in memory

## Troubleshooting

### Dependencies Missing
```bash
# Install missing packages
pip install faiss-cpu numpy PyPDF2 python-docx openpyxl beautifulsoup4 pytesseract pillow watchdog
```

### OCR Issues (Images)
```bash
# Install Tesseract OCR system dependency
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract
```

### FAISS Errors
- Use `faiss-cpu` for CPU-only systems
- Use `faiss-gpu` only if you have CUDA setup

### Memory Issues
- Reduce chunk size in `DocumentProcessor.__init__`
- Process smaller batches of documents
- Use FAISS IVF indexes for large collections

## Integration with Existing Tools

The document search seamlessly integrates with your existing tools. For example:

1. **Web Search + Documents**: Search web for current info, documents for historical context
2. **Stock Data + Documents**: Combine live market data with stored financial reports  
3. **Email + Documents**: Reference documents when sending contextual emails

The 2-stage LLM architecture automatically handles combining these different data sources.