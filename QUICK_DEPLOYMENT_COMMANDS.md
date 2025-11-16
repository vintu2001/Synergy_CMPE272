# Quick Deployment Commands Reference

## Railway Deployment

### Create New Service
1. Railway Dashboard → New Project → Deploy from GitHub
2. Select repo: `Synergy_CMPE272`
3. Set Root Directory: `services/<service-name>`
4. Add environment variables
5. Deploy

### Service URLs (after deployment)
- Request Management: `https://request-management-production.up.railway.app`
- AI Processing: `https://ai-processing-production.up.railway.app`
- Execution: `https://execution-production.up.railway.app`

### Update Environment Variables
- Railway Dashboard → Service → Settings → Variables
- Add/Update variables
- Service auto-redeploys

### View Logs
- Railway Dashboard → Service → Logs tab

---

## EC2 Deployment

### Initial Setup
```bash
# SSH into EC2
ssh -i key.pem ubuntu@<ec2-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
newgrp docker

# Clone repo
git clone https://github.com/<username>/Synergy_CMPE272.git
cd Synergy_CMPE272
```

### Setup Environment
```bash
# Create .env file
cd infrastructure/ec2
nano .env
# Add: GEMINI_API_KEY, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.
```

### Initialize ChromaDB
```bash
cd ../../services/decision-simulation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/kb/ingest_documents.py
```

### Deploy Service
```bash
cd ../../infrastructure/ec2
docker compose up -d --build
```

### Check Status
```bash
# Check if running
docker compose ps

# View logs
docker compose logs -f decision-simulation

# Test health
curl http://localhost:8003/health
```

### Update Service
```bash
git pull
docker compose up -d --build
```

### Restart Service
```bash
docker compose restart decision-simulation
```

---

## Testing Commands

### Health Checks
```bash
# Request Management
curl https://request-management-production.up.railway.app/health

# AI Processing
curl https://ai-processing-production.up.railway.app/health

# Decision & Simulation
curl http://<ec2-ip>:8003/health

# Execution
curl https://execution-production.up.railway.app/health
```

### Submit Request
```bash
curl -X POST https://request-management-production.up.railway.app/api/v1/submit-request \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "RES_Building123_1001",
    "message_text": "My AC is broken"
  }'
```

### Classify Message
```bash
curl -X POST https://request-management-production.up.railway.app/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "RES_Building123_1001",
    "message_text": "AC is broken"
  }'
```

---

## Troubleshooting

### EC2: Service Not Starting
```bash
# Check logs
docker compose logs decision-simulation

# Check container status
docker compose ps

# Restart
docker compose restart decision-simulation
```

### EC2: ChromaDB Issues
```bash
# Check if data exists
docker exec -it decision-simulation-service ls -la /app/vector_stores/chroma_db

# Re-ingest
cd services/decision-simulation
source venv/bin/activate
python app/kb/ingest_documents.py
docker compose restart decision-simulation
```

### Railway: Service Not Responding
- Check Railway Dashboard → Service → Logs
- Verify environment variables are set
- Check deployment status

### Service-to-Service Communication
- Verify URLs in environment variables
- Test connectivity: `curl <service-url>/health`
- Check Railway service URLs (may change)

---

## Environment Variables Reference

### Request Management Service
```
PORT=8001
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_DYNAMODB_TABLE_NAME=aam_requests
AWS_SQS_QUEUE_URL=<url>
AI_PROCESSING_SERVICE_URL=<railway-url>
DECISION_SIMULATION_SERVICE_URL=http://<ec2-ip>:8003
EXECUTION_SERVICE_URL=<railway-url>
ADMIN_API_KEY=<random-key>
```

### AI Processing Service
```
PORT=8002
GEMINI_API_KEY=<key>
AWS_REGION=us-west-2
```

### Decision & Simulation Service (EC2)
```
PORT=8003
GEMINI_API_KEY=<key>
RAG_ENABLED=true
VECTOR_STORE_PATH=/app/vector_stores/chroma_db
VECTOR_STORE_COLLECTION=apartment_kb
EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
AWS_REGION=us-west-2
REQUEST_MANAGEMENT_SERVICE_URL=<railway-url>
ADMIN_API_KEY=<same-as-request-management>
```

### Execution Service
```
PORT=8004
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_SQS_QUEUE_URL=<url>
```

