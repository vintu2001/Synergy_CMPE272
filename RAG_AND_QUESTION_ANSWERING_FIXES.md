# RAG and Question Answering Fixes ✅

## Issues Fixed

### 1. **RAG Not Finding Documents**
**Problem:** System showing "No policy documentation found" even when documents exist.

**Root Causes:**
- Similarity threshold was too high (0.7) - filtering out valid documents
- Documents may not be ingested into ChromaDB

**Fixes Applied:**
1. ✅ Lowered similarity threshold from `0.7` to `0.5` in `docker-compose.microservices.yml`
2. ✅ Updated simulation agent to explicitly pass `similarity_threshold=0.5` when retrieving documents
3. ✅ Improved logging to show document count and retrieval results

**Files Changed:**
- `infrastructure/docker/docker-compose.microservices.yml` - Changed `RAG_SIMILARITY_THRESHOLD=0.5`
- `services/decision-simulation/app/agents/simulation_agent.py` - Added explicit `similarity_threshold=0.5` parameter

**Next Steps:**
- Ensure documents are ingested: Run `python services/decision-simulation/app/kb/ingest_documents.py` if ChromaDB is empty
- Check ChromaDB collection count in logs: Look for "Connected to collection 'apartment_kb' with X documents"

### 2. **ANSWER_QUESTION Intent Not Handled**
**Problem:** When intent is `answer_a_question`, system still shows 3-4 options instead of direct answer.

**Fixes Applied:**
1. ✅ Added `ANSWER_QUESTION` intent check in orchestrator (`services/request-management/app/services/orchestrator.py`)
   - When intent is `ANSWER_QUESTION`, calls `/api/v1/answer-question` endpoint
   - Returns direct answer instead of generating options
   - Creates request record with status `RESOLVED`

2. ✅ Added `/api/v1/answer-question` endpoint in Decision & Simulation Service
   - Uses existing `answer_question()` function from RAG retriever
   - Returns answer with source documents and confidence

3. ✅ Frontend already handles "answered" status (line 176 in `ResidentSubmission.jsx`)
   - Fixed source_docs mapping to handle both `source_docs` and `sources` fields

**Files Changed:**
- `services/request-management/app/services/orchestrator.py` - Added ANSWER_QUESTION handling
- `services/decision-simulation/app/api/routes.py` - Added `/answer-question` endpoint
- `frontend/src/pages/ResidentSubmission.jsx` - Fixed source_docs mapping

## Testing

### Test RAG Document Retrieval:
```bash
# Check if documents are loaded
docker-compose -f docker-compose.microservices.yml logs decision-simulation | grep "documents"

# Should see: "Connected to collection 'apartment_kb' with X documents"
```

### Test Question Answering:
1. Submit a question (e.g., "What is the pet policy?")
2. System should classify as `intent: answer_a_question`
3. Should return direct answer instead of options
4. Frontend should display answer in green card format

### Test Document Retrieval:
1. Submit a maintenance request
2. Check logs for: "RAG retrieval successful: X documents retrieved"
3. Options should include source document IDs if RAG found documents

## Notes

- **Similarity Threshold**: Lowered to 0.5 for better recall. Can be adjusted via `RAG_SIMILARITY_THRESHOLD` env var.
- **Document Ingestion**: If ChromaDB is empty, run the ingestion script to load KB documents.
- **Question Flow**: Questions are immediately resolved (status=RESOLVED) and don't go through option selection.

