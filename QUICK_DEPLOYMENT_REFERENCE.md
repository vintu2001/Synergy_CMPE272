# Quick Deployment Reference
## Hybrid Railway + EC2 Deployment

Quick reference for deploying all 4 microservices.

---

## Prerequisites Checklist

- [ ] Railway.app account (https://railway.app)
- [ ] AWS account (free tier available)
- [ ] GitHub repository
- [ ] Gemini API key
- [ ] AWS credentials (Access Key ID, Secret Access Key)
- [ ] DynamoDB table created (`aam_requests`)
- [ ] SQS queue created (optional)

---

## Railway Deployment (3 Services)

### Service 1: Request Management

1. **Railway Dashboard:**
   - New Project → Deploy from GitHub
   - Root: `services/request-management`
   - Wait for build

2. **Environment Variables:**
   ```
   PORT=8001
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=<key>
   AWS_SECRET_ACCESS_KEY=<secret>
   AWS_DYNAMODB_TABLE_NAME=aam_requests
   AWS_SQS_QUEUE_URL=<sqs-url>
   AI_PROCESSING_SERVICE_URL=<update-after-deploying>
   DECISION_SIMULATION_SERVICE_URL=<update-after-ec2>
   EXECUTION_SERVICE_URL=<update-after-deploying>
   ADMIN_API_KEY=<your-key>
   ```

3. **Get URL:** Note the Railway URL

---

### Service 2: AI Processing

1. **Railway Dashboard:**
   - New Project → Deploy from GitHub
   - Root: `services/ai-processing`
   - Wait for build

2. **Environment Variables:**
   ```
   PORT=8002
   GEMINI_API_KEY=<your-key>
   AWS_REGION=us-west-2
   ```

3. **Get URL:** Note the Railway URL

4. **Update Request Management:**
   - Set `AI_PROCESSING_SERVICE_URL` to this URL

---

### Service 3: Execution

1. **Railway Dashboard:**
   - New Project → Deploy from GitHub
   - Root: `services/execution`
   - Wait for build

2. **Environment Variables:**
   ```
   PORT=8004
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=<key>
   AWS_SECRET_ACCESS_KEY=<secret>
   AWS_SQS_QUEUE_URL=<sqs-url>
   ```

3. **Get URL:** Note the Railway URL

4. **Update Request Management:**
   - Set `EXECUTION_SERVICE_URL` to this URL

---

## EC2 Deployment (1 Service)

### Step 1: Launch EC2

1. **AWS Console → EC2:**
   - Launch Instance
   - AMI: Ubuntu 22.04 LTS
   - Type: t2.micro (free tier)
   - Security Group: Allow SSH (22), HTTP (8003)
   - Launch

2. **Note:** Public IP address

### Step 2: Setup EC2

```bash
# SSH into EC2
ssh -i key.pem ubuntu@<ec2-ip>

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
newgrp docker

# Clone repo
git clone <your-repo>
cd Synergy_CMPE272
```

### Step 3: Initialize ChromaDB

```bash
# If ChromaDB not initialized
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ingest documents
python kb/ingest_documents.py

# Copy to services directory
cp -r vector_stores/chroma_db ../services/decision-simulation/vector_stores/
```

### Step 4: Deploy Service

```bash
cd infrastructure/ec2

# Create .env
cat > .env << EOF
GEMINI_API_KEY=<your-key>
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
EOF

# Deploy
docker-compose up -d

# Check logs
docker-compose logs -f

# Test
curl http://localhost:8003/health
```

### Step 5: Configure Security Group

1. **AWS Console → EC2 → Security Groups:**
   - Select your instance's security group
   - Add Inbound Rule:
     - Type: Custom TCP
     - Port: 8003
     - Source: 0.0.0.0/0

2. **Test from outside:**
   ```bash
   curl http://<ec2-public-ip>:8003/health
   ```

### Step 6: Update Railway

1. **Request Management Service:**
   - Update `DECISION_SIMULATION_SERVICE_URL` = `http://<ec2-ip>:8003`
   - Redeploy if needed

---

## Testing Checklist

```bash
# 1. Health Checks
curl https://request-management-service.up.railway.app/health
curl https://ai-processing-service.up.railway.app/health
curl http://<ec2-ip>:8003/health
curl https://execution-service.up.railway.app/health

# 2. Test Classification
curl -X POST https://ai-processing-service.up.railway.app/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"resident_id": "RES_1001", "message_text": "AC is broken"}'

# 3. Test End-to-End
curl -X POST https://request-management-service.up.railway.app/api/v1/submit-request \
  -H "Content-Type: application/json" \
  -d '{"resident_id": "RES_1001", "message_text": "AC is broken"}'
```

---

## Service URLs Template

After deployment, fill in these URLs:

```
Request Management: https://request-management-service.up.railway.app
AI Processing: https://ai-processing-service.up.railway.app
Decision & Simulation: http://<ec2-ip>:8003
Execution: https://execution-service.up.railway.app
```

---

## Troubleshooting Quick Fixes

**Service not responding:**
- Check Railway dashboard / EC2 status
- Check logs
- Verify environment variables

**Service-to-service communication failing:**
- Verify service URLs are correct
- Test URLs directly with curl
- Check EC2 security group

**ChromaDB not working:**
- Verify ChromaDB data exists
- Check volume mount (EC2)
- Check permissions

---

## Cost Summary

- **Railway:** FREE (within $5/month credit)
- **EC2:** FREE (750 hours/month for 12 months)
- **Total:** FREE for first year

---

For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

