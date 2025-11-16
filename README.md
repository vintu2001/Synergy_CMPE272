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
├── services/                 # Microservices (NEW)
│   ├── request-management/  # Request Management Service (Railway)
│   │   ├── app/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── railway.json
│   ├── ai-processing/       # AI Processing Service (Railway)
│   │   ├── app/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── railway.json
│   ├── decision-simulation/ # Decision & Simulation Service (EC2)
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── execution/           # Execution Service (Railway)
│       ├── app/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── railway.json
│
├── backend/                 # Monolith (legacy - for reference)
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
    ├── docker/              # Docker compose
    └── ec2/                 # EC2 deployment configs
        └── docker-compose.yml
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for frontend)
- AWS Account with appropriate permissions
- Docker (for containerized development)
- Railway.app account (free - https://railway.app)
- GitHub account (for deployment)

---

## 🚀 Quick Start: Deploy Microservices

The system is now deployed as **4 microservices** using a **Hybrid Railway + EC2** strategy:

- **Railway.app** (3 services): Request Management, AI Processing, Execution
- **AWS EC2** (1 service): Decision & Simulation (with RAG/ChromaDB)

### Step 1: Deploy Services on Railway

1. **Sign up for Railway:**
   - Go to https://railway.app
   - Sign up with GitHub (free - $5 credit/month)

2. **Deploy Request Management Service:**
   ```bash
   # In Railway dashboard:
   # 1. Click "New Project"
   # 2. Select "Deploy from GitHub repo"
   # 3. Choose your repository
   # 4. Set root directory: services/request-management
   # 5. Add environment variables (see DEPLOYMENT_GUIDE.md)
   ```

3. **Deploy AI Processing Service:**
   ```bash
   # Same process, set root directory: services/ai-processing
   ```

4. **Deploy Execution Service:**
   ```bash
   # Same process, set root directory: services/execution
   ```

### Step 2: Deploy Decision & Simulation Service on EC2

1. **Launch EC2 Instance:**
   - Go to AWS Console → EC2
   - Launch Ubuntu 22.04 LTS (t2.micro - free tier)
   - Configure security group (open port 8003)

2. **SSH into EC2:**
   ```bash
   ssh -i your-key.pem ubuntu@<ec2-ip>
   ```

3. **Install Docker:**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker ubuntu
   newgrp docker
   ```

4. **Deploy Service:**
   ```bash
   git clone <your-repo>
   cd Synergy_CMPE272/infrastructure/ec2
   
   # Create .env file with GEMINI_API_KEY, AWS credentials
   nano .env
   
   # Deploy
   docker-compose up -d
   
   # Check status
   curl http://localhost:8003/health
   ```

### Step 3: Configure Service URLs

Update environment variables in Railway services:
- `AI_PROCESSING_SERVICE_URL` → Railway URL
- `DECISION_SIMULATION_SERVICE_URL` → `http://<ec2-ip>:8003`
- `EXECUTION_SERVICE_URL` → Railway URL

### Step 4: Test Deployment

```bash
# Test each service
curl https://request-management-service.up.railway.app/health
curl https://ai-processing-service.up.railway.app/health
curl http://<ec2-ip>:8003/health
curl https://execution-service.up.railway.app/health

# Test end-to-end
curl -X POST https://request-management-service.up.railway.app/api/v1/submit-request \
  -H "Content-Type: application/json" \
  -d '{"resident_id": "RES_1001", "message_text": "AC is broken"}'
```

**📖 For detailed deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

---

## 🧪 Local Testing (End-to-End from UI)

To test all microservices locally with the frontend:

### Quick Start

```bash
# Run setup script (initializes ChromaDB, creates config files)
./scripts/setup_local_testing.sh

# Edit environment variables
nano infrastructure/docker/.env

# Start all services
cd infrastructure/docker
docker-compose -f docker-compose.microservices.yml up -d

# Start frontend (in another terminal)
cd frontend
npm run dev
```

**Open:** `http://localhost:5173` in your browser

**📖 For detailed local testing instructions, see [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)**

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js (for frontend)
- AWS Account with appropriate permissions
- Docker (for containerized development)

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

1. **Run with Docker Compose (Monolith)**
   ```bash
   cd infrastructure/docker
   docker-compose up
   ```

2. **Run Microservices Locally**
   ```bash
   # Request Management
   cd services/request-management
   docker build -t request-management .
   docker run -p 8001:8001 request-management
   
   # AI Processing
   cd services/ai-processing
   docker build -t ai-processing .
   docker run -p 8002:8002 ai-processing
   
   # Decision & Simulation (needs ChromaDB)
   cd services/decision-simulation
   docker build -t decision-simulation .
   docker run -p 8003:8003 -v $(pwd)/vector_stores:/app/vector_stores decision-simulation
   
   # Execution
   cd services/execution
   docker build -t execution .
   docker run -p 8004:8004 execution
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

## Deployment Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide for Railway + EC2
- **[MICROSERVICES_ARCHITECTURE_PLAN.md](MICROSERVICES_ARCHITECTURE_PLAN.md)** - Architecture design and reasoning
- **[FILE_STRUCTURE_MIGRATION_PLAN.md](FILE_STRUCTURE_MIGRATION_PLAN.md)** - File structure changes
- **[CHROMADB_AND_DEPLOYMENT_OPTIONS.md](CHROMADB_AND_DEPLOYMENT_OPTIONS.md)** - ChromaDB alternatives and deployment options
- **[FREE_DEPLOYMENT_PLATFORMS.md](FREE_DEPLOYMENT_PLATFORMS.md)** - Free platform comparison

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Railway.app Documentation](https://docs.railway.app/)
- [Docker Documentation](https://docs.docker.com/)
