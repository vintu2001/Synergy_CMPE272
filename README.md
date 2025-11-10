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

## Project Structure

```
Synergy_CMPE272/
├── backend/                 # FastAPI microservices
│   ├── app/                 # Application code
│   │   ├── agents/          # Agent implementations
│   │   ├── services/        # Service layer
│   │   ├── models/          # Data models and schemas
│   │   └── utils/           # Utility functions
│   ├── tests/               # Test suite
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Docker configuration
│
├── frontend/                # Frontend application (TBD)
│   ├── src/
│   └── package.json
│
├── ml/                      # Machine learning components
│   ├── scripts/             # Python scripts
│   ├── notebooks/           # Jupyter notebooks
│   ├── data/                # Data storage
│   └── models/              # Trained models
│
├── infrastructure/          # Infrastructure as code
│   ├── aws/                 # AWS resources
│   └── docker/              # Docker compose
│
└── docs/                    # Project Documentation
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
   # Edit .env with your AWS credentials and configuration
   ```

4. **Run the backend server**
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

- **[Team Onboarding Guide](docs/TEAM_ONBOARDING.md)** - Complete setup instructions for team members
- **[AWS Resources Setup](docs/AWS_RESOURCES_SETUP.md)** - Step-by-step AWS resource creation (SQS, DynamoDB, IAM)
- **[Task 1 Setup Guide](infrastructure/TASK1_SETUP_GUIDE.md)** - Infrastructure setup checklist
- **[Project Architecture](docs/architecture.md)** - System architecture overview
- **[Contributing Guidelines](CONTRIBUTING.md)** - Git workflow and development practices

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)


