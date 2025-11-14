# Knowledge Base Ingestion Guide

## Overview

The Synergy knowledge base uses a **LangChain-based ingestion pipeline** that converts structured documents with YAML frontmatter into semantically searchable vector embeddings stored in ChromaDB.

### Key Features

- ✅ **Frontmatter Pre-Processing**: Extracts YAML metadata before chunking
- ✅ **Clean Document Bodies**: Removes YAML blocks, ensuring only content is embedded
- ✅ **Optimized Chunking**: ~700 token target with semantic-aware splitting
- ✅ **Rich Metadata**: Every chunk preserves document metadata (doc_id, type, category, building_id, version)
- ✅ **Idempotent Rebuilds**: Force rebuild clears and recreates vector store
- ✅ **Incremental Updates**: Add new documents without full rebuild
- ✅ **Comprehensive Validation**: Chunk size, metadata coverage, retrieval testing

---

## Architecture

### Pipeline Flow

```
Document Files (Markdown/CSV)
    ↓
Phase 1: Frontmatter Pre-Processing
    ├─ detect_frontmatter()          → Extract YAML between --- delimiters
    ├─ parse_frontmatter_yaml()      → Validate required fields
    ├─ sanitize_metadata()           → Ensure JSON-serializable values
    └─ load_documents_with_metadata() → Create LangChain Documents
    ↓
Phase 2: LangChain Pipeline
    ├─ create_text_splitter()         → RecursiveCharacterTextSplitter
    ├─ split_documents_with_metadata() → Add chunk_id, chunk_index
    ├─ create_embeddings()             → HuggingFaceEmbeddings (all-MiniLM-L6-v2)
    └─ create_vector_store()           → Chroma.from_documents()
    ↓
Phase 3: Validation
    ├─ validate_chunk_sizes()         → Token estimates (word_count * 0.75)
    ├─ validate_metadata_coverage()   → 100% required fields check
    └─ spot_check_retrieval()         → Test known queries
    ↓
Vector Store (ChromaDB)
    └─ ./vector_stores/chroma_db/apartment_kb (97 chunks, ~1.7MB)
```

---

## Installation & Setup

### Prerequisites

```bash
# Required Python packages (already in requirements.txt)
langchain==0.1.20
langchain-community==0.0.38
langchain-text-splitters==0.0.2
langchain-huggingface>=0.1.2
sentence-transformers==2.5.1
chromadb==0.4.24
```

### Environment Variables

No special environment variables required for ingestion. The pipeline uses:

- `kb_dir`: Source directory (default: `kb/`)
- `persist_directory`: Vector store location (default: `./vector_stores/chroma_db`)
- `collection_name`: ChromaDB collection (default: `apartment_kb`)

---

## Usage

### Full Ingestion (Production)

**Rebuild vector store from scratch:**

```bash
cd backend

python -c "
from kb.langchain_ingest import ingest_kb_documents, print_ingestion_summary
import time

start = time.time()
stats = ingest_kb_documents(
    kb_dir='kb',
    persist_directory='./vector_stores/chroma_db',
    collection_name='apartment_kb',
    force_rebuild=True
)
print_ingestion_summary(stats)
print(f'\nTotal time: {time.time()-start:.2f}s')
"
```

**Expected output:**
```
====================================================================
KNOWLEDGE BASE INGESTION PIPELINE
====================================================================

--- PHASE 1: Document Loading ---
Found 47 files in kb (38 MD, 9 CSV)
Loaded 46 documents (1 skipped)

--- PHASE 2: Document Splitting ---
Created 97 chunks from 46 documents

--- PHASE 2: Embedding Generation ---
Embeddings model loaded successfully

--- PHASE 2: Vector Store Creation ---
Force rebuild: Clearing existing vector store
Vector store created with 97 chunks
✓ Vector store persisted to ./vector_stores/chroma_db

====================================================================
INGESTION COMPLETE
====================================================================

Documents Loaded:  46
Chunks Created:    97
Duration:          8.18 seconds

Document Types:
  catalog     :    7 chunks (  7.2%)
  cost        :   22 chunks ( 22.7%)
  policy      :   20 chunks ( 20.6%)
  scoring     :   29 chunks ( 29.9%)
  sla         :    7 chunks (  7.2%)
  sop         :   12 chunks ( 12.4%)

✅ No errors during ingestion
```

### Incremental Updates

**Add new documents without rebuilding:**

```bash
python -c "
from kb.langchain_ingest import ingest_kb_documents, print_ingestion_summary

stats = ingest_kb_documents(
    kb_dir='kb',
    persist_directory='./vector_stores/chroma_db',
    collection_name='apartment_kb',
    force_rebuild=False
)
print_ingestion_summary(stats)
"
```

> **Note**: Incremental updates add new documents but do not remove deleted documents. Use `force_rebuild=True` to fully synchronize.

### Test Ingestion (Development)

**Use test vector store for development:**

```bash
python -c "
from kb.langchain_ingest import ingest_kb_documents, print_ingestion_summary

stats = ingest_kb_documents(
    kb_dir='kb',
    persist_directory='./test_vector_stores/chroma_db',
    collection_name='test_apartment_kb',
    force_rebuild=True
)
print_ingestion_summary(stats)
"
```

---

## Testing & Validation

### Phase 1: Frontmatter Extraction

**Test YAML frontmatter detection and parsing:**

```bash
python kb/test_phase1_frontmatter.py --kb-dir kb
```

**Validates:**
- ✅ YAML frontmatter detection (Markdown `---` delimiters, CSV headers)
- ✅ Required fields present (doc_id, type, category, building_id, version)
- ✅ Metadata sanitization (lists→strings, dates→ISO format)
- ✅ Clean document bodies (no YAML in `page_content`)

**Expected results:**
- 46 documents loaded
- 100% metadata coverage
- No YAML in document bodies
- All 6 document types present

---

### Phase 2: Ingestion Pipeline

**Test full LangChain ingestion:**

```bash
python kb/test_phase2_ingestion.py --kb-dir kb --persist-dir ./test_vector_stores/chroma_db
```

**Validates:**
- ✅ Text splitting with RecursiveCharacterTextSplitter
- ✅ Embedding generation with HuggingFaceEmbeddings
- ✅ ChromaDB vector store creation
- ✅ Persistence to disk
- ✅ Chunk metadata preservation

**Expected results:**
- 97 chunks created from 46 documents
- ~1.7MB vector store
- ~26 seconds duration
- All document types distributed correctly

---

### Phase 3: Validation

**Test all validations:**

```bash
python kb/test_phase3_validation.py --kb-dir kb --persist-dir ./vector_stores/chroma_db --collection-name apartment_kb
```

**Test specific validation:**

```bash
# Chunk size validation only
python kb/test_phase3_validation.py --test chunk-size --kb-dir kb

# Metadata coverage only
python kb/test_phase3_validation.py --test metadata --kb-dir kb

# Retrieval testing only (requires existing vector store)
python kb/test_phase3_validation.py --test retrieval --persist-dir ./vector_stores/chroma_db --collection-name apartment_kb
```

**Validates:**
- ✅ **Chunk Sizes**: Token estimates (word_count × 0.75), checks 500-800 token target
- ✅ **Metadata Coverage**: 100% required fields in all chunks
- ✅ **Spot-Check Retrieval**: Tests 3 known queries with expected results

**Test queries:**
1. "after-hours AC leak cost" → Expected: COST_005 (type=cost)
2. "emergency decision weights" → Expected: SCORING_001 (type=scoring)
3. "gas smell escalation" → Expected: SCORING_003 (type=scoring)

**Expected results:**
- Average chunk size: ~196 tokens (acceptable for concise KB documents)
- Metadata coverage: 100%
- Retrieval accuracy: 3/3 queries passed

---

## Configuration

### Text Chunking

**Default settings:**
- **chunk_size**: 2800 characters (~700 tokens)
- **chunk_overlap**: 480 characters (~120 tokens)
- **Splitter**: RecursiveCharacterTextSplitter (semantic-aware)

**Rationale:**
- 700 tokens balances context vs. specificity
- 120 token overlap prevents semantic boundary cuts
- Recursive splitting respects Markdown structure (headers, paragraphs, sentences)

**Customization:**

```python
from kb.langchain_ingest import create_text_splitter

text_splitter = create_text_splitter(
    chunk_size=3200,    # ~800 tokens
    chunk_overlap=400   # ~100 tokens
)
```

### Embeddings

**Model**: `sentence-transformers/all-MiniLM-L6-v2`

**Specifications:**
- Dimensions: 384
- Max tokens: 256 (sequences truncated)
- Performance: Fast inference (~0.1s per chunk)
- Quality: Optimized for semantic similarity

**Customization:**

```python
from kb.langchain_ingest import create_embeddings

embeddings = create_embeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"  # Higher quality, slower
)
```

### Vector Store

**Database**: ChromaDB with persistence

**Settings:**
- **persist_directory**: `./vector_stores/chroma_db`
- **collection_name**: `apartment_kb`
- **distance_metric**: Cosine similarity (L2 normalized)

**Customization:**

```python
from kb.langchain_ingest import create_vector_store

vectorstore = create_vector_store(
    chunked_docs=chunked_docs,
    embeddings=embeddings,
    persist_directory="./custom_path",
    collection_name="custom_collection"
)
```

---

## Troubleshooting

### Issue: "Skipping file without frontmatter"

**Cause**: Document missing YAML frontmatter block

**Solution**: Add frontmatter to document:

```markdown
---
doc_id: "POLICY_001"
type: "policy"
category: "noise_complaint"
building_id: "all_buildings"
effective_date: "2024-01-01"
last_updated: "2025-11-13"
version: "1.0"
---

# Document content here
```

---

### Issue: "Missing required metadata fields"

**Cause**: Frontmatter missing required fields

**Required fields:**
- `doc_id`: Unique identifier (format: TYPE_NNN)
- `type`: Document type (policy, sop, catalog, sla, cost, scoring)
- `category`: Primary category
- `building_id`: Building identifier (or "all_buildings")
- `version`: Version number

**Solution**: Add all required fields to frontmatter

---

### Issue: Average chunk size below 500 tokens

**Cause**: Documents are concise (cost/scoring rules)

**Impact**: ⚠️ Acceptable if retrieval accuracy is maintained

**Validation**: Run spot-check queries to verify retrieval works correctly

**Solution** (if retrieval suffers):
- Combine related documents
- Adjust `chunk_size` to create larger chunks
- Review document structure (very short sections may not contain enough context)

---

### Issue: ChromaDB persistence warning

**Message**: "Since Chroma 0.4.x the manual persistence method is no longer supported"

**Cause**: ChromaDB auto-persists, `.persist()` is deprecated

**Impact**: ℹ️ Informational only - data is already persisted

**Solution**: No action needed - warning is expected

---

### Issue: Vector store has 0 chunks after ingestion

**Cause**: Collection name mismatch

**Diagnosis**:

```python
import chromadb

client = chromadb.PersistentClient(path='./vector_stores/chroma_db')
collections = client.list_collections()
for c in collections:
    print(f"{c.name}: {c.count()} chunks")
```

**Solution**: Use correct collection name when loading vector store

---

### Issue: Retrieval returns wrong documents

**Diagnosis**: Run validation tests

```bash
python kb/test_phase3_validation.py --test retrieval --persist-dir ./vector_stores/chroma_db --collection-name apartment_kb
```

**Common causes:**
- **Insufficient context in queries**: Add more specific terms
- **Metadata filtering needed**: Use metadata filters in retrieval
- **Chunk size too small**: Documents split mid-context
- **Stale vector store**: Rebuild with `force_rebuild=True`

**Solution**: Adjust query or rebuild vector store

---

## Performance Metrics

### Baseline Performance (46 documents, 97 chunks)

| Metric | Value |
|--------|-------|
| **Documents** | 46 |
| **Chunks** | 97 |
| **Average Chunk Size** | 196 tokens (~1992 chars) |
| **Vector Store Size** | 1.7MB |
| **Ingestion Time** | ~8 seconds |
| **Embedding Time** | ~6 seconds |
| **Metadata Coverage** | 100% |
| **Retrieval Accuracy** | 3/3 (100%) |

### Scaling Estimates

| Documents | Est. Chunks | Est. Size | Est. Time |
|-----------|-------------|-----------|-----------|
| 100 | ~210 | ~3.6MB | ~17s |
| 500 | ~1050 | ~18MB | ~85s |
| 1000 | ~2100 | ~36MB | ~170s |

> **Note**: Times include embedding generation (~0.06s per chunk average)

---

## Best Practices

### Document Preparation

1. **Use YAML frontmatter**: Required for metadata extraction
2. **Validate required fields**: Ensure all documents have doc_id, type, category, building_id, version
3. **Use semantic structure**: Leverage Markdown headers for better chunking
4. **Keep sections focused**: One concept per section for optimal retrieval
5. **Avoid very short documents**: Minimum ~100 words for meaningful chunks

### Ingestion Workflow

1. **Development**:
   - Test with `test_vector_stores/chroma_db`
   - Use `collection_name="test_apartment_kb"`
   - Run validation tests

2. **Production**:
   - Use `force_rebuild=True` for first ingestion
   - Use `force_rebuild=False` for incremental updates
   - Run spot-check validation after ingestion
   - Monitor chunk count and distribution

3. **Maintenance**:
   - Rebuild weekly or after major KB updates
   - Archive old vector stores before rebuilding
   - Track ingestion metrics over time

### Quality Assurance

✅ **Before committing documents:**
- YAML frontmatter present and valid
- Required fields populated
- Document content follows KB guidelines

✅ **After ingestion:**
- Run Phase 3 validation tests
- Verify chunk count matches expectations
- Test retrieval with known queries
- Check metadata coverage is 100%

✅ **Production checklist:**
- Vector store location: `./vector_stores/chroma_db`
- Collection name: `apartment_kb`
- Validation tests passed
- Spot-check queries return correct results

---

## API Reference

### Main Functions

#### `ingest_kb_documents()`

```python
def ingest_kb_documents(
    kb_dir: str = "kb",
    persist_directory: str = "./vector_stores/chroma_db",
    collection_name: str = "apartment_kb",
    force_rebuild: bool = False
) -> dict:
    """
    Main ingestion pipeline orchestrator.
    
    Args:
        kb_dir: Source directory containing KB documents
        persist_directory: ChromaDB storage path
        collection_name: ChromaDB collection name
        force_rebuild: If True, clears and rebuilds vector store
        
    Returns:
        dict: Ingestion statistics (docs_loaded, chunks_created, duration, errors)
    """
```

#### `load_documents_with_metadata()`

```python
def load_documents_with_metadata(
    kb_dir: str
) -> List[Document]:
    """
    Load documents from directory with frontmatter extraction.
    
    Args:
        kb_dir: Directory to scan for documents
        
    Returns:
        List[Document]: LangChain Documents with clean bodies and metadata
    """
```

#### `split_documents_with_metadata()`

```python
def split_documents_with_metadata(
    documents: List[Document],
    text_splitter: RecursiveCharacterTextSplitter
) -> List[Document]:
    """
    Split documents into chunks with metadata preservation.
    
    Args:
        documents: List of LangChain Documents
        text_splitter: Configured text splitter
        
    Returns:
        List[Document]: Chunked documents with chunk_id, chunk_index, total_chunks
    """
```

#### `run_full_validation()`

```python
def run_full_validation(
    kb_dir: str,
    persist_directory: str,
    collection_name: str = "apartment_kb"
) -> dict:
    """
    Run all validation checks on ingested vector store.
    
    Args:
        kb_dir: Source directory for documents
        persist_directory: Vector store location
        collection_name: ChromaDB collection name
        
    Returns:
        dict: Validation results (chunk_size, metadata, retrieval, overall_passed)
    """
```

---

## Migration from Custom Ingestion

### Old Approach (Deprecated)

```bash
# ❌ Old custom ingestion (removed)
python kb/ingest_documents.py --full-rebuild
```

### New Approach (LangChain)

```bash
# ✅ New LangChain ingestion
python -c "from kb.langchain_ingest import ingest_kb_documents; ingest_kb_documents('kb', './vector_stores/chroma_db', 'apartment_kb', force_rebuild=True)"
```

### Key Differences

| Feature | Old (Custom) | New (LangChain) |
|---------|--------------|-----------------|
| **Framework** | Custom implementation | LangChain-based |
| **Frontmatter** | Embedded in chunks | Pre-extracted |
| **Document Bodies** | Contains YAML | Clean, YAML-free |
| **Chunking** | Basic character split | RecursiveCharacterTextSplitter |
| **Metadata** | Limited fields | Rich metadata + chunk info |
| **Validation** | Manual | Automated tests |
| **Test Suite** | None | 3-phase comprehensive |

### Migration Steps

1. ✅ Install LangChain dependencies (already in requirements.txt)
2. ✅ Backup old vector store (if needed)
3. ✅ Run new ingestion with `force_rebuild=True`
4. ✅ Validate with Phase 3 tests
5. ✅ Update retrieval code to use new collection name
6. ✅ Remove old `ingest_documents.py` (already done)

---

## Support

For questions or issues:

1. Check this guide for common solutions
2. Run validation tests to diagnose issues
3. Review ingestion logs for error messages
4. Consult `kb/README.md` for document standards

---

## Changelog

### v2.0.0 - LangChain Migration (2025-11-13)

**Added:**
- LangChain-based ingestion pipeline
- Frontmatter pre-processing phase
- Comprehensive 3-phase test suite
- Validation functions (chunk size, metadata, retrieval)
- Ingestion statistics and summaries

**Changed:**
- Chunking: Custom → RecursiveCharacterTextSplitter
- Target chunk size: 512 chars → 2800 chars (~700 tokens)
- Document bodies: YAML-included → YAML-free
- Metadata: Basic → Rich (chunk_id, indices, etc.)

**Removed:**
- Custom `ingest_documents.py` (601 lines)
- Manual validation steps

**Improved:**
- 100% metadata coverage guarantee
- Idempotent force_rebuild
- Automated retrieval testing
- Better error handling and logging

---

## License

[Add your license information here]
