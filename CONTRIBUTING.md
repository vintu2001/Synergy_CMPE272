# Contributing Guidelines

## Git Workflow

### Branch Strategy
- **main**: Production-ready code (protected branch)
- **develop**: Integration branch for completed features
- **feature/**: Feature branches (e.g., `feature/classification-agent`)
- **fix/**: Bug fix branches (e.g., `fix/message-intake-bug`)

### Branch Protection
The `main` branch requires:
- Pull request reviews (at least 1 approval)
- Passing status checks (if configured)
- No force pushes

### Commit Guidelines
- Use clear, descriptive commit messages
- Reference ticket numbers when applicable (e.g., "Ticket 5: Implement classification agent")
- Keep commits atomic and focused

### Pull Request Process
1. Create a feature branch from `main`
2. Implement your changes
3. Test locally
4. Push to remote and create a Pull Request
5. Request review from team members
6. Address feedback and update PR
7. Once approved, merge to `main`

## Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install  # After framework is selected
```

### ML Environment Setup
```bash
cd ml
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Code Style
- Python: Follow PEP 8 style guide
- Use type hints where applicable
- Add docstrings to functions and classes
- Keep functions small and focused

## Testing
- Write tests for new features
- Run tests before submitting PR
- Aim for meaningful test coverage

## Team Responsibilities

### Member 1 (Lead Developer)
- Backend API development
- Agent implementations
- Pipeline orchestration

### Member 2 (ML & Simulation)
- ML model training
- Synthetic data generation
- Simulation logic

### Member 3 (Frontend)
- UI/UX development
- Frontend-backend integration
- User interface design

### Member 4 (Frontend & DevOps)
- AWS infrastructure
- Deployment configuration
- Monitoring setup
- CI/CD pipelines

## Ticket Assignment
Each team member should:
1. Update ticket status when starting work
2. Create a feature branch named after the ticket
3. Reference ticket number in commit messages
4. Update documentation as needed

## Communication
- Use GitHub Issues for task tracking
- Use Pull Request comments for code review discussions
- Keep team updated on progress in shared channels

