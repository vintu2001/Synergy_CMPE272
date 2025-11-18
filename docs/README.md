# Documentation Index

This directory contains comprehensive documentation for the Agentic Apartment Manager system.

## 📚 Documentation Structure

### Core Documentation
- **[README.md](../README.md)** - Project overview, quick start, and basic information
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Complete system architecture and technical design
- **[DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Deployment instructions for various environments
- **[TESTING_GUIDE.md](../TESTING_GUIDE.md)** - Testing strategies and test execution

### Diagrams & Visuals
- **[LUCIDCHART_GUIDE.md](./LUCIDCHART_GUIDE.md)** - Instructions for creating architecture diagrams
- **Mermaid Diagrams** - Embedded in README.md and ARCHITECTURE.md (auto-rendered on GitHub)

### API Documentation
- **API Reference** - OpenAPI/Swagger documentation (available at `/docs` endpoint when services run)
  - Request Management: http://localhost:8001/docs
  - AI Processing: http://localhost:8002/docs
  - Decision & Simulation: http://localhost:8003/docs
  - Execution: http://localhost:8004/docs

### Technical Specifications

#### System Design
- [System Architecture](../ARCHITECTURE.md#architecture-overview) - High-level system design
- [Data Flow](../ARCHITECTURE.md#data-flow) - Request processing pipeline
- [Technology Stack](../ARCHITECTURE.md#technology-stack) - Technologies and frameworks
- [Deployment Architecture](../ARCHITECTURE.md#deployment-architecture) - Infrastructure setup

#### Component Documentation
- [Request Management Service](../ARCHITECTURE.md#1-request-management-service-port-8001) - API gateway and orchestration
- [AI Processing Service](../ARCHITECTURE.md#2-ai-processing-service-port-8002) - Classification and risk prediction
- [Decision & Simulation Service](../ARCHITECTURE.md#3-decision--simulation-service-port-8003) - RAG and multi-agent AI
- [Execution Service](../ARCHITECTURE.md#4-execution-service-port-8004) - Action execution

#### AI/ML Documentation
- [RAG System](../ARCHITECTURE.md#rag-knowledge-base-details) - Retrieval-Augmented Generation setup
- [Multi-Agent Coordination](../ARCHITECTURE.md#multi-agent-coordination) - Agent communication patterns
- [Knowledge Base](../services/decision-simulation/app/kb/README.md) - Document structure and categories

### Deployment Guides

#### Local Development
- [Docker Compose Setup](../DEPLOYMENT_GUIDE.md) - Running services locally
- [Environment Configuration](../DEPLOYMENT_GUIDE.md) - Setting up .env files
- [Service Dependencies](../DEPLOYMENT_GUIDE.md) - Required external services

#### Cloud Deployment
- [AWS EC2 Deployment](../DEPLOYMENT_GUIDE.md) - EC2 instance setup
- [Production Configuration](../DEPLOYMENT_GUIDE.md) - Production best practices
- [Scaling Strategies](../ARCHITECTURE.md#security--scalability) - Horizontal and vertical scaling

### Testing Documentation
- [Test Execution](../TESTING_GUIDE.md) - Running unit and integration tests
- [Recurring Issue Test](../test_recurring_issue.py) - Specialized recurring detection test
- [Test Coverage](../TESTING_GUIDE.md) - Coverage reports and quality metrics

### Operations & Monitoring
- [Logging Strategy](../ARCHITECTURE.md#monitoring-alerts) - CloudWatch integration
- [Error Handling](../ARCHITECTURE.md#error-handling--resilience) - Failure scenarios and recovery
- [Health Checks](../infrastructure/docker/docker-compose.microservices.yml) - Service health monitoring

## 🚀 Quick Links

### Getting Started
1. [Prerequisites](../README.md#prerequisites)
2. [Installation](../README.md#getting-started)
3. [Running Services](../DEPLOYMENT_GUIDE.md)
4. [Testing](../TESTING_GUIDE.md)

### Development
- [Project Structure](../README.md#project-structure)
- [Service Architecture](../ARCHITECTURE.md#system-components)
- [API Endpoints](http://localhost:8001/docs) (when running)

### Deployment
- [Local Deployment](../DEPLOYMENT_GUIDE.md)
- [EC2 Deployment](./LUCIDCHART_GUIDE.md) (EC2 setup instructions)
- [Environment Variables](../DEPLOYMENT_GUIDE.md)

### Understanding the System
- [Data Flow Diagram](../ARCHITECTURE.md#data-flow)
- [RAG Retrieval Process](../ARCHITECTURE.md#rag-retrieval-process)
- [Agent Tools](../ARCHITECTURE.md#tools-available-to-agents)

## 📊 Visual Documentation

### Architecture Diagrams
- **Mermaid Diagram** (in README.md) - Interactive, GitHub-native diagram
- **ASCII Diagram** (in ARCHITECTURE.md) - Text-based architecture view
- **Lucidchart** (guide available) - Professional diagram creation

### Data Flow Diagrams
- [Complete Request Flow](../ARCHITECTURE.md#complete-request-processing-flow) - Step-by-step processing
- [Agent Communication](../ARCHITECTURE.md#agent-communication-flow) - Multi-agent coordination
- [RAG Pipeline](../ARCHITECTURE.md#rag-retrieval-process) - Document retrieval flow

## 🔧 Technical References

### Service APIs
| Service | Port | Swagger UI | Purpose |
|---------|------|------------|---------|
| Request Management | 8001 | http://localhost:8001/docs | API Gateway |
| AI Processing | 8002 | http://localhost:8002/docs | Classification |
| Decision & Simulation | 8003 | http://localhost:8003/docs | RAG & Agents |
| Execution | 8004 | http://localhost:8004/docs | Work Orders |

### External Dependencies
- **Google Gemini API**: LLM for text generation
- **AWS DynamoDB**: Request storage
- **AWS SQS**: Message queue
- **AWS CloudWatch**: Logging
- **ChromaDB**: Vector database

### Performance Metrics
- RAG Retrieval: <100ms
- Classification: <2s
- Simulation: 10-25s
- Decision: <500ms
- End-to-End: 15-35s

## 📖 Additional Resources

### Code Documentation
- Inline docstrings in Python modules
- Type hints for all functions
- Pydantic schemas for data validation

### Community & Support
- GitHub Issues: Bug reports and feature requests
- Team Contacts: See [README.md](../README.md#team-members)

### Future Enhancements
- [Planned Features](../ARCHITECTURE.md#planned-features)
- [Architectural Improvements](../ARCHITECTURE.md#architectural-improvements)

---

## Document Maintenance

**Last Updated:** November 17, 2025  
**Maintained By:** Synergy Team  
**Review Frequency:** Monthly or on major updates

### Contributing to Documentation
When adding new features or making significant changes:
1. Update relevant documentation files
2. Update this index if new docs are added
3. Ensure diagrams reflect current architecture
4. Update API documentation (Swagger/OpenAPI)
5. Add to version control with descriptive commit message

---

**Need help?** Check the [README](../README.md) or create an issue on GitHub.
