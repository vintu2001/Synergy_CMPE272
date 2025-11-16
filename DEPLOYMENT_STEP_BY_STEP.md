# Step-by-Step Deployment Guide

This guide walks you through deploying all 4 microservices to production.

## 🎯 Deployment Strategy

- **Railway.app** (3 services): Request Management, AI Processing, Execution
- **AWS EC2** (1 service): Decision & Simulation (needs persistent storage for ChromaDB)

---

## 📋 Prerequisites Checklist

- [ ] GitHub repository with code pushed
- [ ] Railway.app account (sign up at https://railway.app)
- [ ] AWS account (free tier available)
- [ ] Gemini API key (from Google AI Studio)
- [ ] AWS credentials (Access Key ID and Secret Access Key)

---

## Part 1: Deploy to Railway (3 Services)

### Step 1: Sign Up for Railway

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign up with GitHub (recommended)
4. You'll get $5 free credit per month

### Step 2: Deploy Request Management Service

1. **Create New Project:**
   - Click "New Project" in Railway dashboard
   - Select "Deploy from GitHub repo"
   - Choose your repository: `Synergy_CMPE272`
   - **Important:** Set **Root Directory** to: `services/request-management`
   - Click "Deploy"

2. **Configure Environment Variables:**
   - Go to your project → Settings → Variables
   - Add these variables:
   ```
   PORT=8001
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=<your-aws-access-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
   AWS_DYNAMODB_TABLE_NAME=aam_requests
   AWS_SQS_QUEUE_URL=<your-sqs-queue-url>
   AI_PROCESSING_SERVICE_URL=<will-update-after-next-step>
   DECISION_SIMULATION_SERVICE_URL=<will-update-after-ec2>
   EXECUTION_SERVICE_URL=<will-update-after-next-step>
   ADMIN_API_KEY=<generate-a-secure-random-key>
   ```

3. **Get Service URL:**
   - Go to Settings → Networking
   - Railway generates a URL like: `https://request-management-production.up.railway.app`
   - **Copy this URL** - you'll need it for other services

4. **Wait for Deployment:**
   - Check the "Deployments" tab
   - Wait for build to complete (~2-3 minutes)
   - Verify it's running: Click the URL to see health check

### Step 3: Deploy AI Processing Service

1. **Create New Project:**
   - Click "New Project" → "Deploy from GitHub repo"
   - Choose repository: `Synergy_CMPE272`
   - Set **Root Directory** to: `services/ai-processing`
   - Click "Deploy"

2. **Configure Environment Variables:**
   ```
   PORT=8002
   GEMINI_API_KEY=<your-gemini-api-key>
   AWS_REGION=us-west-2
   ```

3. **Get Service URL:**
   - Settings → Networking
   - Copy the URL: `https://ai-processing-production.up.railway.app`

4. **Update Request Management Service:**
   - Go back to Request Management project
   - Settings → Variables
   - Update `AI_PROCESSING_SERVICE_URL` with the new URL
   - Service will auto-redeploy

### Step 4: Deploy Execution Service

1. **Create New Project:**
   - Click "New Project" → "Deploy from GitHub repo"
   - Choose repository: `Synergy_CMPE272`
   - Set **Root Directory** to: `services/execution`
   - Click "Deploy"

2. **Configure Environment Variables:**
   ```
   PORT=8004
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=<your-aws-access-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
   AWS_SQS_QUEUE_URL=<your-sqs-queue-url>
   ```

3. **Get Service URL:**
   - Settings → Networking
   - Copy the URL: `https://execution-production.up.railway.app`

4. **Update Request Management Service:**
   - Go back to Request Management project
   - Settings → Variables
   - Update `EXECUTION_SERVICE_URL` with the new URL

---

## Part 2: Deploy Decision & Simulation Service on EC2

### Step 1: Launch EC2 Instance

1. **Go to AWS Console:**
   - Navigate to EC2 Dashboard
   - Click "Launch Instance"

2. **Configure Instance:**
   - **Name:** `decision-simulation-service`
   - **AMI:** Ubuntu Server 22.04 LTS (free tier eligible)
   - **Instance type:** t2.micro (free tier eligible) or t2.small (recommended for better performance)
   - **Key pair:** 
     - If you don't have one, click "Create new key pair"
     - Name: `decision-simulation-key`
     - Download the `.pem` file (you'll need it to SSH)
   - **Network settings:**
     - Click "Edit"
     - Security group: Create new or use existing
     - **Inbound rules:**
       - SSH (port 22) from My IP
       - Custom TCP (port 8003) from Anywhere (0.0.0.0/0)
   - **Storage:** 30 GB gp3 (free tier)

3. **Launch:**
   - Click "Launch Instance"
   - Wait for instance to be "Running"
   - **Note the Public IPv4 address** (e.g., `54.123.45.67`)

### Step 2: Connect to EC2 Instance

1. **SSH into instance:**
   ```bash
   # On Mac/Linux
   chmod 400 decision-simulation-key.pem
   ssh -i decision-simulation-key.pem ubuntu@<your-ec2-public-ip>
   
   # On Windows (use Git Bash or WSL)
   # Same command as above
   ```

2. **Update system:**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

### Step 3: Install Docker

```bash
# Install Docker
sudo apt install -y docker.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (to run docker without sudo)
sudo usermod -aG docker ubuntu
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Step 4: Clone Repository

```bash
# Install Git
sudo apt install -y git

# Clone your repository
git clone https://github.com/<your-username>/Synergy_CMPE272.git
cd Synergy_CMPE272
```

### Step 5: Set Up Environment Variables

```bash
# Create .env file
cd infrastructure/ec2
nano .env
```

Add the following (press `Ctrl+X`, then `Y`, then `Enter` to save):
```env
GEMINI_API_KEY=<your-gemini-api-key>
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
REQUEST_MANAGEMENT_SERVICE_URL=https://request-management-production.up.railway.app
ADMIN_API_KEY=<same-admin-api-key-from-request-management>
```

### Step 6: Initialize ChromaDB (First Time Only)

**Initialize ChromaDB inside Docker container (Recommended)**

```bash
# First, start the container (it will be empty initially)
cd infrastructure/ec2
docker compose up -d

# Wait for container to be ready (~30 seconds)
sleep 30

# Run ingestion inside the container
docker exec -it decision-simulation-service python app/kb/ingest_documents.py

# This will create ChromaDB data in the Docker volume
# Check if it worked:
docker exec -it decision-simulation-service ls -la /app/vector_stores/chroma_db

# Restart to ensure everything loads correctly
docker compose restart decision-simulation

# Verify service is working
curl http://localhost:8003/health
```

**Alternative: Initialize before Docker (if you prefer)**

```bash
# Go to decision-simulation service directory
cd ../../services/decision-simulation

# Run the ingestion script
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/kb/ingest_documents.py

# This creates vector_stores/chroma_db directory
# Copy to Docker volume location (after starting container)
cd ../../infrastructure/ec2
docker compose up -d
docker cp ../../services/decision-simulation/vector_stores/chroma_db decision-simulation-service:/app/vector_stores/
docker compose restart decision-simulation
```

### Step 7: Verify Service is Running

```bash
# Check if service is running
docker compose ps

# Check logs
docker compose logs -f decision-simulation

# Test health endpoint
curl http://localhost:8003/health
# Should return: {"status":"healthy","service":"Decision & Simulation Service"}
```

### Step 8: Configure Security Group (Allow External Access)

1. **In AWS Console:**
   - Go to EC2 → Instances
   - Select your instance
   - Click "Security" tab
   - Click on Security Group name

2. **Add Inbound Rule:**
   - Click "Edit inbound rules"
   - Click "Add rule"
   - **Type:** Custom TCP
   - **Port:** 8003
   - **Source:** 0.0.0.0/0 (or restrict to Railway IPs if you know them)
   - Click "Save rules"

3. **Test from Outside:**
   ```bash
   # From your local machine
   curl http://<ec2-public-ip>:8003/health
   # Should return: {"status":"healthy","service":"Decision & Simulation Service"}
   ```

### Step 9: Update Railway Services with EC2 URL

1. **Update Request Management Service:**
   - Go to Railway dashboard
   - Select Request Management project
   - Settings → Variables
   - Update `DECISION_SIMULATION_SERVICE_URL` to: `http://<ec2-public-ip>:8003`
   - Service will auto-redeploy

---

## Part 3: Update Frontend

1. **Update API URL:**
   ```javascript
   // frontend/src/services/api.js
   const API_BASE_URL = 'https://request-management-production.up.railway.app';
   ```

2. **Deploy Frontend:**
   - Option 1: Deploy to Vercel/Netlify (recommended)
   - Option 2: Keep running locally and point to production API

---

## Part 4: Testing

### Test 1: Health Checks

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

### Test 2: End-to-End Request

```bash
curl -X POST https://request-management-production.up.railway.app/api/v1/submit-request \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "RES_Building123_1001",
    "message_text": "My AC is broken and it'\''s very hot outside"
  }'
```

Expected response should include:
- `status: "submitted"`
- `classification` (category, urgency, intent)
- `simulation.options` (array of options with source_doc_ids)

### Test 3: Check Logs

**Railway:**
- Go to each service → "Logs" tab
- Check for errors

**EC2:**
```bash
ssh -i key.pem ubuntu@<ec2-ip>
cd infrastructure/ec2
docker compose logs -f decision-simulation
```

---

## 🔧 Troubleshooting

### Service Not Responding

1. **Check Railway deployment:**
   - Go to service → Deployments
   - Check if latest deployment succeeded
   - View logs for errors

2. **Check EC2 service:**
   ```bash
   ssh -i key.pem ubuntu@<ec2-ip>
   docker compose ps
   docker compose logs decision-simulation
   ```

### Service-to-Service Communication Failing

1. **Verify URLs are correct:**
   - Check Railway service URLs (they may change)
   - Check EC2 public IP (it changes on restart unless using Elastic IP)

2. **Test connectivity:**
   ```bash
   # From EC2, test Railway service
   curl https://request-management-production.up.railway.app/health
   
   # From local, test EC2
   curl http://<ec2-ip>:8003/health
   ```

### ChromaDB Not Working

1. **Check if data exists:**
   ```bash
   ssh -i key.pem ubuntu@<ec2-ip>
   docker exec -it decision-simulation-service ls -la /app/vector_stores/chroma_db
   ```

2. **Re-ingest if needed:**
   ```bash
   cd Synergy_CMPE272/services/decision-simulation
   source venv/bin/activate
   python app/kb/ingest_documents.py
   docker compose restart decision-simulation
   ```

### Out of Memory on EC2

- **t2.micro** has 1 GB RAM (may be insufficient)
- **Upgrade to t2.small** (2 GB RAM) - ~$15/month
- Or optimize: reduce RAG_TOP_K, etc.

---

## 📊 Monitoring

### Railway
- Dashboard → Service → Metrics
- Monitor CPU, memory, requests
- View logs in real-time

### EC2
- AWS CloudWatch → EC2 metrics
- Monitor CPU, memory, network
- Set up billing alerts

---

## 💰 Cost Monitoring

### Railway
- Free tier: $5/month credit
- Monitor: Dashboard → Usage
- Set up billing alerts

### EC2
- Free tier: 750 hours/month for 12 months (t2.micro)
- Monitor: AWS Cost Explorer
- Set up billing alerts

---

## 🔄 Updating Services

### Railway
- Push to GitHub
- Railway auto-deploys on push
- Or manually trigger: Dashboard → Deploy → Redeploy

### EC2
```bash
ssh -i key.pem ubuntu@<ec2-ip>
cd Synergy_CMPE272
git pull
cd infrastructure/ec2
docker compose up -d --build
```

---

## ✅ Deployment Checklist

- [ ] All 3 Railway services deployed and healthy
- [ ] EC2 instance running and accessible
- [ ] ChromaDB initialized with knowledge base
- [ ] All environment variables set correctly
- [ ] Service URLs updated in Request Management
- [ ] Security groups configured (EC2 port 8003 open)
- [ ] Health checks passing for all services
- [ ] End-to-end request test successful
- [ ] Frontend updated with production API URL

---

## 🎉 You're Done!

Your microservices are now deployed and running in production. Test the full flow through the frontend or API calls.

For issues, check:
1. Service logs (Railway dashboard / EC2)
2. Health endpoints
3. Environment variables
4. Network connectivity

