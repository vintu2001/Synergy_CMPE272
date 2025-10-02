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

## Project Proposal: Agentic Cloud Cost Optimizer

### Abstract
This proposal outlines Project Aegis, a smart AI assistant built to automatically fix security problems and save money in a company's cloud environment. The project tackles the major challenges of accidental security mistakes and wasted spending that come with using large-scale cloud services. Aegis works by watching a live feed of all cloud activity, using an AI brain to make decisions, and automatically fixing issues on its own. This solution is a direct example of the 

Agentic Era of software, where programs don't just report problems—they actively solve them.

### Problem Statement
Using cloud platforms like AWS is complex and leads to several key problems that manual oversight cannot solve effectively

Security Mistakes: It's easy for users to accidentally leave a digital "door" unlocked in the cloud, such as making data public by mistake. This creates serious security risks.

Wasted Money: Companies often pay for cloud services they aren't actually using, like servers that are left running for no reason. This is like leaving the lights on in an empty room and results in significant hidden costs.

Slow Human Fixes: Currently, most tools just send an alert when something goes wrong. A person then has to see the alert, figure out the problem, and fix it by hand. This process is too slow, and a lot of damage can happen in the meantime.

### Proposed Solution
We propose building Project Aegis, an autonomous agent that works 24/7 to enforce security and cost-saving rules in an AWS account. Aegis is an 

agentic system, meaning it is a smart program that can understand what's happening, make a decision, and take action all by itself, without needing a person to tell it what to do.

### Technical Approach
The optimizer operates in a continuous three-step loop:

1.⁠ ⁠Perceive (It Watches)
Aegis watches a live feed of every action happening in the cloud, provided by a service called AWS CloudTrail. This feed is sent through a high-speed messaging system, Apache Kafka, giving the agent a real-time view of the environment.

2.⁠ ⁠Decide (It Thinks)
When Aegis sees an action, its AI brain (a Large Language Model) checks a rulebook written in plain English. It thinks, "Does this action break one of our rules?" and then decides on the correct way to fix it. This thinking process is organized by a framework called LangChain.

3.⁠ ⁠Act (It Acts)
If a rule is broken, Aegis does not wait for a person. It instantly uses its tools (the AWS SDK) to fix the problem. This could mean locking a digital door that was left open or shutting down a server that's wasting money.
