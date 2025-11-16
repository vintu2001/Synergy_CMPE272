# Microservices Directory

This directory contains the 4 microservices for the Agentic Apartment Manager system.

## Services

### 1. Request Management Service
- **Location:** `request-management/`
- **Port:** 8001
- **Deployment:** Railway.app
- **Responsibilities:**
  - Request lifecycle management
  - CRUD operations
  - Resident and Admin APIs
  - Orchestrates other services

### 2. AI Processing Service
- **Location:** `ai-processing/`
- **Port:** 8002
- **Deployment:** Railway.app
- **Responsibilities:**
  - Message classification
  - Risk prediction
  - ML model serving

### 3. Decision & Simulation Service
- **Location:** `decision-simulation/`
- **Port:** 8003
- **Deployment:** AWS EC2
- **Responsibilities:**
  - Resolution option simulation
  - Decision making
  - RAG retrieval
  - Knowledge base management

### 4. Execution Service
- **Location:** `execution/`
- **Port:** 8004
- **Deployment:** Railway.app
- **Responsibilities:**
  - Action execution
  - External system integrations

## Quick Start

See [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## Migration

See [MIGRATION_HELPER.md](../MIGRATION_HELPER.md) for help moving code from monolith to microservices.

