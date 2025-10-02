# PROJECT IDEAS

## Agentic Apartment Manager
### Overview
The Agentic Apartment Manager (AAM) is an autonomous, AI-driven system designed to
proactively handle apartment management issues reported by residents through messages. 
Unlike traditional ticketing systems, AAM anticipates, forecasts, and
autonomously executes actions to resolve issues such as maintenance, package theft, billing,
security, and amenity management.

### Problem
Current property management tools are reactive, relying on human intervention to classify,
assign, and resolve issues. This results in inefficiencies, delays, and dissatisfied residents.

### Solution
AAM provides a multi-agent pipeline that:
- Ingests resident messages in natural language.
- Classifies the issue (maintenance, billing, delivery, etc.).
- Forecasts likelihood of repeat or related problems.
- Simulates multiple resolution options.
- Decides on the best action using policy-based scoring.
- Executes the action autonomously (e.g., dispatch work order, reroute delivery, send
notification).
- Logs explanations with IBM Watsonx.governance.
- Monitors system health and actions via Instana and AWS CloudWatch.
