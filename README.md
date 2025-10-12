# Agentic Apartment Manager

## Group Information
**Group Name:**

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

