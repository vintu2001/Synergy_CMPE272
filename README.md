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
The **Agentic Apartment Manager (AAM)** is an autonomous, AI-driven system that functions as a proactive digital property manager for apartment complexes.  
It receives resident messages, predicts potential problems, simulates solutions, and autonomously executes actions — with explainability and observability built in.

Traditional property management tools are reactive and rely on manual intervention.  
AAM instead operates *agentically* — it understands, forecasts, acts, and explains.

---


## Agentic Enterprise Stack Alignment

| **Layer** | **Implementation in AAM** | **Functionality** |
|------------|----------------------------|--------------------|
| **Governance Layer** | IBM **Watsonx.governance** | Ensures transparency, ethical compliance, and decision accountability through explainable AI logs. |
| **Agent Layer** | Decision Orchestrator built using **LangChain / CrewAI** | Coordinates sub-agents (classification, prediction, simulation, execution) to perform reasoning, policy enforcement, and decision-making autonomously. |
| **AI Layer** | Predictive models (XGBoost, ARIMA) + LLMs | Handles message classification, pattern detection, and forecasting of recurring issues or failures. |
| **Service Layer** | **FastAPI microservices**, AWS Lambda, Kafka/Kinesis | Manages asynchronous communication, event processing, and API interactions with simulated maintenance, billing, and delivery systems. |
| **Foundation Layer** | **AWS Cloud**, Docker, DynamoDB | Provides scalable infrastructure for running distributed agents and storing message/event history. |

This layered design follows the *Agentic Enterprise Stack* model where governance ensures ethics, the agent layer handles autonomy, and the AI, service, and foundation layers provide the intelligence, connectivity, and infrastructure that make autonomous operation possible.

---

## System Architecture
The Agentic Apartment Manager is built as a distributed, event-driven system on AWS Cloud, where containerized FastAPI microservices communicate asynchronously through Kafka or Kinesis to process resident messages and management events in real time. A LangChain-powered LLM interprets natural language inputs, and predictive models using XGBoost and ARIMA assess risk and recurrence probabilities. These outputs feed a reasoning engine built with CrewAI and SimPy, which simulates outcomes and autonomously triggers actions via AWS Lambda APIs. Data is stored in DynamoDB and PostgreSQL, monitored through Instana, CloudWatch, and Grafana, while IBM Watsonx.governance ensures explainability and auditability. The result is a cohesive, self-learning architecture that continuously perceives, reasons, and acts to manage apartment operations predictively and autonomously.

---

## Features

### 🤖 Agentic Intelligence
- **Multi-Agent System**: Coordinated agents for classification, simulation, and decision-making
- **Autonomous Actions**: Self-directed problem resolution with policy compliance
- **Learning Engine**: Continuous improvement from historical decisions

### 🧠 RAG-Enhanced Decision Making (Phase 1 Complete)
- **Knowledge Base Integration**: 35+ policy documents, SOPs, vendor catalogs, and SLAs
- **Context-Aware Retrieval**: Building-specific and global document filtering
- **Policy Compliance**: Decisions grounded in actual building policies and regulations
- **Citation Tracking**: Full traceability of knowledge sources used in decisions
- **Vector Search**: ChromaDB-powered semantic search with <100ms latency

### 📊 Predictive Analytics
- **Risk Prediction**: XGBoost-based urgency classification
- **Pattern Detection**: ARIMA forecasting for recurring issues
- **Proactive Maintenance**: Identify problems before they escalate

### 🔍 Governance & Explainability
- **Decision Logging**: Complete audit trail in DynamoDB
- **Rule Transparency**: Structured rule objects with policy citations
- **Compliance Tracking**: IBM Watsonx.governance integration

---

## Project Structure

```
Synergy_CMPE272/
├── backend/                 # FastAPI microservices
│   ├── app/                 # Application code
│   │   ├── agents/          # Agent implementations (classification, simulation, decision)
│   │   ├── rag/             # RAG module (retrieval, context injection) - Phase 1
│   │   ├── services/        # Service layer (APIs, database, message intake)
│   │   ├── models/          # Data models and schemas (with RAG support)
│   │   └── utils/           # Utility functions (LLM client, validation)
│   ├── kb/                  # Knowledge Base (35+ documents) - Phase 1
│   │   ├── policies/        # Building policies (15 documents)
│   │   ├── sops/            # Standard Operating Procedures (10 documents)
│   │   ├── catalogs/        # Vendor/contact catalogs (5 documents)
│   │   └── slas/            # Service Level Agreements (5 documents)
│   ├── vector_stores/       # Vector database storage - Phase 1
│   │   └── chroma_db/       # ChromaDB persistent storage
│   ├── tests/               # Comprehensive test suite (70+ test cases) - Phase 1
│   │   ├── unit/            # Unit tests (chunking, embeddings, vector store)
│   │   ├── integration/     # Integration tests (schemas, performance)
│   │   └── fixtures/        # Test fixtures and sample documents
│   ├── docs/                # Technical documentation - Phase 1
│   │   ├── RAG_ARCHITECTURE.md      # RAG system design
│   │   ├── INGESTION_GUIDE.md       # How to add KB documents
│   │   ├── RETRIEVAL_TUNING.md      # Optimize RAG parameters
│   │   ├── SCHEMA_DESIGN.md         # Data model reference
│   │   ├── RAG_INTEGRATION_POINTS.md # Agent integration guide
│   │   ├── RAG_DATA_FLOW.md         # Visual flow diagrams
│   │   └── TESTING_INFRASTRUCTURE.md # Testing guide
│   ├── requirements.txt     # Python dependencies (with RAG packages)
│   └── Dockerfile           # Docker configuration
│
├── frontend/                # Frontend application (TBD)
│   ├── src/
│   └── package.json
│
├── ml/                      # Machine learning components
│   ├── scripts/             # Python scripts (model training, data generation)
│   ├── notebooks/           # Jupyter notebooks
│   ├── data/                # Synthetic datasets
│   └── models/              # Trained models (XGBoost, ARIMA)
│
├── infrastructure/          # Infrastructure as code
│   ├── aws/                 # AWS resources
│   └── docker/              # Docker compose
│
└── docs/                    # Project-wide documentation
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for frontend, framework TBD)
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
   # Enable RAG features
   RAG_ENABLED=true
   RAG_TOP_K=5
   RAG_SIMILARITY_THRESHOLD=0.7
   
   # Embedding configuration
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   EMBEDDING_CACHE_ENABLED=true
   
   # Vector store configuration
   VECTOR_STORE_TYPE=chromadb
   VECTOR_STORE_PATH=./vector_stores/chroma_db
   VECTOR_STORE_COLLECTION=apartment_kb
   ```
   
   See `backend/.env.example` for complete RAG configuration options (27 variables).

4. **Download embedding model** (automatic on first run)
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

5. **Initialize vector store** (future - after ingestion script)
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

2. **Generate synthetic data (Ticket 2)**
   ```bash
   python scripts/synthetic_message_generator.py
   ```

### Frontend Setup
Frontend framework selection pending (Ticket 3). See `frontend/README.md` for details.

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

## Documentation

### General Documentation
- **[Team Onboarding Guide](docs/TEAM_ONBOARDING.md)** - Complete setup instructions for team members
- **[AWS Resources Setup](docs/AWS_RESOURCES_SETUP.md)** - Step-by-step AWS resource creation (SQS, DynamoDB, IAM)
- **[Task 1 Setup Guide](infrastructure/TASK1_SETUP_GUIDE.md)** - Infrastructure setup checklist
- **[Project Architecture](docs/architecture.md)** - System architecture overview
- **[Contributing Guidelines](CONTRIBUTING.md)** - Git workflow and development practices

### RAG Documentation (Phase 1 - Complete)
- **[RAG Architecture](backend/docs/RAG_ARCHITECTURE.md)** - System design and component overview
- **[Ingestion Guide](backend/docs/INGESTION_GUIDE.md)** - How to add and update KB documents
- **[Retrieval Tuning](backend/docs/RETRIEVAL_TUNING.md)** - Optimize RAG parameters and performance
- **[Schema Design](backend/docs/SCHEMA_DESIGN.md)** - Data models and API schemas
- **[Integration Points](backend/docs/RAG_INTEGRATION_POINTS.md)** - Agent integration guide
- **[Data Flow Diagrams](backend/docs/RAG_DATA_FLOW.md)** - Visual flow diagrams
- **[Testing Infrastructure](backend/docs/TESTING_INFRASTRUCTURE.md)** - Test suite documentation

### Quick Start: RAG Features

**To use RAG in your queries:**

1. **Enable RAG** (in `.env`):
   ```bash
   RAG_ENABLED=true
   ```

2. **Submit a resident request**:
   ```bash
   curl -X POST http://localhost:8000/api/message/submit \
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
   - Review governance logs for full audit trail

**Configuration Tips:**
- Adjust `RAG_TOP_K` (3-7) to control document count
- Tune `RAG_SIMILARITY_THRESHOLD` (0.65-0.75) for precision/recall balance
- See [Retrieval Tuning Guide](backend/docs/RETRIEVAL_TUNING.md) for details

**Knowledge Base:**
- 35+ documents covering policies, SOPs, catalogs, SLAs
- Located in `backend/kb/`
- See [Ingestion Guide](backend/docs/INGESTION_GUIDE.md) to add documents

---

## Documentation

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)


