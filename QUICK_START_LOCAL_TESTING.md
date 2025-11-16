# Quick Start: Local Testing
## Fast Setup for End-to-End UI Testing

### 1. Initialize ChromaDB (One Time)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python kb/ingest_documents.py
cp -r vector_stores/chroma_db ../services/decision-simulation/vector_stores/
```

### 2. Create Environment File

```bash
cd infrastructure/docker
cat > .env << EOF
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DYNAMODB_TABLE_NAME=aam_requests
AWS_SQS_QUEUE_URL=your-sqs-url
GEMINI_API_KEY=your-gemini-key
ADMIN_API_KEY=test-admin-key
EOF
```

### 3. Start Services

```bash
docker-compose -f docker-compose.microservices.yml up -d
```

### 4. Verify Services

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### 5. Update Frontend

```bash
cd frontend
echo "VITE_API_BASE_URL=http://localhost:8001" > .env.local
npm run dev
```

### 6. Test from UI

1. Open `http://localhost:5173`
2. Submit a request: "My AC is broken"
3. Verify options appear
4. Select an option
5. Check request history

### 7. View Logs

```bash
cd infrastructure/docker
docker-compose -f docker-compose.microservices.yml logs -f
```

### Stop Services

```bash
docker-compose -f docker-compose.microservices.yml down
```

---

**For detailed instructions, see [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)**

