# Agentic Apartment Manager - System Architecture

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Deployment Architecture](#deployment-architecture)
6. [Security & Scalability](#security--scalability)

---

## Architecture Overview

The Agentic Apartment Manager (AAM) is a **microservices-based, event-driven system** that autonomously manages apartment operations using AI agents, RAG (Retrieval-Augmented Generation), and predictive analytics.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   Resident   │  │    Admin     │  │   Mobile     │                  │
│  │   Portal     │  │  Dashboard   │  │     App      │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                  │                           │
│         └─────────────────┴──────────────────┘                           │
│                           │                                              │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │           Request Management Service (Port 8001)                  │  │
│  │  • Message Ingestion  • Request Orchestration  • Response Agg.   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  AI PROCESSING   │ │   DECISION &     │ │   EXECUTION      │
│   SERVICE        │ │   SIMULATION     │ │   SERVICE        │
│   (Port 8002)    │ │   (Port 8003)    │ │   (Port 8004)    │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ • Classification │ │ • RAG Retrieval  │ │ • Work Orders    │
│ • Intent Det.    │ │ • Simulation     │ │ • Notifications  │
│ • Risk Pred.     │ │ • Decision       │ │ • Vendor Mgmt    │
│ • Gemini LLM     │ │ • Multi-Agent    │ │ • SQS Consumer   │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         │         ┌──────────┴──────────┐         │
         │         │                     │         │
         ▼         ▼                     ▼         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   DynamoDB   │  │   ChromaDB   │  │   AWS SQS    │      │
│  │   Requests   │  │   Vector DB  │  │   Queue      │      │
│  │   Decisions  │  │   35+ Docs   │  │   Messages   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  MONITORING & LOGGING                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CloudWatch  │  │   Grafana    │  │   Instana    │      │
│  │   Logs       │  │  Dashboards  │  │   APM        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. Request Management Service (Port 8001)
**Role:** API Gateway and request orchestration hub

**Responsibilities:**
- Receives resident messages via REST API
- Orchestrates communication between microservices
- Aggregates responses from AI, Decision, and Execution services
- Manages request lifecycle in DynamoDB
- Provides admin APIs for dashboard

**Key Files:**
- `app/services/orchestrator.py` - Request flow coordination
- `app/api/routes.py` - REST API endpoints
- `app/models/schemas.py` - Pydantic data models

**Technology:**
- FastAPI (async framework)
- DynamoDB (request storage)
- CloudWatch (logging)

---

### 2. AI Processing Service (Port 8002)
**Role:** Natural language understanding and risk assessment

**Responsibilities:**
- **Message Classification**: Categorize messages (Maintenance, Noise, Parking, etc.)
- **Intent Detection**: Identify user intent (solve_problem, answer_question, escalate)
- **Urgency Assessment**: Classify as Low/Medium/High/Critical
- **Risk Prediction**: XGBoost model for escalation probability

**Agents:**
- `ClassificationAgent` - Rule-based + Gemini fallback classifier
- `RiskPredictionAgent` - ML-based risk scorer

**Key Files:**
- `app/agents/classifier.py` - Classification logic
- `app/ml_models/risk_predictor.py` - Risk prediction model
- `app/api/routes.py` - `/classify` and `/predict-risk` endpoints

**Technology:**
- Google Gemini API (LLM)
- XGBoost (ML model)
- FastAPI

---

### 3. Decision & Simulation Service (Port 8003)
**Role:** Multi-agent decision making with RAG-enhanced reasoning

**Responsibilities:**
- **RAG Retrieval**: Fetch relevant policies, SOPs, and vendor info from ChromaDB
- **Simulation**: Generate 3 resolution options using LLM + real-time data
- **Decision Making**: Score options using policy rules and select optimal solution
- **Learning**: Analyze historical patterns to improve recommendations

**Agents:**
- `SimulationAgent` - Generates resolution options with tool execution
- `DecisionAgent` - Scores and selects optimal option
- `LearningEngine` - Analyzes historical data for insights
- `ReasoningEngine` - Determines complexity for single vs multi-step reasoning

**RAG System:**
- **Vector Store**: ChromaDB with 466 documents
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Document Types**: Policies (6), SOPs (8), Vendor Catalogs (10), SLAs (11)
- **Retrieval Threshold**: 0.5 similarity (configurable)

**Tools Available to Agents:**
- `check_technician_availability` - Real-time availability data
- `get_dynamic_pricing` - Cost estimation based on urgency
- `check_recurring_issues` - Pattern detection from history
- `get_past_solutions` - Success rate of previous resolutions
- `check_inventory` - Parts/supplies availability
- `get_weather_impact` - Weather-based urgency adjustment
- `get_optimal_schedule` - Time optimization

**Key Files:**
- `app/agents/simulation_agent.py` - Option generation
- `app/agents/decision_agent.py` - Decision scoring
- `app/rag/retriever.py` - RAG retrieval logic
- `app/agents/tools.py` - Agent tool implementations

**Technology:**
- Google Gemini API (LLM for simulation)
- ChromaDB (vector database)
- SentenceTransformers (embeddings)
- CrewAI concepts (multi-agent coordination)
- SimPy concepts (discrete event simulation)

---

### 4. Execution Service (Port 8004)
**Role:** Action execution and notification delivery

**Responsibilities:**
- Generate work orders for maintenance tasks
- Send notifications to residents (email, SMS, push)
- Coordinate with vendor systems
- Process background jobs via SQS queue
- Track execution status and completion

**Key Files:**
- `app/services/work_order_service.py` - Work order generation
- `app/services/notification_service.py` - Multi-channel notifications
- `app/api/routes.py` - Execution endpoints

**Technology:**
- AWS SQS (message queue)
- FastAPI
- Twilio/SendGrid (future notifications)

---

## Data Flow

### Complete Request Processing Flow

```
1. INGESTION
   Resident submits message → Request Management Service
   ↓
   Creates request in DynamoDB with status="pending"

2. CLASSIFICATION
   Request Mgmt → AI Processing Service (/classify)
   ↓
   Returns: {category, urgency, intent, confidence}

3. RISK ASSESSMENT
   Request Mgmt → AI Processing Service (/predict-risk)
   ↓
   Returns: {risk_score, escalation_probability}

4. SIMULATION
   Request Mgmt → Decision Service (/simulate)
   ↓
   • Retrieves 5 relevant docs from ChromaDB (RAG)
   • Executes 8 agent tools for context
   • Generates 3 resolution options using Gemini
   ↓
   Returns: {options: [{option_id, action, cost, time, reasoning}], is_recurring}

5. DECISION
   Request Mgmt → Decision Service (/decide)
   ↓
   • Retrieves 3 policy documents (RAG)
   • Scores each option against policies
   • Selects optimal option
   ↓
   Returns: {recommended_option_id, policy_scores, reasoning}

6. EXECUTION
   Request Mgmt → Execution Service (/execute)
   ↓
   • Generates work order
   • Sends notifications
   • Updates request status to "completed"
   ↓
   Returns: {work_order_id, notifications_sent}

7. RESPONSE
   Request Mgmt aggregates all responses
   ↓
   Returns complete response to frontend with full decision trail
```

---

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI | Async REST APIs |
| Language | Python 3.10+ | Primary language |
| LLM | Google Gemini 2.5 Flash | Text generation & reasoning |
| Vector DB | ChromaDB | RAG document storage |
| Embeddings | SentenceTransformers | Semantic search |
| ML Model | XGBoost | Risk prediction |
| Database | AWS DynamoDB | Request & decision storage |
| Queue | AWS SQS | Async job processing |
| Logging | AWS CloudWatch | Centralized logs |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | React 18 | UI components |
| Build Tool | Vite | Fast development |
| Styling | Tailwind CSS | Utility-first CSS |
| State | Context API | Global state |
| HTTP Client | Axios | API requests |

### Infrastructure
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker | Service isolation |
| Orchestration | Docker Compose | Local development |
| Cloud Platform | AWS | Production hosting |
| Monitoring | CloudWatch + Grafana | Metrics & dashboards |
| CI/CD | GitHub Actions (planned) | Automated deployments |

---

## Deployment Architecture

### Local Development (Docker Compose)
```yaml
Services:
  - request-management: 8001
  - ai-processing: 8002
  - decision-simulation: 8003
  - execution: 8004

Volumes:
  - chroma-data: Persistent ChromaDB storage
  - kb: Read-only knowledge base mount

Network:
  - synergy-microservices-network (bridge)

Health Checks:
  - All services monitored every 30s
  - 3 retries before marking unhealthy
  - 40s startup grace period
```

### Production (AWS EC2 - Planned)
```
EC2 Instances:
  - t3.small (2 vCPU, 2GB RAM) per service
  - Auto-scaling groups for demand handling
  - Application Load Balancer for traffic distribution

Storage:
  - DynamoDB: On-demand billing
  - S3: Document storage backup
  - EBS: ChromaDB persistence

Security:
  - VPC with private subnets
  - Security groups for port control
  - IAM roles for service authentication
  - Secrets Manager for API keys
```

---

## Security & Scalability

### Security Measures
1. **API Authentication**: Admin API key for protected endpoints
2. **Environment Variables**: Sensitive data in .env files (not in code)
3. **AWS IAM**: Fine-grained permissions for services
4. **CloudWatch Logs**: Encrypted log storage
5. **HTTPS**: SSL/TLS for production APIs (planned)
6. **Input Validation**: Pydantic schemas prevent injection attacks

### Scalability Features
1. **Horizontal Scaling**: Each service can scale independently
2. **Async Processing**: FastAPI async endpoints for high concurrency
3. **Message Queue**: SQS decouples execution for peak loads
4. **Caching**: ChromaDB metadata caching reduces latency
5. **Database Optimization**: DynamoDB partition keys for even distribution
6. **Stateless Services**: All services are stateless for easy replication

### Performance Metrics
- **RAG Retrieval**: <100ms for vector search
- **Classification**: <2s with Gemini API
- **Simulation**: 10-25s (depends on LLM response)
- **Decision**: <500ms (after RAG retrieval)
- **End-to-End**: 15-35s from message to complete response

---

## RAG Knowledge Base Details

### Document Categories
| Type | Count | Purpose | Examples |
|------|-------|---------|----------|
| Policies | 6 | Apartment rules | Maintenance, Noise, Parking |
| SOPs | 8 | Standard procedures | Emergency protocols |
| Vendor Catalogs | 10 | Service providers | HVAC, Plumbing, Electrical |
| SLAs | 11 | Service agreements | Response times, guarantees |

### RAG Retrieval Process
1. **Query Enhancement**: Expand abbreviations (AC → air conditioning)
2. **Embedding Generation**: Convert query to 384-dim vector
3. **Similarity Search**: ChromaDB cosine similarity
4. **Filtering**: Building-specific + document type filters
5. **Threshold**: Only return docs with score > 0.5
6. **Ranking**: Sort by relevance score

### RAG Configuration
```python
RAG_ENABLED=true
RAG_TOP_K=5                    # Simulation retrieves 5 docs
RAG_SIMILARITY_THRESHOLD=0.5   # Decision retrieves 3 high-precision docs
VECTOR_STORE_PATH=/app/vector_stores/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Multi-Agent Coordination

### Agent Communication Flow
```
SimulationAgent
  ├─→ Executes 8 tools concurrently
  ├─→ Queries RAG for context (5 docs)
  ├─→ Passes context to Gemini LLM
  └─→ Returns 3 options with citations

DecisionAgent
  ├─→ Queries RAG for policies (3 docs)
  ├─→ Scores each option against rules
  ├─→ Applies recurring issue boost (+15% for permanent solutions)
  └─→ Selects optimal option with reasoning

LearningEngine
  ├─→ Analyzes historical patterns
  ├─→ Calculates success rates
  └─→ Provides insights for future decisions

ReasoningEngine
  ├─→ Assesses complexity
  ├─→ Routes to single-step vs multi-step
  └─→ Determines reasoning depth needed
```

---

## Error Handling & Resilience

### Failure Scenarios
1. **LLM API Failure**: Fallback to rule-based classification
2. **RAG Unavailable**: Proceed with default policies
3. **Service Timeout**: Return partial response with degraded features
4. **DynamoDB Error**: Retry with exponential backoff
5. **SQS Queue Full**: Log error and alert admin

### Monitoring Alerts
- Service health check failures
- API latency > 5s
- Error rate > 5%
- CloudWatch log errors
- DynamoDB throttling

---

## Future Enhancements

### Planned Features
1. **Advanced ML**: ARIMA for time-series prediction
2. **Graph Database**: Neo4j for relationship tracking
3. **Real-time Updates**: WebSocket notifications
4. **Mobile App**: Native iOS/Android apps
5. **Voice Interface**: Alexa/Google Home integration
6. **Blockchain**: Immutable audit trail
7. **Kubernetes**: Container orchestration for scale

### Architectural Improvements
1. **Event Streaming**: Replace REST with Kafka/Kinesis
2. **API Gateway**: AWS API Gateway for centralized routing
3. **Service Mesh**: Istio for advanced traffic management
4. **Distributed Tracing**: OpenTelemetry for request tracking
5. **Feature Flags**: LaunchDarkly for gradual rollouts

---

## Glossary

- **RAG**: Retrieval-Augmented Generation - combines LLM with document retrieval
- **ChromaDB**: Open-source vector database for embeddings
- **DynamoDB**: AWS NoSQL database with millisecond latency
- **SQS**: Simple Queue Service - AWS message queue
- **Gemini**: Google's large language model API
- **FastAPI**: Modern Python web framework with async support
- **Pydantic**: Data validation using Python type annotations
- **Agent**: Autonomous software component that perceives, reasons, and acts
- **Multi-Agent System**: Coordinated agents working toward common goals

---

## References

- [System Design Document](./docs/SYSTEM_DESIGN.md)
- [API Documentation](./docs/API_REFERENCE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Testing Guide](./TESTING_GUIDE.md)

---

**Last Updated:** November 17, 2025  
**Version:** 1.0  
**Maintainers:** Synergy Team
