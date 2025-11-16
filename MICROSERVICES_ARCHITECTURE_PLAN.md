# Microservices Architecture Plan
## Agentic Apartment Manager - Migration from Monolith to Microservices

---

## Executive Summary

This document outlines the migration strategy from the current monolithic architecture to a 4-microservice architecture. The migration is designed to improve scalability, maintainability, and enable independent deployment of services.

---

## Current Monolithic Architecture Analysis

### Current Components:
1. **Agents Layer**:
   - Classification Agent (NLP, rule-based + LLM)
   - Risk Prediction Agent (XGBoost ML model)
   - Simulation Agent (LLM + RAG + SimPy)
   - Decision Agent (Policy-based scoring + RAG)
   - Learning Engine
   - Reasoning Engine

2. **Services Layer**:
   - Message Intake Service (Orchestrator)
   - Execution Layer (External API calls)
   - Database Service (DynamoDB operations)
   - Admin API
   - Resident API

3. **RAG System**:
   - RAG Retriever (ChromaDB vector search)
   - Knowledge Base (35+ documents)
   - Embedding model (SentenceTransformers)

4. **Infrastructure**:
   - DynamoDB (Request storage)
   - SQS (Event queue)
   - CloudWatch (Logging)

### Current Flow:
```
Resident Request → Message Intake → Classification → Risk Prediction → 
Simulation (with RAG) → Decision (with RAG) → Execution → Database
```

---

## Proposed 4-Microservice Architecture

### Microservice 1: Request Management Service
**Port: 8001**

#### Responsibilities:
- Request lifecycle management
- Request CRUD operations
- Request status tracking
- Resident and Admin APIs
- Request history retrieval
- Database operations (DynamoDB)

#### Components:
- `services/database.py` → **Request Management Service**
- `services/resident_api.py` → **Request Management Service**
- `services/admin_api.py` → **Request Management Service**
- Request storage and retrieval logic

#### API Endpoints:
```
POST   /api/v1/requests              # Create request
GET    /api/v1/requests/{request_id} # Get request
GET    /api/v1/requests              # List requests (admin)
GET    /api/v1/residents/{id}/requests # Get resident requests
PUT    /api/v1/requests/{request_id} # Update request status
POST   /api/v1/requests/{id}/select-option # Select option
POST   /api/v1/requests/{id}/resolve # Resolve request
```

#### Data Store:
- **DynamoDB**: `aam_requests` table
- Owns: Request data, status, metadata

#### Dependencies:
- DynamoDB (direct)
- SQS (publishes events)
- CloudWatch (logging)

#### Reasoning:
- **Single Responsibility**: Manages all request-related operations
- **Data Ownership**: Owns the request domain model
- **API Gateway**: Single entry point for request operations
- **Scalability**: Can scale independently based on request volume
- **Isolation**: Request management changes don't affect AI processing

---

### Microservice 2: AI Processing Service
**Port: 8002**

#### Responsibilities:
- Message classification (rule-based + LLM)
- Risk prediction (XGBoost model)
- ML model serving
- Text analysis and NLP

#### Components:
- `agents/classification_agent.py` → **AI Processing Service**
- `agents/risk_prediction_agent.py` → **AI Processing Service**
- `ml_models/` → **AI Processing Service**
- `utils/llm_client.py` (classification part) → **AI Processing Service**

#### API Endpoints:
```
POST   /api/v1/classify              # Classify message
POST   /api/v1/predict-risk          # Predict risk score
GET    /api/v1/health                 # Health check
```

#### Data Store:
- **Local Storage**: ML model files (XGBoost, encoders)
- **In-Memory**: Model cache

#### Dependencies:
- Gemini API (LLM for classification)
- CloudWatch (logging)
- No database dependencies

#### Reasoning:
- **ML Isolation**: ML models require specific resources (GPU/CPU, memory)
- **Independent Scaling**: Can scale based on classification load
- **Model Versioning**: Can deploy new models without affecting other services
- **Resource Optimization**: ML workloads can run on GPU instances
- **Stateless**: No persistent state, pure computation service

---

### Microservice 3: Decision & Simulation Service
**Port: 8003**

#### Responsibilities:
- Resolution option simulation
- Decision making (policy-based scoring)
- RAG retrieval (knowledge base access)
- Option generation with LLM
- Policy compliance checking

#### Components:
- `agents/simulation_agent.py` → **Decision & Simulation Service**
- `agents/decision_agent.py` → **Decision & Simulation Service**
- `rag/` (entire module) → **Decision & Simulation Service**
- `agents/tools.py` → **Decision & Simulation Service**
- `utils/llm_client.py` (simulation/decision part) → **Decision & Simulation Service**

#### API Endpoints:
```
POST   /api/v1/simulate              # Generate resolution options
POST   /api/v1/decide                # Make decision
POST   /api/v1/rag/retrieve          # Retrieve knowledge base docs
GET    /api/v1/rag/config            # RAG configuration
GET    /api/v1/health                # Health check
```

#### Data Store:
- **ChromaDB**: Vector store for knowledge base
- **Local Storage**: Knowledge base documents, embeddings cache
- **In-Memory**: RAG retriever cache

#### Dependencies:
- Gemini API (LLM for simulation)
- ChromaDB (vector database)
- CloudWatch (logging)

#### Reasoning:
- **RAG Coupling**: Simulation and Decision both heavily use RAG
- **Knowledge Domain**: Owns the knowledge base and retrieval logic
- **LLM Workload**: Both services use LLM for generation
- **Policy Logic**: Decision-making requires policy knowledge (RAG)
- **Resource Sharing**: RAG infrastructure (embeddings, vector DB) shared efficiently
- **Cohesive Domain**: Simulation and Decision are tightly coupled in the decision-making flow

---

### Microservice 4: Execution Service
**Port: 8004**

#### Responsibilities:
- Execute selected decisions/actions
- External system integrations
- Action orchestration
- Workflow management
- Notification sending

#### Components:
- `services/execution_layer.py` → **Execution Service**
- External API integrations
- Action execution logic

#### API Endpoints:
```
POST   /api/v1/execute               # Execute an action
POST   /api/v1/notify                # Send notifications
GET    /api/v1/executions/{id}       # Get execution status
GET    /api/v1/health                # Health check
```

#### Data Store:
- **DynamoDB**: Execution logs (optional, for audit)
- **External Systems**: Maintenance systems, billing systems, etc.

#### Dependencies:
- External APIs (maintenance, billing, delivery systems)
- SQS (receives execution events)
- CloudWatch (logging)
- DynamoDB (optional, for execution history)

#### Reasoning:
- **External Integration**: Isolates external system dependencies
- **Failure Isolation**: External system failures don't affect core services
- **Retry Logic**: Can implement sophisticated retry mechanisms
- **Rate Limiting**: Can handle external API rate limits independently
- **Action Domain**: Owns the execution domain model

---

## Service Communication Architecture

### Communication Patterns:

#### 1. Synchronous (HTTP/REST):
- **Request Management** → **AI Processing**: Classification, Risk Prediction
- **Request Management** → **Decision & Simulation**: Generate options, Make decisions
- **Request Management** → **Execution**: Execute actions
- **Frontend** → **Request Management**: All user-facing APIs

#### 2. Asynchronous (SQS/Event-Driven):
- **Request Management** → SQS → **Execution Service**: Action execution events
- **Request Management** → SQS → **Decision & Simulation**: Background processing (optional)

#### 3. Service Mesh (Future):
- Consider AWS App Mesh or Istio for service-to-service communication
- Circuit breakers, retries, timeouts

---

## Data Flow Architecture

### Request Submission Flow:
```
1. Frontend → Request Management Service (POST /api/v1/requests)
2. Request Management → AI Processing Service (POST /api/v1/classify)
3. Request Management → AI Processing Service (POST /api/v1/predict-risk)
4. Request Management → Decision & Simulation Service (POST /api/v1/simulate)
   └─ Decision & Simulation uses RAG internally
5. Request Management → Decision & Simulation Service (POST /api/v1/decide)
6. Request Management stores result in DynamoDB
7. Request Management → SQS → Execution Service (when action selected)
8. Execution Service executes action and updates status
```

### Data Ownership:
- **Request Management**: Owns request data, status, metadata
- **AI Processing**: Stateless, no data ownership
- **Decision & Simulation**: Owns knowledge base, RAG data
- **Execution**: Owns execution logs (optional)

---

## Deployment Plan

### Infrastructure Components:

#### 1. Container Registry:
- **AWS ECR** (Elastic Container Registry)
- One repository per microservice:
  - `synergy/request-management-service`
  - `synergy/ai-processing-service`
  - `synergy/decision-simulation-service`
  - `synergy/execution-service`

#### 2. Container Orchestration:
- **AWS ECS (Fargate)** - Serverless containers
- **Alternative**: AWS EKS (Kubernetes) for more control

#### 3. Load Balancing:
- **AWS Application Load Balancer (ALB)**
- One ALB per microservice (or API Gateway)

#### 4. API Gateway:
- **AWS API Gateway** (optional, for unified API)
- Routes to appropriate microservice
- Handles authentication, rate limiting

#### 5. Service Discovery:
- **AWS Cloud Map** or **ECS Service Discovery**
- Services discover each other by name

#### 6. Message Queue:
- **AWS SQS** (Simple Queue Service)
- For async communication

#### 7. Database:
- **AWS DynamoDB** (shared, but with service-specific tables)
- **ChromaDB** (for Decision & Simulation Service, can be containerized)

#### 8. Monitoring:
- **AWS CloudWatch** (logs, metrics, alarms)
- **AWS X-Ray** (distributed tracing)

---

## Detailed Deployment Plan

### Phase 1: Containerization

#### Step 1.1: Create Dockerfiles for Each Service

**Request Management Service** (`services/request-management/Dockerfile`):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
ENV PORT=8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**AI Processing Service** (`services/ai-processing/Dockerfile`):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/agents/classification_agent.py ./app/
COPY app/agents/risk_prediction_agent.py ./app/
COPY app/ml_models/ ./app/ml_models/
COPY app/utils/llm_client.py ./app/utils/
ENV PORT=8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

**Decision & Simulation Service** (`services/decision-simulation/Dockerfile`):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/agents/simulation_agent.py ./app/
COPY app/agents/decision_agent.py ./app/
COPY app/rag/ ./app/rag/
COPY app/kb/ ./app/kb/
COPY app/vector_stores/ ./app/vector_stores/
ENV PORT=8003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

**Execution Service** (`services/execution/Dockerfile`):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/services/execution_layer.py ./app/
ENV PORT=8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

#### Step 1.2: Build and Push to ECR
```bash
# For each service
aws ecr create-repository --repository-name synergy/request-management-service
docker build -t synergy/request-management-service:latest .
docker tag synergy/request-management-service:latest <account>.dkr.ecr.<region>.amazonaws.com/synergy/request-management-service:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/synergy/request-management-service:latest
```

---

### Phase 2: ECS Task Definitions

#### Request Management Service Task Definition:
```json
{
  "family": "request-management-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [{
    "name": "request-management",
    "image": "<account>.dkr.ecr.<region>.amazonaws.com/synergy/request-management-service:latest",
    "portMappings": [{
      "containerPort": 8001,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "AWS_REGION", "value": "us-west-2"},
      {"name": "AWS_DYNAMODB_TABLE_NAME", "value": "aam_requests"},
      {"name": "AWS_SQS_QUEUE_URL", "value": "<sqs-url>"},
      {"name": "AI_PROCESSING_SERVICE_URL", "value": "http://ai-processing-service:8002"},
      {"name": "DECISION_SIMULATION_SERVICE_URL", "value": "http://decision-simulation-service:8003"},
      {"name": "EXECUTION_SERVICE_URL", "value": "http://execution-service:8004"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/request-management",
        "awslogs-region": "us-west-2",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
```

#### AI Processing Service Task Definition:
```json
{
  "family": "ai-processing-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [{
    "name": "ai-processing",
    "image": "<account>.dkr.ecr.<region>.amazonaws.com/synergy/ai-processing-service:latest",
    "portMappings": [{
      "containerPort": 8002,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "GEMINI_API_KEY", "value": "<key>"},
      {"name": "AWS_REGION", "value": "us-west-2"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/ai-processing",
        "awslogs-region": "us-west-2"
      }
    }
  }]
}
```

#### Decision & Simulation Service Task Definition:
```json
{
  "family": "decision-simulation-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [{
    "name": "decision-simulation",
    "image": "<account>.dkr.ecr.<region>.amazonaws.com/synergy/decision-simulation-service:latest",
    "portMappings": [{
      "containerPort": 8003,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "GEMINI_API_KEY", "value": "<key>"},
      {"name": "RAG_ENABLED", "value": "true"},
      {"name": "VECTOR_STORE_PATH", "value": "/app/vector_stores/chroma_db"},
      {"name": "AWS_REGION", "value": "us-west-2"}
    ],
    "mountPoints": [{
      "sourceVolume": "vector-store",
      "containerPath": "/app/vector_stores"
    }],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/decision-simulation",
        "awslogs-region": "us-west-2"
      }
    }
  }],
  "volumes": [{
    "name": "vector-store",
    "efsVolumeConfiguration": {
      "fileSystemId": "<efs-id>",
      "rootDirectory": "/chroma_db"
    }
  }]
}
```

#### Execution Service Task Definition:
```json
{
  "family": "execution-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [{
    "name": "execution",
    "image": "<account>.dkr.ecr.<region>.amazonaws.com/synergy/execution-service:latest",
    "portMappings": [{
      "containerPort": 8004,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "AWS_REGION", "value": "us-west-2"},
      {"name": "AWS_SQS_QUEUE_URL", "value": "<sqs-url>"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/execution",
        "awslogs-region": "us-west-2"
      }
    }
  }]
}
```

---

### Phase 3: ECS Services and Load Balancers

#### Create ECS Cluster:
```bash
aws ecs create-cluster --cluster-name synergy-cluster
```

#### Create ALB for Each Service:
```bash
# Request Management ALB
aws elbv2 create-load-balancer \
  --name request-management-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# AI Processing ALB
aws elbv2 create-load-balancer \
  --name ai-processing-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Decision & Simulation ALB
aws elbv2 create-load-balancer \
  --name decision-simulation-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Execution ALB
aws elbv2 create-load-balancer \
  --name execution-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx
```

#### Create ECS Services:
```bash
# Request Management Service
aws ecs create-service \
  --cluster synergy-cluster \
  --service-name request-management-service \
  --task-definition request-management-service \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<target-group-arn>,containerName=request-management,containerPort=8001"

# AI Processing Service
aws ecs create-service \
  --cluster synergy-cluster \
  --service-name ai-processing-service \
  --task-definition ai-processing-service \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<target-group-arn>,containerName=ai-processing,containerPort=8002"

# Decision & Simulation Service
aws ecs create-service \
  --cluster synergy-cluster \
  --service-name decision-simulation-service \
  --task-definition decision-simulation-service \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<target-group-arn>,containerName=decision-simulation,containerPort=8003"

# Execution Service
aws ecs create-service \
  --cluster synergy-cluster \
  --service-name execution-service \
  --task-definition execution-service \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<target-group-arn>,containerName=execution,containerPort=8004"
```

---

### Phase 4: Service Discovery and Communication

#### Option A: Direct Service URLs (Development)
- Use ECS service discovery or internal ALB DNS names
- Configure via environment variables

#### Option B: API Gateway (Production)
- Create REST API in API Gateway
- Map routes to ALB endpoints
- Handle authentication, rate limiting

#### Option C: Service Mesh (Advanced)
- AWS App Mesh
- Istio on EKS

---

### Phase 5: Database and Storage

#### DynamoDB:
- Keep existing `aam_requests` table
- All services can access (with IAM roles)
- Request Management Service is primary owner

#### ChromaDB (Vector Store):
- **Option 1**: EFS (Elastic File System) - Shared storage
- **Option 2**: Container volume (ephemeral)
- **Option 3**: S3 + local cache (hybrid)
- **Recommended**: EFS for persistence

#### EFS Setup:
```bash
aws efs create-file-system \
  --creation-token chroma-db-storage \
  --performance-mode generalPurpose \
  --throughput-mode provisioned \
  --provisioned-throughput-in-mibps 100

aws efs create-mount-target \
  --file-system-id <efs-id> \
  --subnet-id subnet-xxx \
  --security-groups sg-xxx
```

---

### Phase 6: Monitoring and Observability

#### CloudWatch Logs:
- Each service logs to `/ecs/<service-name>`
- Centralized log aggregation

#### CloudWatch Metrics:
- ECS service metrics (CPU, memory, request count)
- Custom application metrics
- Alarms for error rates, latency

#### AWS X-Ray:
- Distributed tracing
- Service map visualization
- Performance bottleneck identification

#### Setup:
```bash
# Enable X-Ray for each service
# Add X-Ray daemon sidecar container
# Instrument code with X-Ray SDK
```

---

## Migration Strategy

### Strategy: Strangler Fig Pattern

#### Phase 1: Parallel Run (2-4 weeks)
1. Deploy microservices alongside monolith
2. Route 10% of traffic to microservices
3. Monitor and fix issues
4. Gradually increase traffic percentage

#### Phase 2: Feature Parity (2-4 weeks)
1. Ensure all features work in microservices
2. Performance testing
3. Load testing

#### Phase 3: Cutover (1 week)
1. Route 100% traffic to microservices
2. Keep monolith running for rollback
3. Monitor for 1 week

#### Phase 4: Decommission (1 week)
1. Shut down monolith
2. Clean up resources
3. Update documentation

---

## Cost Estimation

### ECS Fargate Costs (Monthly):
- **Request Management**: 2 tasks × 0.5 vCPU × 1GB × $0.04/vCPU-hour × 730 hours = **$29.20**
- **AI Processing**: 2 tasks × 1 vCPU × 2GB × $0.04/vCPU-hour × 730 hours = **$58.40**
- **Decision & Simulation**: 2 tasks × 2 vCPU × 4GB × $0.04/vCPU-hour × 730 hours = **$116.80**
- **Execution**: 2 tasks × 0.25 vCPU × 0.5GB × $0.04/vCPU-hour × 730 hours = **$14.60**

**Total ECS**: ~$219/month

### ALB Costs:
- 4 ALBs × $16.20/month = **$64.80/month**

### EFS Costs:
- 100 GB × $0.30/GB = **$30/month**

### Data Transfer:
- Estimated: **$20-50/month**

### Total Estimated Monthly Cost: **~$334-364/month**

---

## Reasoning for Each Microservice

### 1. Request Management Service

**Why Separate?**
- **Data Ownership**: Owns the core domain model (requests)
- **API Gateway Pattern**: Single entry point for all request operations
- **Scalability**: Request volume can scale independently from AI processing
- **Team Ownership**: Different team can own request management vs AI
- **Deployment Independence**: Can deploy request API changes without affecting AI models

**Boundaries**:
- Owns: Request CRUD, status management, resident/admin APIs
- Does NOT own: AI processing, decision logic, execution

**Communication**:
- Calls: AI Processing, Decision & Simulation, Execution
- Publishes: SQS events for execution

---

### 2. AI Processing Service

**Why Separate?**
- **Resource Requirements**: ML models need specific CPU/memory/GPU resources
- **Model Versioning**: Can deploy new models without affecting other services
- **Scaling**: Classification load may differ from request volume
- **Technology Stack**: ML-specific dependencies (XGBoost, transformers)
- **Stateless**: Pure computation, no data ownership
- **Isolation**: ML model failures don't affect request management

**Boundaries**:
- Owns: Classification logic, risk prediction models
- Does NOT own: Request data, knowledge base, execution

**Communication**:
- Called by: Request Management Service
- Stateless: No persistent storage

---

### 3. Decision & Simulation Service

**Why Combine?**
- **RAG Coupling**: Both heavily depend on RAG/knowledge base
- **Shared Infrastructure**: ChromaDB, embeddings, vector store
- **Workflow Coupling**: Simulation → Decision is a tight workflow
- **Knowledge Domain**: Both require policy/knowledge access
- **LLM Usage**: Both use LLM for generation
- **Resource Efficiency**: Sharing RAG infrastructure is more efficient

**Why Not Separate?**
- Separating would require:
  - Duplicate RAG infrastructure (2x ChromaDB, 2x embeddings)
  - Network calls between services (latency)
  - Data consistency issues (knowledge base sync)
  - Higher costs (2x storage, 2x compute)

**Boundaries**:
- Owns: Simulation logic, decision logic, RAG system, knowledge base
- Does NOT own: Request data, ML models, execution

**Communication**:
- Called by: Request Management Service
- Uses: ChromaDB (vector store), Gemini API (LLM)

---

### 4. Execution Service

**Why Separate?**
- **External Dependencies**: Isolates external system integrations
- **Failure Isolation**: External API failures don't affect core services
- **Retry Logic**: Can implement sophisticated retry/backoff
- **Rate Limiting**: Handles external API rate limits
- **Async Processing**: Can process execution events asynchronously
- **Scalability**: Execution load may differ from request volume

**Boundaries**:
- Owns: Execution logic, external integrations, action orchestration
- Does NOT own: Request data, AI processing, decision logic

**Communication**:
- Called by: Request Management Service (sync)
- Receives: SQS events (async)
- Calls: External APIs (maintenance, billing, etc.)

---

## Benefits of This Architecture

### 1. Scalability
- **Independent Scaling**: Scale each service based on its load
- **Resource Optimization**: Right-size each service (AI needs more CPU, Execution needs less)
- **Horizontal Scaling**: Add more instances of high-load services

### 2. Maintainability
- **Clear Boundaries**: Each service has clear responsibilities
- **Team Ownership**: Different teams can own different services
- **Technology Flexibility**: Can use different tech stacks per service

### 3. Deployment
- **Independent Deployment**: Deploy services without affecting others
- **Rollback Safety**: Rollback one service without affecting others
- **Blue-Green Deployment**: Easier to implement per service

### 4. Resilience
- **Failure Isolation**: One service failure doesn't cascade
- **Circuit Breakers**: Can implement per-service circuit breakers
- **Graceful Degradation**: Services can degrade independently

### 5. Development
- **Parallel Development**: Teams can work on different services
- **Faster Iteration**: Smaller codebases = faster development cycles
- **Testing**: Easier to test services in isolation

---

## Challenges and Mitigations

### Challenge 1: Service Communication Latency
**Mitigation**:
- Use async communication (SQS) where possible
- Implement caching (Redis) for frequently accessed data
- Use connection pooling
- Consider service mesh for optimized routing

### Challenge 2: Data Consistency
**Mitigation**:
- Clear data ownership per service
- Use event sourcing for cross-service data sync
- Implement eventual consistency patterns
- Use distributed transactions only when necessary

### Challenge 3: Distributed Tracing
**Mitigation**:
- Implement AWS X-Ray
- Use correlation IDs across services
- Centralized logging (CloudWatch)

### Challenge 4: Service Discovery
**Mitigation**:
- Use ECS Service Discovery
- Or API Gateway for external access
- Environment variables for service URLs

### Challenge 5: Deployment Complexity
**Mitigation**:
- Use Infrastructure as Code (Terraform/CloudFormation)
- CI/CD pipelines per service
- Automated testing
- Staged rollouts

---

## Next Steps

1. **Review and Approve**: Review this plan with the team
2. **Create Service Stubs**: Create basic FastAPI apps for each service
3. **Extract Components**: Move code from monolith to services
4. **Setup Infrastructure**: Create ECR repos, ECS cluster, ALBs
5. **Deploy Services**: Deploy each service to ECS
6. **Integration Testing**: Test service-to-service communication
7. **Load Testing**: Test under load
8. **Migration**: Follow strangler fig pattern
9. **Monitor**: Set up monitoring and alerts
10. **Documentation**: Update API documentation

---

## Conclusion

This 4-microservice architecture provides:
- **Clear separation of concerns**
- **Independent scalability**
- **Improved maintainability**
- **Better resource utilization**
- **Faster development cycles**

The architecture balances:
- **Granularity** (not too many services)
- **Cohesion** (related functionality together)
- **Coupling** (minimal dependencies)
- **Practicality** (manageable complexity)

Each microservice has a clear purpose, well-defined boundaries, and can be developed, deployed, and scaled independently.

