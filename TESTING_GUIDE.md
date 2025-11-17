# Testing Guide

## Prerequisites

### Python Environment Setup (Recommended)

**Using Virtual Environment (Recommended):**

# Create virtual environment
python -m venv venv

# Windows CMD:
.\venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate

### Install Test Dependencies

Each service has its own test dependencies. Install them before running tests:

# Install dependencies for all services
cd services\request-management
pip install -r requirements.txt
pip install -r requirements-test.txt

cd ..\ai-processing
pip install -r requirements.txt
pip install -r requirements-test.txt

cd ..\decision-simulation
pip install -r requirements.txt
pip install -r requirements-test.txt

cd ..\execution
pip install -r requirements.txt
pip install -r requirements-test.txt

cd ..\..

**Or install test-only dependencies (minimal, faster):**

# From project root
pip install pytest pytest-asyncio pytest-mock pytest-cov httpx fastapi pydantic boto3 python-dotenv google-generativeai

## Quick Test Commands

## Run ALL Tests (Backend + Frontend)

# Python (Recommended - cross-platform)
python run_tests.py

This will:
- Automatically install test dependencies for each service
- Run pytest for all 4 backend services
- Show pass/fail summary with test counts
- Exit with code 0 (success) or 1 (failures)

## Backend Tests (Individual Services)

**Important:** Install service dependencies first (see Prerequisites above)

### Request Management Service

cd services\request-management
pip install -r requirements-test.txt  # If not already installed
pytest -v

### AI Processing Service

cd services\ai-processing
pip install -r requirements-test.txt  # If not already installed
pytest -v

### Decision Simulation Service

cd services\decision-simulation
pip install -r requirements-test.txt  # If not already installed
pytest -v

### Execution Service

cd services\execution
pip install -r requirements-test.txt  # If not already installed
pytest -v

## What Gets Tested

### Request Management (13 tests)
- CloudWatch logger functionality (Decimal conversion, log streams, event structure)
- Request orchestration (option selection, validation)

### AI Processing (9 tests)
- Rule-based classification (escalation, questions, deliveries, amenities)
- Gemini AI classification integration
- Urgency detection
- Risk prediction

### Decision Simulation (3 tests)
- Decision agent placeholder tests
- RAG retriever placeholder tests
- Simulation placeholder tests

### Execution (2 tests)
- Work order ID format validation
- Alert ID format validation

## Test Output

Successful run shows:
```
==================================================
Test Results
==================================================

Request Management
--------------------------------------------------
13 passed

AI Processing  
--------------------------------------------------
9 passed

Decision Simulation
--------------------------------------------------
3 passed

Execution
--------------------------------------------------
2 passed

==================================================
Passed: 4
  ✓ Request Management
  ✓ AI Processing
  ✓ Decision Simulation
  ✓ Execution
==================================================
```

## Specific Test Files

### Run single test file
```powershell
# Backend
cd services\request-management
pytest tests/test_orchestrator.py -v

# Frontend
cd frontend
npm test -- tests/ResidentSubmission.test.jsx
```

### Run specific test function
```powershell
# Backend
pytest tests/test_orchestrator.py::test_submit_request_success -v

# Frontend
npm test -- -t "renders form correctly"
```

## Coverage Reports

### Backend coverage
```powershell
cd services\request-management
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Frontend coverage
```powershell
cd frontend
npm run test:coverage
# Open coverage/index.html in browser
```

## Watch Mode (Auto-rerun on changes)

### Frontend watch mode
```powershell
cd frontend
npm test -- --watch
```
## Example Usage

### Run only async tests
```powershell
pytest -v -m asyncio
```

### Run only unit tests (exclude integration)
```powershell
pytest -v -m "not integration"
```

### Run tests and show print output
```powershell
pytest -v -s
```
