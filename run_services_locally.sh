#!/bin/bash

# Local Service Runner for Testing Recurring Issue Detection
# This script runs the microservices locally to test code changes without Docker rebuild

set -e

echo "=================================================="
echo "LOCAL SERVICE RUNNER - Recurring Issue Test"
echo "=================================================="
echo ""

# Load environment variables from .env files
echo "Loading environment variables from .env files..."

# Function to load .env file
load_env() {
    local env_file=$1
    if [ -f "$env_file" ]; then
        export $(grep -v '^#' "$env_file" | xargs)
        echo "  ✓ Loaded: $env_file"
    fi
}

# Load common env vars from decision-simulation (has all the keys)
load_env "services/decision-simulation/.env"

echo ""

# Set environment variables (override if needed)
export AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_DYNAMODB_TABLE_NAME="${AWS_DYNAMODB_TABLE_NAME:-aam_requests}"
export RAG_ENABLED="${RAG_ENABLED:-false}"

# Service URLs for local running
export DECISION_SIMULATION_URL="http://localhost:8003"
export AI_PROCESSING_URL="http://localhost:8002"
export REQUEST_MANAGEMENT_URL="http://localhost:8001"
export EXECUTION_URL="http://localhost:8004"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to kill all background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    jobs -p | xargs -r kill 2>/dev/null || true
    wait 2>/dev/null || true
    echo -e "${GREEN}Services stopped${NC}"
}
trap cleanup EXIT INT TERM

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}⚠️  ERROR: GEMINI_API_KEY not found!${NC}"
    echo "   Please check services/decision-simulation/.env file"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables loaded${NC}"
echo "  • GEMINI_API_KEY: ${GEMINI_API_KEY:0:20}..."
echo "  • AWS_REGION: $AWS_REGION"
echo "  • AWS_DYNAMODB_TABLE: $AWS_DYNAMODB_TABLE_NAME"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}Starting services locally...${NC}"
echo ""

# Start Decision Simulation Service (Port 8003)
echo -e "${YELLOW}[1/4]${NC} Starting Decision Simulation Service on port 8003..."
cd services/decision-simulation
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload > ../../logs/decision-simulation-local.log 2>&1 &
DECISION_PID=$!
cd ../..
echo "      PID: $DECISION_PID"

sleep 2

# Start AI Processing Service (Port 8002)
echo -e "${YELLOW}[2/4]${NC} Starting AI Processing Service on port 8002..."
cd services/ai-processing
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload > ../../logs/ai-processing-local.log 2>&1 &
AI_PID=$!
cd ../..
echo "      PID: $AI_PID"

sleep 2

# Start Execution Service (Port 8004)
echo -e "${YELLOW}[3/4]${NC} Starting Execution Service on port 8004..."
cd services/execution
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload > ../../logs/execution-local.log 2>&1 &
EXEC_PID=$!
cd ../..
echo "      PID: $EXEC_PID"

sleep 2

# Start Request Management Service (Port 8001)
echo -e "${YELLOW}[4/4]${NC} Starting Request Management Service on port 8001..."
cd services/request-management
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > ../../logs/request-management-local.log 2>&1 &
REQ_PID=$!
cd ../..
echo "      PID: $REQ_PID"

sleep 3

echo ""
echo "=================================================="
echo -e "${GREEN}✓ All services started!${NC}"
echo "=================================================="
echo ""
echo "Service URLs:"
echo "  • Request Management:    http://localhost:8001"
echo "  • AI Processing:         http://localhost:8002"
echo "  • Decision Simulation:   http://localhost:8003"
echo "  • Execution:             http://localhost:8004"
echo ""
echo "Logs location:"
echo "  • logs/decision-simulation-local.log"
echo "  • logs/ai-processing-local.log"
echo "  • logs/execution-local.log"
echo "  • logs/request-management-local.log"
echo ""
echo "To test recurring issue detection:"
echo "  python3 test_recurring_issue.py"
echo ""
echo "To view logs in real-time:"
echo "  tail -f logs/*.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for all background processes
wait
