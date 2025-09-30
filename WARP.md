# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

QAChatAgent is an AI-powered Q&A system with PDF document processing and knowledge base management. It consists of a FastAPI backend and Vue 3 frontend, supporting multi-session management and context-aware intelligent Q&A.

## Quick Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies with conda (recommended)
conda env create -f environment.yml
conda activate multimodal-rag-pdf

# Or use pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Start development server
python main.py
# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start with shell script
./start.sh
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Running Full Stack
1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Access application at `http://localhost:5173` (frontend) with API at `http://localhost:8000`

## Core Architecture

### Backend Architecture
- **Main Entry**: `backend/main.py` - FastAPI application with CORS middleware
- **Database Layer**: 
  - `utils/database_chat.py` - Chat session and message management
  - `utils/database_knowledge.py` - Knowledge base CRUD operations
- **Document Processing**: 
  - `utils/pdf_to_markdown.py` - PDF parsing with OCR (PaddleOCR/Tesseract)
  - `utils/document_loader.py` - Multi-format document loading
- **Vector Search**: 
  - `utils/chroma_store.py` - ChromaDB vector storage and retrieval
  - `utils/embeding.py` - Text embedding generation
- **AI Chat**: 
  - `utils/rag_chat.py` - RAG-enhanced chat with context awareness
  - Uses ChatZhipuAI (GLM-4) with streaming responses

### Frontend Architecture
- **Main Entry**: `frontend/src/main.js` - Vue 3 app with Element Plus
- **State Management**: 
  - `stores/chat.js` - Chat sessions, messages, SSE handling
  - `stores/knowledge.js` - Knowledge base management
- **Views**: 
  - `views/chat/ChatView.vue` - Main chat interface with session management
  - `views/knowledge/KnowledgeView.vue` - Knowledge base management UI
- **Components**: 
  - `components/KnowledgeManagement.vue` - Knowledge base operations
  - `components/FilePreview.vue` - File preview functionality

## Key System Integration Points

### RAG Pipeline Flow
1. **Document Upload** → PDF processing (OCR) → Text extraction → Vector embedding → ChromaDB storage
2. **Query Processing** → Context-aware question reconstruction → Vector similarity search → LLM generation with retrieved context
3. **Streaming Response** → SSE connection → JSON-formatted chunks → Frontend markdown rendering

### Session Management
- **Session Creation**: Time-based ID generation in frontend store
- **Message Storage**: SQLite database with session history tracking
- **Context Awareness**: Historical messages used for query reconstruction and context enhancement

### File Processing Architecture
- **Upload Handler**: `POST /api/upload` with background task processing
- **PDF Processing**: PyMuPDF + PaddleOCR for text/table/image extraction
- **Knowledge Integration**: Automatic vectorization and ChromaDB storage

## Environment Setup Requirements

### System Dependencies
```bash
# Windows (using conda/pip)
# Install Poppler for PDF rendering
# Install Tesseract for OCR
# Set environment variables: POPPLER_PATH, TESSERACT_CMD
```

### Backend Environment Variables (.env)
```
DATABASE_URL=sqlite:///./chat.db
ZHIPUAI_API_KEY=your_zhipuai_api_key
POPPLER_PATH=/path/to/poppler/bin
LLM_MODEL_NAME=glm-4
EMBEDDING_MODEL_NAME=embedding-2
```

### Frontend Environment Variables (.env)
```
VITE_API_BASE_URL=http://localhost:8000
```

## Key API Endpoints

### Chat Operations
- `GET /api/chat/stream` - SSE streaming chat with knowledge base integration
- `PUT /api/session/update/{session_id}` - Update session metadata

### Document Management
- `POST /api/upload` - File upload with optional knowledge base association
- `DELETE /api/delete/{kb_id}/{doc_id}` - Delete knowledge base documents
- `GET /api/task/status/{task_id}` - Check background task status

### Knowledge Base Management
- `POST /api/knowledge_base/create` - Create new knowledge base
- `DELETE /api/knowledge_base/delete/{kb_id}` - Delete knowledge base

## Common Development Patterns

### Adding New Document Processing
1. Extend `document_loader.py` with new format handlers
2. Update `chroma_store.py` for vectorization logic
3. Modify upload endpoint in `main.py` for processing pipeline

### Extending Chat Functionality
1. Modify `rag_chat.py` for new AI model integration
2. Update streaming response format in main chat endpoint
3. Adjust frontend SSE handling in `stores/chat.js`

### Database Schema Changes
1. Update models in `database_chat.py` or `database_knowledge.py`
2. Handle migration logic for existing data
3. Update API endpoints and frontend stores accordingly

## Performance Considerations

- **Vector Search**: ChromaDB similarity threshold set to 0.5 with k=10 results
- **Streaming**: Configurable delay (STREAM_DELAY=0.01) for response pacing
- **Background Processing**: PDF processing runs in separate threads
- **Memory Management**: Document chunking for large files, session history limiting

## Testing Approach

### Backend Testing
```bash
cd backend
# Test API endpoints
python -m pytest tests/ -v
# Manual API testing
curl http://localhost:8000/docs
```

### Frontend Testing
```bash
cd frontend
# Component testing (if tests exist)
npm run test
# E2E testing
npm run test:e2e
```

## Troubleshooting Common Issues

### PDF Processing Fails
- Check Poppler installation and PATH configuration
- Verify Tesseract OCR engine availability
- Review log output in backend console

### SSE Connection Issues
- Monitor browser Network tab for connection status
- Check CORS configuration in FastAPI middleware
- Verify frontend event source handling logic

### Vector Search Not Working
- Ensure ChromaDB persistence directory permissions
- Check embedding model availability and API keys
- Review document vectorization logs