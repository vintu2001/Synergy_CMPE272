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

