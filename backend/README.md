# Synergy Backend - LangChain RAG Implementation

## Overview
Backend service for the Synergy apartment management system with AI-powered request processing using LangChain RAG (Retrieval-Augmented Generation).

## Prerequisites
- Python 3.10 or 3.11
- Virtual environment (recommended)
- Google Gemini API key
- AWS credentials (for DynamoDB)

## Quick Start

### 1. Setup Virtual Environment
```bash
cd /path/to/Synergy_CMPE272
python3.10 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
cd backend
make install
# OR manually:
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# AWS
AWS_REGION=us-west-2
AWS_DYNAMODB_TABLE_NAME=aam_requests

# Optional (defaults provided)
PERSIST_DIR=./vector_stores/chroma_db
COLLECTION_NAME=apartment_kb
GEMINI_MODEL=gemini-2.5-pro
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### 4. Verify Installation

```bash
# Check environment variables
make check-env

# Test connectivity (Gemini API, ChromaDB, LangChain)
make check-connectivity

# Or run verification script directly
python scripts/verify_setup.py
```

Expected output:
```
✓ Gemini API connectivity: SUCCESS
✓ ChromaDB: WORKING
✓ LangChain imports successful
✓ Embedding model: WORKING
🎉 All checks passed!
```

### 5. Run Backend Server

```bash
make run
# OR
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | - | Google Gemini API key (LangChain) |
| `GEMINI_API_KEY` | ✅ Yes | - | Backward compatibility alias |
| `AWS_REGION` | ✅ Yes | - | AWS region for DynamoDB |
| `AWS_DYNAMODB_TABLE_NAME` | ✅ Yes | - | DynamoDB table name |
| `PERSIST_DIR` | ❌ No | `./vector_stores/chroma_db` | ChromaDB storage path |
| `COLLECTION_NAME` | ❌ No | `apartment_kb` | Vector store collection |
| `GEMINI_MODEL` | ❌ No | `gemini-2.5-pro` | Gemini model (pro/flash/latest) |
| `EMBEDDING_MODEL` | ❌ No | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | ❌ No | `512` | Text chunk size |
| `CHUNK_OVERLAP` | ❌ No | `50` | Chunk overlap |
| `RETRIEVAL_TOP_K` | ❌ No | `5` | Number of docs to retrieve |
| `SIMILARITY_THRESHOLD` | ❌ No | `0.7` | Minimum similarity score |

## LangChain Stack (Pinned Versions)

### Core Dependencies
- `langchain==0.1.20` - LangChain framework
- `langchain-core==0.1.52` - Core abstractions
- `langchain-community==0.0.38` - Community integrations
- `langchain-text-splitters==0.0.2` - Text chunking
- `langchain-google-genai==0.0.11` - Google Gemini integration

### Supporting Libraries
- `chromadb==0.4.24` - Vector database
- `sentence-transformers==2.5.1` - Embeddings
- `pydantic==2.10.1` - Data validation

## Available Commands

```bash
# Development
make help                  # Show all available commands
make install              # Install all dependencies
make run                  # Start backend server
make test                 # Run tests

# Verification
make check-env            # Verify environment variables
make check-connectivity   # Test API and package connectivity

# Maintenance
make clean                # Remove cache and build artifacts
```

## Architecture

### RAG Components
1. **Embeddings**: HuggingFaceEmbeddings with all-MiniLM-L6-v2 (384-dim)
2. **Vector Store**: ChromaDB (persisted on disk at `./vector_stores/chroma_db`)
3. **LLM**: ChatGoogleGenerativeAI (Gemini 1.5 Flash/Pro)
4. **Chunking**: RecursiveCharacterTextSplitter (~700 tokens target, 2800 chars with 480 overlap)
5. **Output Parsing**: Pydantic models with structured output

### Knowledge Base Ingestion

**LangChain-based pipeline** with three phases:

1. **Frontmatter Pre-Processing**: Extracts YAML metadata from Markdown/CSV, validates required fields, creates Documents with clean bodies
2. **LangChain Pipeline**: Splits text, generates embeddings, stores in ChromaDB with metadata
3. **Validation**: Verifies chunk sizes, metadata coverage, retrieval accuracy

**Quick ingestion:**
```bash
# Full rebuild
python -c "from kb.langchain_ingest import ingest_kb_documents; ingest_kb_documents('kb', './vector_stores/chroma_db', 'apartment_kb', force_rebuild=True)"

# Incremental update
python -c "from kb.langchain_ingest import ingest_kb_documents; ingest_kb_documents('kb', './vector_stores/chroma_db', 'apartment_kb', force_rebuild=False)"
```

**Test ingestion:**
```bash
python kb/test_phase3_validation.py --persist-dir ./vector_stores/chroma_db --collection-name apartment_kb
```

See `kb/README.md` for detailed ingestion documentation.

### Agent Pipeline
```
User Request → Classification → Risk Assessment → 
Simulation (RAG) → Decision → Execution
```

## Troubleshooting

### "GOOGLE_API_KEY not set"
- Check `.env` file exists in backend directory
- Verify API key is valid at https://makersuite.google.com/app/apikey
- Ensure you're using the `.env` file, not `.env.example`

### "Module 'langchain_google_genai' not found"
- Run: `pip install langchain-google-genai==0.0.11`
- Or: `make install`

### "ChromaDB import failed"
- Reinstall: `pip install --upgrade chromadb==0.4.24`
- Check Python version >= 3.10

### "Gemini API connectivity failed" (429 Error)
- Check API quota at https://ai.dev/usage
- Verify API key has Gemini API enabled
- Consider upgrading to paid tier for higher limits

### "ResourceExhausted" errors
- Your API key has exceeded free tier quota
- Wait for quota reset or upgrade plan
- Check usage at https://ai.dev/usage?tab=rate-limit

## Testing

```bash
# Run all tests
make test

# Run specific test files
pytest tests/unit/test_vector_store.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Development

### Project Structure
```
backend/
├── app/
│   ├── agents/          # AI agents (classification, simulation, decision)
│   ├── models/          # Pydantic schemas
│   ├── rag/             # RAG implementation
│   ├── services/        # Business logic
│   └── utils/           # Utilities and helpers
├── kb/                  # Knowledge base documents
├── scripts/             # Utility scripts
├── tests/               # Test suite
├── vector_stores/       # ChromaDB persistence
├── Makefile             # Build automation
└── requirements.txt     # Python dependencies
```

### Adding New Dependencies
1. Add to `requirements.txt` with pinned version
2. Add to `requirements-railway.txt` (deployment)
3. Run `make install`
4. Update this README if it's a core dependency

## API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Support

For issues or questions:
1. Check this README
2. Review `.env.example` for configuration
3. Run `python scripts/verify_setup.py` for diagnostics
4. Check application logs for errors

## License

[Add your license information here]
