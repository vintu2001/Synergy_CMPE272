# Task 1 Setup Guide – Infrastructure Setup Checklist

This guide gets the **Agentic Apartment Manager (AAM)** running on your machine with the repo’s existing infrastructure pieces (backend, Docker, optional AWS). Do these in order.

> This document assumes the repo structure from GitHub:
>
> ```
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
└── docs/                    # Documentation
> ```

---

## 1. Objectives

- clone the project
- run the **backend (FastAPI)** locally or with Docker
- create and load a `.env`
- optionally hook it up to AWS (DynamoDB, SQS) using the separate AWS guide
- verify via `/docs` and `/health`

---

## 2. Prerequisites

Make sure you have:

- **Git**
- **Docker + Docker Compose** (for the simplest run)  
  - check: `docker --version` and `docker compose version`
- **Python 3.11** (only if you want to run backend without Docker)
- **Node.js 20+** (only if you want to run the React/Vite frontend)
- **AWS CLI** (optional, for creating AWS resources)

---

## 3. Clone the Repository

```bash
git clone https://github.com/vintu2001/Synergy_CMPE272.git
cd Synergy_CMPE272
