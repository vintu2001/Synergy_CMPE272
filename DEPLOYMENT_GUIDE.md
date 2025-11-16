# Deployment Guide
## Hybrid Railway + EC2 Strategy

This guide walks you through deploying the 4 microservices using Railway (3 services) and EC2 (1 service).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Railway.app                           │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Request          │  │ AI           │  │ Execution│  │
│  │ Management       │  │ Processing   │  │ Service  │  │
│  │ (Port 8001)      │  │ (Port 8002)  │  │ (8004)   │  │
│  └──────────────────┘  └──────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP Calls
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    AWS EC2                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Decision & Simulation Service (Port 8003)         │  │
│  │ - RAG System                                      │  │
│  │ - ChromaDB (Persistent Volume)                    │  │
│  │ - Knowledge Base                                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Accounts:
1. **Railway.app** - Sign up at https://railway.app (free)
2. **AWS Account** - Sign up at https://aws.amazon.com (free tier available)
3. **GitHub** - For code repository

### Required Tools:
- Docker (for local testing)
- AWS CLI (for EC2 setup)
- Git
- Python 3.11+

---

## Part 1: Deploy Services on Railway

### Step 1: Prepare Railway Projects

1. **Sign up for Railway:**
   - Go to https://railway.app
   - Sign up with GitHub
   - You'll get $5 free credit per month

2. **Install Railway CLI (optional but recommended):**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

### Step 2: Deploy Request Management Service

1. **Create new project on Railway:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select `services/request-management` as root directory

2. **Configure environment variables:**
   ```
   PORT=8001
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=<your-aws-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret>
   AWS_DYNAMODB_TABLE_NAME=aam_requests
   AWS_SQS_QUEUE_URL=<your-sqs-url>
   AI_PROCESSING_SERVICE_URL=https://ai-processing-service.up.railway.app
   DECISION_SIMULATION_SERVICE_URL=http://<ec2-ip>:8003
   EXECUTION_SERVICE_URL=https://execution-service.up.railway.app
   ```

3. **Deploy:**
   - Railway will automatically detect the Dockerfile
   - Build and deploy will start automatically
   - Wait for deployment to complete (~2-3 minutes)

4. **Get service URL:**
   - Railway provides a URL like: `https://request-management-service.up.railway.app`
   - Note this URL for other services

### Step 3: Deploy AI Processing Service

1. **Create new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select `services/ai-processing` as root directory

2. **Configure environment variables:**
   ```
   PORT=8002
   GEMINI_API_KEY=<your-gemini-key>
   AWS_REGION=us-west-2
   ```

3. **Deploy:**
   - Railway will build and deploy automatically
   - Get the service URL: `https://ai-processing-service.up.railway.app`

4. **Update Request Management Service:**
   - Go back to Request Management project
   - Update `AI_PROCESSING_SERVICE_URL` with the new URL
   - Redeploy if needed

### Step 4: Deploy Execution Service

1. **Create new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select `services/execution` as root directory

2. **Configure environment variables:**
   ```
   PORT=8004
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=<your-aws-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret>
   AWS_SQS_QUEUE_URL=<your-sqs-url>
   ```

3. **Deploy:**
   - Railway will build and deploy automatically
   - Get the service URL: `https://execution-service.up.railway.app`

4. **Update Request Management Service:**
   - Update `EXECUTION_SERVICE_URL` with the new URL

---

## Part 2: Deploy Decision & Simulation Service on EC2

### Step 1: Launch EC2 Instance

1. **Go to AWS Console:**
   - Navigate to EC2 Dashboard
   - Click "Launch Instance"

2. **Configure instance:**
   - **Name:** `decision-simulation-service`
   - **AMI:** Ubuntu 22.04 LTS (free tier eligible)
   - **Instance type:** t2.micro (free tier eligible)
   - **Key pair:** Create new or use existing
   - **Network settings:** 
     - Allow SSH (port 22)
     - Allow HTTP (port 8003)
     - Allow HTTPS (port 443)
   - **Storage:** 30 GB (free tier)

3. **Launch instance:**
   - Click "Launch Instance"
   - Wait for instance to be running
   - Note the **Public IP address**

### Step 2: Connect to EC2 Instance

1. **SSH into instance:**
   ```bash
   ssh -i your-key.pem ubuntu@<ec2-public-ip>
   ```

2. **Update system:**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

### Step 3: Install Docker

```bash
# Install Docker
sudo apt install -y docker.io docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker ubuntu
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Step 4: Clone Repository

```bash
# Install Git
sudo apt install -y git

# Clone repository
git clone <your-repo-url>
cd Synergy_CMPE272
```

### Step 5: Set Up Environment Variables

```bash
# Create .env file
cd infrastructure/ec2
nano .env
```

Add the following:
```env
GEMINI_API_KEY=<your-gemini-key>
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
```

### Step 6: Initialize ChromaDB (First Time Only)

```bash
# If ChromaDB is not initialized, run ingestion
cd ../../backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ingest knowledge base documents
python kb/ingest_documents.py

# Copy ChromaDB data to services directory
cp -r vector_stores/chroma_db ../services/decision-simulation/vector_stores/
```

### Step 7: Deploy Service

```bash
# Go to EC2 deployment directory
cd infrastructure/ec2

# Build and start service
docker-compose up -d

# Check logs
docker-compose logs -f decision-simulation

# Check if service is running
curl http://localhost:8003/health
```

### Step 8: Configure Security Group

1. **In AWS Console:**
   - Go to EC2 → Security Groups
   - Select your instance's security group
   - Add inbound rule:
     - **Type:** Custom TCP
     - **Port:** 8003
     - **Source:** 0.0.0.0/0 (or restrict to Railway IPs)

2. **Test from outside:**
   ```bash
   curl http://<ec2-public-ip>:8003/health
   ```

### Step 9: Update Railway Services

1. **Update Request Management Service:**
   - Go to Railway dashboard
   - Select Request Management project
   - Update environment variable:
     ```
     DECISION_SIMULATION_SERVICE_URL=http://<ec2-public-ip>:8003
     ```
   - Redeploy if needed

---

## Part 3: Testing the Deployment

### Test 1: Health Checks

**Request Management Service:**
```bash
curl https://request-management-service.up.railway.app/health
# Expected: {"status":"healthy","service":"Request Management Service"}
```

**AI Processing Service:**
```bash
curl https://ai-processing-service.up.railway.app/health
# Expected: {"status":"healthy","service":"AI Processing Service"}
```

**Decision & Simulation Service:**
```bash
curl http://<ec2-ip>:8003/health
# Expected: {"status":"healthy","service":"Decision & Simulation Service"}
```

**Execution Service:**
```bash
curl https://execution-service.up.railway.app/health
# Expected: {"status":"healthy","service":"Execution Service"}
```

### Test 2: End-to-End Request Flow

1. **Submit a request:**
   ```bash
   curl -X POST https://request-management-service.up.railway.app/api/v1/submit-request \
     -H "Content-Type: application/json" \
     -d '{
       "resident_id": "RES_Building123_1001",
       "message_text": "My AC is broken and it'\''s very hot"
     }'
   ```

2. **Expected flow:**
   - Request Management receives request
   - Calls AI Processing for classification
   - Calls Decision & Simulation for options
   - Stores result in DynamoDB
   - Returns response with options

3. **Check response:**
   - Should include classification (category, urgency)
   - Should include simulation options
   - Should have request_id

### Test 3: Service-to-Service Communication

**Test AI Processing directly:**
```bash
curl -X POST https://ai-processing-service.up.railway.app/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "RES_1001",
    "message_text": "AC is broken"
  }'
```

**Test Decision & Simulation:**
```bash
curl -X POST http://<ec2-ip>:8003/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Maintenance",
    "urgency": "High",
    "message_text": "AC is broken",
    "resident_id": "RES_1001"
  }'
```

### Test 4: Check Logs

**Railway logs:**
- Go to Railway dashboard
- Select each service
- Click "Logs" tab
- Check for errors

**EC2 logs:**
```bash
ssh -i key.pem ubuntu@<ec2-ip>
cd infrastructure/ec2
docker-compose logs -f decision-simulation
```

### Test 5: Frontend Integration

1. **Update frontend API URL:**
   ```javascript
   // frontend/src/services/api.js
   const API_BASE_URL = 'https://request-management-service.up.railway.app';
   ```

2. **Test from frontend:**
   - Submit a request
   - Check if it goes through all services
   - Verify options are displayed

---

## Troubleshooting

### Issue: Service not responding

**Check:**
1. Service is running (Railway dashboard / EC2)
2. Environment variables are set correctly
3. Ports are open (EC2 security group)
4. Service URLs are correct

**Fix:**
```bash
# EC2: Check container status
docker-compose ps

# EC2: Restart service
docker-compose restart decision-simulation

# Railway: Check deployment logs
# Go to Railway dashboard → Logs
```

### Issue: Service-to-service communication failing

**Check:**
1. Service URLs are correct
2. Services are accessible (test with curl)
3. CORS is configured
4. Network connectivity

**Fix:**
- Update environment variables with correct URLs
- Check Railway service URLs (they may change)
- Verify EC2 public IP is correct

### Issue: ChromaDB not working

**Check:**
1. ChromaDB data exists in volume
2. Volume is mounted correctly
3. Permissions are correct

**Fix:**
```bash
# Check volume
docker volume ls
docker volume inspect synergy-network_chroma-data

# Check ChromaDB data
docker exec -it decision-simulation-service ls -la /app/vector_stores/chroma_db
```

### Issue: Out of memory on EC2

**Check:**
- t2.micro has 1 GB RAM
- Decision & Simulation service needs more

**Fix:**
- Upgrade to t2.small (2 GB RAM) - ~$15/month
- Or optimize service (reduce RAG top_k, etc.)

---

## Monitoring

### Railway Monitoring

1. **Metrics:**
   - Go to Railway dashboard
   - Click on service
   - View "Metrics" tab
   - Monitor CPU, memory, requests

2. **Logs:**
   - View real-time logs
   - Search logs
   - Export logs

### EC2 Monitoring

1. **CloudWatch:**
   - Go to AWS CloudWatch
   - View EC2 metrics
   - Set up alarms

2. **Docker logs:**
   ```bash
   docker-compose logs -f decision-simulation
   ```

---

## Cost Monitoring

### Railway Costs

- **Free tier:** $5/month credit
- **Monitor:** Railway dashboard → Usage
- **Alert:** Set up billing alerts

### EC2 Costs

- **Free tier:** 750 hours/month for 12 months
- **Monitor:** AWS Cost Explorer
- **Alert:** Set up billing alerts in AWS

---

## Next Steps

1. **Set up custom domains** (optional)
2. **Configure SSL certificates** (Railway provides free SSL)
3. **Set up monitoring alerts**
4. **Configure auto-scaling** (if needed)
5. **Set up CI/CD** (GitHub Actions)

---

## Quick Reference

### Service URLs

After deployment, note these URLs:

- **Request Management:** `https://request-management-service.up.railway.app`
- **AI Processing:** `https://ai-processing-service.up.railway.app`
- **Decision & Simulation:** `http://<ec2-ip>:8003`
- **Execution:** `https://execution-service.up.railway.app`

### Useful Commands

**Railway:**
```bash
railway status
railway logs
railway variables
```

**EC2:**
```bash
# SSH into instance
ssh -i key.pem ubuntu@<ec2-ip>

# Check service status
docker-compose ps

# View logs
docker-compose logs -f decision-simulation

# Restart service
docker-compose restart decision-simulation

# Update service
git pull
docker-compose up -d --build
```

---

## Support

If you encounter issues:
1. Check logs (Railway dashboard / EC2)
2. Verify environment variables
3. Test service health endpoints
4. Check service-to-service URLs
5. Review this guide's troubleshooting section

