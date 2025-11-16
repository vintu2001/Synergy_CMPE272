# Agentic Apartment Manager

## Group Information
**Group Name: Synergy**

### Team Members
- **Maitreya Patankar**
- **Vineet Malewar**
- **David Wang**
- **Jeremy Tung**

---

## Project Summary
The **Agentic Apartment Manager (AAM)** is an autonomous, AI-driven system that functions as a proactive digital property manager for apartment complexes. It receives resident messages, predicts potential problems, simulates solutions, and autonomously executes actions with explainability and observability built in.

---

## System Architecture
The Agentic Apartment Manager is built as a distributed, event-driven system on AWS Cloud, where containerized FastAPI microservices communicate asynchronously through Kafka or Kinesis to process resident messages and management events in real time. A LangChain-powered LLM interprets natural language inputs, and predictive models using XGBoost and ARIMA assess risk and recurrence probabilities. These outputs feed a reasoning engine built with CrewAI and SimPy, which simulates outcomes and autonomously triggers actions via AWS Lambda APIs. Data is stored in DynamoDB and PostgreSQL, monitored through Instana, CloudWatch, and Grafana. The result is a cohesive, self-learning architecture that continuously perceives, reasons, and acts to manage apartment operations predictively and autonomously.

---

## Features

### 🤖 Agentic Intelligence
- **Multi-Agent System**: Coordinated agents for classification, simulation, and decision-making
- **Autonomous Actions**: Self-directed problem resolution with policy compliance
- **Learning Engine**: Continuous improvement from historical decisions

### 🧠 RAG-Enhanced Decision Making
- **Knowledge Base Integration**: 35+ policy documents, SOPs, vendor catalogs, and SLAs
- **Context-Aware Retrieval**: Building-specific and global document filtering
- **Policy Compliance**: Decisions grounded in actual building policies and regulations
- **Citation Tracking**: Full traceability of knowledge sources used in decisions
- **Vector Search**: ChromaDB-powered semantic search with <100ms latency

### 📊 Predictive Analytics
- **Risk Prediction**: XGBoost-based urgency classification
- **Pattern Detection**: ARIMA forecasting for recurring issues
- **Proactive Maintenance**: Identify problems before they escalate

### 🔍 Decision Logging
- **Audit Trail**: Complete decision history in DynamoDB
- **Rule Transparency**: Structured rule objects with policy citations

---

## Project Structure

```
Synergy_CMPE272/
├── backend/                 # FastAPI microservices
│   ├── app/                 # Application code
│   │   ├── agents/          # Agent implementations
│   │   ├── rag/             # RAG module
│   │   ├── services/        # Service layer
│   │   ├── models/          # Data models and schemas
│   │   └── utils/           # Utility functions
│   ├── kb/                  # Knowledge Base (35+ documents)
│   │   ├── policies/        # Building policies
│   │   ├── sops/            # Standard Operating Procedures
│   │   ├── catalogs/        # Vendor/contact catalogs
│   │   └── slas/            # Service Level Agreements
│   ├── vector_stores/       # Vector database storage
│   │   └── chroma_db/       # ChromaDB persistent storage
│   ├── tests/               # Test suite
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Docker configuration
│
├── frontend/                # Frontend application
│   ├── src/
│   └── package.json
│
├── ml/                      # Machine learning components
│   ├── scripts/             # Python scripts
│   ├── notebooks/           # Jupyter notebooks
│   ├── data/                # Synthetic datasets
│   └── models/              # Trained models
│
└── infrastructure/          # Infrastructure as code
    ├── aws/                 # AWS resources
    └── docker/              # Docker compose
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for frontend)
- AWS Account with appropriate permissions
- Docker (optional, for containerized development)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/vintu2001/Synergy_CMPE272.git
   cd Synergy_CMPE272
   ```

2. **Set up Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and RAG configuration
   ```
   
   **Key RAG Environment Variables:**
   ```bash
   RAG_ENABLED=true
   RAG_TOP_K=5
   RAG_SIMILARITY_THRESHOLD=0.7
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   EMBEDDING_CACHE_ENABLED=true
   VECTOR_STORE_TYPE=chromadb
   VECTOR_STORE_PATH=./vector_stores/chroma_db
   VECTOR_STORE_COLLECTION=apartment_kb
   ```

4. **Download embedding model** (automatic on first run)
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

5. **Initialize vector store**
   ```bash
   python kb/ingest_documents.py
   ```

6. **Validate setup**
   ```bash
   python app/utils/validate_env.py
   ```

7. **Run the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`

### ML Environment Setup

1. **Set up ML environment**
   ```bash
   cd ml
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Generate synthetic data**
   ```bash
   python scripts/synthetic_message_generator.py
   ```

### Frontend Setup
See `frontend/README.md` for details.

### Docker Setup (Optional)

1. **Run with Docker Compose**
   ```bash
   cd infrastructure/docker
   docker-compose up
   ```

---

## API Documentation

Once the backend is running, visit:
- API Docs: `http://localhost:8000/docs` (Swagger UI)
- Alternative Docs: `http://localhost:8000/redoc`

---

## Quick Start: RAG Features

**To use RAG in your queries:**

1. **Enable RAG** (in `.env`):
   ```bash
   RAG_ENABLED=true
   ```

2. **Submit a resident request**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/submit-request \
     -H "Content-Type: application/json" \
     -d '{
       "resident_id": "RES_Building123_1001",
       "message_text": "AC is broken and it'\''s 95°F outside"
     }'
   ```

3. **RAG automatically**:
   - Extracts `building_id` from `resident_id`
   - Retrieves relevant policies, SOPs, and vendor catalogs
   - Injects context into LLM prompts
   - Generates options with policy citations
   - Makes decisions grounded in building rules

4. **View decisions with citations**:
   - Check `source_doc_ids` in `SimulatedOption`
   - Check `rule_sources` and `rule_object` in `DecisionResponse`

**Configuration Tips:**
- Adjust `RAG_TOP_K` (3-7) to control document count
- Tune `RAG_SIMILARITY_THRESHOLD` (0.65-0.75) for precision/recall balance

**Knowledge Base:**
- 35+ documents covering policies, SOPs, catalogs, SLAs
- Located in `backend/kb/`

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
