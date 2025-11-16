# Migration Helper
## Moving Code from Monolith to Microservices

This guide helps you move actual code from the monolith (`backend/app/`) to the microservices structure.

---

## Code Mapping Reference

### Request Management Service

**Files to Copy:**
```bash
# From monolith
backend/app/services/database.py
  → services/request-management/app/services/database.py

backend/app/services/resident_api.py
  → services/request-management/app/api/resident_api.py

backend/app/services/admin_api.py
  → services/request-management/app/api/admin_api.py

backend/app/services/message_intake.py
  → services/request-management/app/services/orchestrator.py
  # Refactor to call other services via HTTP instead of direct imports

backend/app/models/schemas.py (relevant parts)
  → services/request-management/app/models/schemas.py
  # Extract: MessageRequest, ResidentRequest, Status, SelectOptionRequest, etc.
```

**Changes Needed:**
1. Replace direct imports with HTTP calls:
   ```python
   # Before (monolith):
   from app.agents.classification_agent import classify_message
   classification = await classify_message(request)
   
   # After (microservice):
   import httpx
   async with httpx.AsyncClient() as client:
       response = await client.post(
           f"{AI_PROCESSING_SERVICE_URL}/api/v1/classify",
           json={"resident_id": request.resident_id, "message_text": request.message_text}
       )
       classification = response.json()
   ```

2. Update imports:
   ```python
   # Remove:
   from app.agents import ...
   from app.services.governance import ...
   
   # Keep:
   from app.services.database import ...
   from app.models.schemas import ...
   ```

---

### AI Processing Service

**Files to Copy:**
```bash
backend/app/agents/classification_agent.py
  → services/ai-processing/app/agents/classification_agent.py

backend/app/agents/risk_prediction_agent.py
  → services/ai-processing/app/agents/risk_prediction_agent.py

backend/app/ml_models/
  → services/ai-processing/app/ml_models/

backend/app/utils/llm_client.py (classification part)
  → services/ai-processing/app/utils/llm_client.py
  # Keep only classification-related methods

backend/app/models/schemas.py (relevant parts)
  → services/ai-processing/app/models/schemas.py
  # Extract: ClassificationResponse, MessageRequest, etc.
```

**Changes Needed:**
1. Create API routes:
   ```python
   # services/ai-processing/app/api/routes.py
   from fastapi import APIRouter
   from app.agents.classification_agent import classify_message
   from app.agents.risk_prediction_agent import predict_risk
   
   router = APIRouter()
   
   @router.post("/classify")
   async def classify(request: MessageRequest):
       return await classify_message(request)
   
   @router.post("/predict-risk")
   async def predict_risk_endpoint(classification: ClassificationResponse):
       return await predict_risk(classification)
   ```

2. Remove dependencies on other services:
   - Remove RAG imports
   - Remove database imports
   - Keep only ML/classification code

---

### Decision & Simulation Service

**Files to Copy:**
```bash
backend/app/agents/simulation_agent.py
  → services/decision-simulation/app/agents/simulation_agent.py

backend/app/agents/decision_agent.py
  → services/decision-simulation/app/agents/decision_agent.py

backend/app/agents/tools.py
  → services/decision-simulation/app/agents/tools.py

backend/app/rag/
  → services/decision-simulation/app/rag/

backend/app/kb/
  → services/decision-simulation/app/kb/

backend/vector_stores/
  → services/decision-simulation/vector_stores/

backend/app/utils/llm_client.py (simulation/decision part)
  → services/decision-simulation/app/utils/llm_client.py
  # Keep only simulation/decision-related methods

backend/app/models/schemas.py (relevant parts)
  → services/decision-simulation/app/models/schemas.py
  # Extract: SimulationResponse, DecisionResponse, SimulatedOption, etc.
```

**Changes Needed:**
1. Create API routes:
   ```python
   # services/decision-simulation/app/api/routes.py
   from fastapi import APIRouter
   from app.agents.simulation_agent import simulator
   from app.agents.decision_agent import make_decision
   
   router = APIRouter()
   
   @router.post("/simulate")
   async def simulate(request: SimulationRequest):
       return await simulator.generate_options(...)
   
   @router.post("/decide")
   async def decide(request: DecisionRequest):
       return await make_decision(request)
   ```

2. Keep RAG system intact:
   - ChromaDB connection
   - RAG retriever
   - Knowledge base

---

### Execution Service

**Files to Copy:**
```bash
backend/app/services/execution_layer.py
  → services/execution/app/services/execution_layer.py

backend/app/models/schemas.py (relevant parts)
  → services/execution/app/models/schemas.py
  # Extract: ExecutionRequest, etc.
```

**Changes Needed:**
1. Create API routes:
   ```python
   # services/execution/app/api/routes.py
   from fastapi import APIRouter
   from app.services.execution_layer import execute_decision
   
   router = APIRouter()
   
   @router.post("/execute")
   async def execute(request: ExecutionRequest):
       return await execute_decision(request)
   ```

---

## Step-by-Step Migration Process

### Step 1: Copy Base Files

```bash
# Request Management
cp backend/app/services/database.py services/request-management/app/services/
cp backend/app/services/resident_api.py services/request-management/app/api/
cp backend/app/services/admin_api.py services/request-management/app/api/

# AI Processing
cp -r backend/app/agents/classification_agent.py services/ai-processing/app/agents/
cp -r backend/app/agents/risk_prediction_agent.py services/ai-processing/app/agents/
cp -r backend/app/ml_models services/ai-processing/app/

# Decision & Simulation
cp -r backend/app/agents/simulation_agent.py services/decision-simulation/app/agents/
cp -r backend/app/agents/decision_agent.py services/decision-simulation/app/agents/
cp -r backend/app/agents/tools.py services/decision-simulation/app/agents/
cp -r backend/app/rag services/decision-simulation/app/
cp -r backend/app/kb services/decision-simulation/app/
cp -r backend/vector_stores services/decision-simulation/

# Execution
cp backend/app/services/execution_layer.py services/execution/app/services/
```

### Step 2: Extract Schemas

Create a script to extract relevant schemas for each service:

```python
# scripts/extract_schemas.py
# This script helps identify which schemas each service needs
```

**Manual Process:**
1. Read `backend/app/models/schemas.py`
2. Identify schemas used by each service
3. Copy relevant schemas to each service's `app/models/schemas.py`

### Step 3: Refactor Orchestrator

The orchestrator (`services/request-management/app/services/orchestrator.py`) needs to:
1. Call AI Processing service via HTTP
2. Call Decision & Simulation service via HTTP
3. Call Execution service via HTTP
4. Store results in DynamoDB

**Example Refactored Code:**
```python
import httpx
import os

AI_PROCESSING_URL = os.getenv("AI_PROCESSING_SERVICE_URL")
DECISION_SIMULATION_URL = os.getenv("DECISION_SIMULATION_SERVICE_URL")
EXECUTION_URL = os.getenv("EXECUTION_SERVICE_URL")

@router.post("/submit-request")
async def submit_request(request: MessageRequest):
    # Step 1: Classify
    async with httpx.AsyncClient() as client:
        classify_response = await client.post(
            f"{AI_PROCESSING_URL}/api/v1/classify",
            json={"resident_id": request.resident_id, "message_text": request.message_text}
        )
        classification = classify_response.json()
    
    # Step 2: Predict Risk
    async with httpx.AsyncClient() as client:
        risk_response = await client.post(
            f"{AI_PROCESSING_URL}/api/v1/predict-risk",
            json=classification
        )
        risk_result = risk_response.json()
    
    # Step 3: Generate Options
    async with httpx.AsyncClient() as client:
        simulate_response = await client.post(
            f"{DECISION_SIMULATION_URL}/api/v1/simulate",
            json={
                "category": classification["category"],
                "urgency": classification["urgency"],
                "message_text": request.message_text,
                "resident_id": request.resident_id,
                "risk_score": risk_result["risk_forecast"]
            }
        )
        simulation = simulate_response.json()
    
    # Step 4: Make Decision
    async with httpx.AsyncClient() as client:
        decision_response = await client.post(
            f"{DECISION_SIMULATION_URL}/api/v1/decide",
            json={
                "classification": classification,
                "simulation": simulation
            }
        )
        decision = decision_response.json()
    
    # Step 5: Store in DynamoDB
    from app.services.database import create_request
    # ... store request ...
    
    return {
        "status": "submitted",
        "request_id": request_id,
        "classification": classification,
        "simulation": simulation,
        "decision": decision
    }
```

### Step 4: Update Imports

For each service, update imports to:
1. Remove cross-service imports
2. Keep only service-specific imports
3. Add HTTP client for inter-service calls

### Step 5: Test Each Service

1. **Test locally:**
   ```bash
   cd services/request-management
   docker build -t request-management .
   docker run -p 8001:8001 request-management
   ```

2. **Test endpoints:**
   ```bash
   curl http://localhost:8001/health
   ```

3. **Fix import errors:**
   - Add missing dependencies to requirements.txt
   - Fix import paths
   - Add missing schemas

---

## Common Migration Issues

### Issue: Missing Dependencies

**Solution:**
- Check which packages each service actually uses
- Add to service-specific requirements.txt
- Remove unused packages

### Issue: Circular Dependencies

**Solution:**
- Remove cross-service imports
- Use HTTP calls instead
- Extract shared code to separate package (if needed)

### Issue: Schema Duplication

**Solution:**
- Create shared schemas package (optional)
- Or copy schemas to each service (simpler for now)
- Keep schemas in sync manually

### Issue: Environment Variables

**Solution:**
- Create .env.example for each service
- Document required variables
- Set in Railway/EC2 deployment

---

## Testing After Migration

1. **Unit Tests:**
   - Test each service in isolation
   - Mock HTTP calls to other services

2. **Integration Tests:**
   - Test service-to-service communication
   - Use test containers or mock services

3. **End-to-End Tests:**
   - Test complete request flow
   - Verify all services work together

---

## Next Steps

1. **Copy files** using the mapping above
2. **Refactor orchestrator** to use HTTP calls
3. **Update imports** in each service
4. **Test locally** with Docker
5. **Deploy to Railway/EC2**
6. **Test deployed services**

---

## Quick Reference

**Service Dependencies:**
- Request Management → AI Processing, Decision & Simulation, Execution
- AI Processing → None (standalone)
- Decision & Simulation → None (standalone, uses RAG)
- Execution → None (standalone)

**Shared Code:**
- Schemas (copy to each service)
- Helpers (copy if needed, or create shared package)

**Communication:**
- Synchronous: HTTP/REST
- Asynchronous: SQS (for execution events)

