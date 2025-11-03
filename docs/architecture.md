# System Architecture

## Overview
The Agentic Apartment Manager is built as a distributed, event-driven system on AWS Cloud, where containerized FastAPI microservices communicate asynchronously to process resident messages and management events in real time.

## Architecture Components

### 1. Frontend Layer
- **Technology**: React/Vue/Angular (TBD)
- **Components**:
  - Resident submission page
  - Resident dashboard
  - Admin read-only dashboard

### 2. Backend Layer
- **Technology**: FastAPI microservices
- **Components**:
  - Message Intake Service (SQS + Lambda)
  - Classification Agent (LLM-based)
  - Risk Prediction Agent (XGBoost/ARIMA)
  - Simulation Agent (SimPy)
  - Decision Agent (Policy-based)
  - Execution Layer (Simulated APIs)

### 3. Data Layer
- **DynamoDB**: Event database for requests
- **S3**: Model artifacts and storage

### 4. Infrastructure Layer
- **AWS Services**: S3, SQS, Lambda, DynamoDB
- **Containerization**: Docker
- **Monitoring**: Instana, CloudWatch

### 5. Governance Layer
- **IBM Watsonx.governance**: Decision explainability and auditability

## Data Flow

1. Resident submits message via frontend
2. Message Intake normalizes and queues message (SQS)
3. Lambda triggers Classification Agent
4. Classification Agent categorizes message
5. Risk Prediction Agent enriches with risk score
6. Simulation Agent generates resolution options
7. Decision Agent selects optimal action
8. Execution Layer executes action
9. Results logged to DynamoDB and Watsonx.governance
10. Frontend polls for status updates

## Agent Pipeline

```
Message Intake → Classification → Risk Prediction → Simulation → Decision → Execution
```

