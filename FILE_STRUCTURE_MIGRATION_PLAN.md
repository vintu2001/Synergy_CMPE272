# File Structure Migration Plan
## From Monolith to Microservices

---

## Current Structure (Monolith)

```
Synergy_CMPE272/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── classification_agent.py
│   │   │   ├── risk_prediction_agent.py
│   │   │   ├── simulation_agent.py
│   │   │   ├── decision_agent.py
│   │   │   ├── learning_engine.py
│   │   │   ├── reasoning_engine.py
│   │   │   └── tools.py
│   │   ├── services/
│   │   │   ├── message_intake.py
│   │   │   ├── database.py
│   │   │   ├── execution_layer.py
│   │   │   ├── resident_api.py
│   │   │   └── admin_api.py
│   │   ├── rag/
│   │   │   ├── retriever.py
│   │   │   └── ingest/
│   │   ├── models/
│   │   │   └── schemas.py          # SHARED - Used by all services
│   │   ├── utils/
│   │   │   ├── llm_client.py       # SHARED - Used by multiple services
│   │   │   ├── helpers.py          # SHARED - Used by multiple services
│   │   │   ├── cloudwatch_logger.py
│   │   │   └── validate_env.py
│   │   ├── ml_models/              # ML models for risk prediction
│   │   └── main.py                 # Single entry point
│   ├── kb/                         # Knowledge base documents
│   ├── vector_stores/              # ChromaDB storage
│   ├── requirements.txt            # All dependencies
│   └── Dockerfile                  # Single container
```

---

## Proposed Microservices Structure

```
Synergy_CMPE272/
├── services/                       # NEW: All microservices
│   │
│   ├── request-management/         # Microservice 1
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py       # FastAPI routes
│   │   │   │   ├── resident_api.py
│   │   │   │   └── admin_api.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── database.py     # DynamoDB operations
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── schemas.py      # Request-specific schemas
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       ├── helpers.py      # Request-specific helpers
│   │   │       └── http_client.py  # HTTP client for calling other services
│   │   ├── requirements.txt           # Service-specific dependencies
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   ├── ai-processing/              # Microservice 2
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── routes.py       # Classification & risk prediction endpoints
│   │   │   ├── agents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── classification_agent.py
│   │   │   │   └── risk_prediction_agent.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── schemas.py      # Classification schemas
│   │   │   ├── ml_models/          # XGBoost models
│   │   │   │   ├── risk_prediction_model.pkl
│   │   │   │   ├── feature_columns.pkl
│   │   │   │   ├── label_encoders.pkl
│   │   │   │   └── model_metadata.json
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── llm_client.py   # LLM client for classification
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   ├── decision-simulation/        # Microservice 3
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── routes.py       # Simulation & decision endpoints
│   │   │   ├── agents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── simulation_agent.py
│   │   │   │   ├── decision_agent.py
│   │   │   │   └── tools.py
│   │   │   ├── rag/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── retriever.py
│   │   │   │   └── ingest/
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── schemas.py      # Simulation & decision schemas
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   └── llm_client.py   # LLM client for simulation/decision
│   │   │   ├── kb/                 # Knowledge base documents
│   │   │   │   ├── policies/
│   │   │   │   ├── sops/
│   │   │   │   ├── catalogs/
│   │   │   │   └── slas/
│   │   │   └── vector_stores/      # ChromaDB storage
│   │   │       └── chroma_db/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   ├── execution/                  # Microservice 4
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── routes.py       # Execution endpoints
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── execution_layer.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── schemas.py      # Execution schemas
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── http_client.py  # External API clients
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   └── shared/                     # NEW: Shared code library
│       ├── __init__.py
│       ├── schemas/                # Shared Pydantic models
│       │   ├── __init__.py
│       │   ├── common.py           # Common schemas (HealthCheck, etc.)
│       │   ├── request.py          # Request-related schemas
│       │   ├── classification.py  # Classification schemas
│       │   ├── simulation.py      # Simulation schemas
│       │   └── decision.py        # Decision schemas
│       ├── utils/                  # Shared utilities
│       │   ├── __init__.py
│       │   └── helpers.py          # Common helper functions
│       └── setup.py                # Package setup for pip install
│
├── backend/                        # KEEP: For backward compatibility during migration
│   └── (existing monolith - can be removed after migration)
│
├── frontend/                       # UNCHANGED
│
├── ml/                             # UNCHANGED
│
├── infrastructure/                 # Infrastructure as code
│   ├── terraform/                  # Terraform configs (optional)
│   ├── docker/                     # Docker compose for local dev
│   └── kubernetes/                 # K8s manifests (if using EKS)
│
└── scripts/                        # NEW: Migration and deployment scripts
    ├── migrate_to_microservices.py
    ├── build_all_services.sh
    └── deploy_all_services.sh
```

---

## Detailed Component Mapping

### 1. Request Management Service

**Files to Move:**
```
backend/app/services/database.py          → services/request-management/app/services/database.py
backend/app/services/resident_api.py      → services/request-management/app/api/resident_api.py
backend/app/services/admin_api.py         → services/request-management/app/api/admin_api.py
backend/app/services/message_intake.py    → services/request-management/app/services/orchestrator.py (refactored)
```

**Files to Create:**
```
services/request-management/app/main.py
services/request-management/app/api/routes.py
services/request-management/app/utils/http_client.py
services/request-management/requirements.txt
services/request-management/Dockerfile
```

**Dependencies Needed:**
- FastAPI
- boto3 (DynamoDB)
- httpx (for calling other services)
- pydantic (schemas)

---

### 2. AI Processing Service

**Files to Move:**
```
backend/app/agents/classification_agent.py  → services/ai-processing/app/agents/classification_agent.py
backend/app/agents/risk_prediction_agent.py  → services/ai-processing/app/agents/risk_prediction_agent.py
backend/app/ml_models/                       → services/ai-processing/app/ml_models/
backend/app/utils/llm_client.py             → services/ai-processing/app/utils/llm_client.py (classification part)
```

**Files to Create:**
```
services/ai-processing/app/main.py
services/ai-processing/app/api/routes.py
services/ai-processing/requirements.txt
services/ai-processing/Dockerfile
```

**Dependencies Needed:**
- FastAPI
- google-generativeai (Gemini)
- xgboost
- joblib
- numpy
- scikit-learn

---

### 3. Decision & Simulation Service

**Files to Move:**
```
backend/app/agents/simulation_agent.py      → services/decision-simulation/app/agents/simulation_agent.py
backend/app/agents/decision_agent.py        → services/decision-simulation/app/agents/decision_agent.py
backend/app/agents/tools.py                 → services/decision-simulation/app/agents/tools.py
backend/app/rag/                            → services/decision-simulation/app/rag/
backend/app/kb/                             → services/decision-simulation/app/kb/
backend/app/vector_stores/                  → services/decision-simulation/app/vector_stores/
backend/app/utils/llm_client.py             → services/decision-simulation/app/utils/llm_client.py (simulation/decision part)
```

**Files to Create:**
```
services/decision-simulation/app/main.py
services/decision-simulation/app/api/routes.py
services/decision-simulation/requirements.txt
services/decision-simulation/Dockerfile
```

**Dependencies Needed:**
- FastAPI
- google-generativeai (Gemini)
- chromadb
- sentence-transformers
- langchain

---

### 4. Execution Service

**Files to Move:**
```
backend/app/services/execution_layer.py     → services/execution/app/services/execution_layer.py
```

**Files to Create:**
```
services/execution/app/main.py
services/execution/app/api/routes.py
services/execution/requirements.txt
services/execution/Dockerfile
```

**Dependencies Needed:**
- FastAPI
- boto3 (SQS)
- httpx (external APIs)

---

## Shared Code Strategy

### Option 1: Shared Package (Recommended)

Create a `shared/` package that can be installed as a Python package:

```
services/shared/
├── setup.py
├── shared/
│   ├── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── request.py
│   │   ├── classification.py
│   │   ├── simulation.py
│   │   └── decision.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
└── requirements.txt
```

**Installation:**
```bash
# In each service's Dockerfile
COPY ../shared /app/shared
RUN pip install -e /app/shared
```

**Usage:**
```python
from shared.schemas.common import HealthCheck
from shared.schemas.request import MessageRequest
```

### Option 2: Copy Shared Code (Simpler, but less maintainable)

Copy shared schemas to each service that needs them. Update manually when schemas change.

### Option 3: Git Submodule (Advanced)

Create a separate repository for shared code and use git submodules.

**Recommendation: Use Option 1 (Shared Package)** for better maintainability.

---

## Requirements.txt Strategy

### Current: Single requirements.txt with all dependencies

### New: Service-specific requirements.txt

**services/request-management/requirements.txt:**
```txt
fastapi==0.115.4
uvicorn==0.34.0
boto3==1.35.0
httpx==0.27.2
pydantic==2.9.2
python-dotenv==1.0.1
```

**services/ai-processing/requirements.txt:**
```txt
fastapi==0.115.4
uvicorn==0.34.0
google-generativeai==0.8.3
xgboost==2.1.3
joblib==1.4.2
numpy==1.26.4
scikit-learn==1.5.2
pydantic==2.9.2
python-dotenv==1.0.1
```

**services/decision-simulation/requirements.txt:**
```txt
fastapi==0.115.4
uvicorn==0.34.0
google-generativeai==0.8.3
chromadb==0.4.24
sentence-transformers==3.3.1
langchain==0.1.20
pydantic==2.9.2
python-dotenv==1.0.1
```

**services/execution/requirements.txt:**
```txt
fastapi==0.115.4
uvicorn==0.34.0
boto3==1.35.0
httpx==0.27.2
pydantic==2.9.2
python-dotenv==1.0.1
```

---

## Dockerfile Changes

### Current: Single Dockerfile for monolith

### New: One Dockerfile per service

**Example: services/request-management/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy shared package
COPY ../shared /app/shared
RUN pip install -e /app/shared

# Copy service code
COPY app/ ./app/
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Environment
ENV PORT=8001
ENV PYTHONPATH=/app

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## Migration Steps

### Phase 1: Create New Structure (No Code Changes)

1. **Create directory structure:**
   ```bash
   mkdir -p services/{request-management,ai-processing,decision-simulation,execution}/app
   mkdir -p services/shared
   ```

2. **Create shared package:**
   ```bash
   cd services/shared
   # Create setup.py, shared/schemas/, shared/utils/
   ```

3. **Create basic service stubs:**
   - Create `main.py` for each service
   - Create `requirements.txt` for each service
   - Create `Dockerfile` for each service

### Phase 2: Extract and Move Code

1. **Move Request Management code:**
   ```bash
   cp backend/app/services/database.py services/request-management/app/services/
   cp backend/app/services/resident_api.py services/request-management/app/api/
   cp backend/app/services/admin_api.py services/request-management/app/api/
   ```

2. **Move AI Processing code:**
   ```bash
   cp backend/app/agents/classification_agent.py services/ai-processing/app/agents/
   cp backend/app/agents/risk_prediction_agent.py services/ai-processing/app/agents/
   cp -r backend/app/ml_models services/ai-processing/app/
   ```

3. **Move Decision & Simulation code:**
   ```bash
   cp backend/app/agents/simulation_agent.py services/decision-simulation/app/agents/
   cp backend/app/agents/decision_agent.py services/decision-simulation/app/agents/
   cp -r backend/app/rag services/decision-simulation/app/
   cp -r backend/app/kb services/decision-simulation/app/
   cp -r backend/vector_stores services/decision-simulation/app/
   ```

4. **Move Execution code:**
   ```bash
   cp backend/app/services/execution_layer.py services/execution/app/services/
   ```

### Phase 3: Refactor Code

1. **Update imports:**
   - Change relative imports to absolute
   - Update shared schema imports
   - Add HTTP client calls for inter-service communication

2. **Remove dependencies:**
   - Remove unused imports
   - Remove code that belongs to other services

3. **Add service communication:**
   - Add HTTP clients for calling other services
   - Update orchestrator to call services via HTTP

### Phase 4: Test Each Service

1. **Unit tests:** Test each service in isolation
2. **Integration tests:** Test service-to-service communication
3. **End-to-end tests:** Test full request flow

### Phase 5: Deploy

1. **Build containers:** Build Docker images for each service
2. **Push to ECR:** Push images to AWS ECR
3. **Deploy to ECS:** Deploy services to ECS Fargate
4. **Configure ALBs:** Set up load balancers
5. **Update frontend:** Update frontend API URLs

---

## Key Changes Required

### 1. Import Statements

**Before (Monolith):**
```python
from app.services.database import create_request
from app.agents.classification_agent import classify_message
```

**After (Microservices):**
```python
# In request-management service
from app.services.database import create_request
import httpx

# Call AI Processing Service
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{AI_PROCESSING_SERVICE_URL}/api/v1/classify",
        json={"message_text": message_text}
    )
```

### 2. Service Communication

**Before:** Direct function calls
```python
classification = await classify_message_endpoint(request)
```

**After:** HTTP calls
```python
classification = await http_client.post(
    f"{AI_PROCESSING_SERVICE_URL}/api/v1/classify",
    json=request.dict()
)
```

### 3. Configuration

**Before:** Single `.env` file
```env
GEMINI_API_KEY=xxx
AWS_REGION=us-west-2
```

**After:** Service-specific `.env` files
```env
# services/ai-processing/.env
GEMINI_API_KEY=xxx
PORT=8002

# services/request-management/.env
AI_PROCESSING_SERVICE_URL=http://ai-processing-service:8002
AWS_REGION=us-west-2
PORT=8001
```

### 4. Main Application Files

**Before:** Single `backend/app/main.py`
```python
from app.agents import classification_agent, simulation_agent
from app.services import message_intake

app.include_router(classification_agent.router)
app.include_router(simulation_agent.router)
app.include_router(message_intake.router)
```

**After:** Separate `main.py` per service
```python
# services/ai-processing/app/main.py
from app.api.routes import router

app = FastAPI()
app.include_router(router, prefix="/api/v1")
```

---

## File Structure Comparison

### Current Monolith Structure:
- **1 main.py** - All routes
- **1 requirements.txt** - All dependencies
- **1 Dockerfile** - Single container
- **Shared code** - Direct imports

### New Microservices Structure:
- **4 main.py files** - One per service
- **4 requirements.txt files** - Service-specific dependencies
- **4 Dockerfiles** - One per service
- **Shared package** - Installable package

---

## Benefits of New Structure

1. **Clear Separation:** Each service has its own directory
2. **Independent Deployment:** Deploy services independently
3. **Smaller Containers:** Each container only has needed dependencies
4. **Team Ownership:** Different teams can own different services
5. **Easier Testing:** Test services in isolation
6. **Better Scaling:** Scale services independently

---

## Challenges and Solutions

### Challenge 1: Shared Code Management
**Solution:** Use shared package that can be versioned and installed

### Challenge 2: Schema Synchronization
**Solution:** 
- Keep schemas in shared package
- Use versioning for schema changes
- Implement backward compatibility

### Challenge 3: Service Discovery
**Solution:**
- Use environment variables for service URLs (dev)
- Use ECS Service Discovery or API Gateway (prod)

### Challenge 4: Database Access
**Solution:**
- Request Management owns DynamoDB access
- Other services call Request Management API for data
- Or use IAM roles for direct DynamoDB access (if needed)

---

## Summary

**Yes, significant file structure changes are required:**

1. ✅ **Create new `services/` directory** with 4 service subdirectories
2. ✅ **Move code** from `backend/app/` to appropriate service directories
3. ✅ **Create shared package** for common code (schemas, utils)
4. ✅ **Create service-specific** requirements.txt, Dockerfile, main.py
5. ✅ **Refactor imports** to use shared package and HTTP clients
6. ✅ **Update configuration** to use service-specific .env files

**The monolith structure cannot be used as-is for microservices.** Each service needs:
- Its own directory
- Its own dependencies
- Its own container
- Its own entry point

This separation is essential for independent deployment, scaling, and team ownership.

