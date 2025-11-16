# Free Deployment Platforms for Microservices
## Comparison and Recommendations

---

## Overview

This document compares free platforms suitable for deploying 4 Python/FastAPI microservices. Each platform has different limitations, so choose based on your needs.

---

## Platform Comparison

### 1. Railway.app ⭐ **RECOMMENDED**

**Free Tier:**
- **$5 free credit per month** (Hobby plan)
- **No credit card required** initially
- **750 hours** of usage per month
- **512 MB RAM** per service
- **1 GB storage** per service

**Pros:**
- ✅ **Excellent Docker support** - Perfect for microservices
- ✅ **Easy deployment** - Git-based, auto-deploy
- ✅ **Built-in PostgreSQL/MySQL** (free tier available)
- ✅ **Environment variables** - Easy configuration
- ✅ **Custom domains** - Free SSL
- ✅ **Service discovery** - Services can communicate via internal URLs
- ✅ **Logs and metrics** - Built-in monitoring
- ✅ **No sleep** - Services stay awake (unlike some free tiers)

**Cons:**
- ❌ **Limited to $5/month** - May need to upgrade for 4 services
- ❌ **512 MB RAM** - May be tight for Decision & Simulation service (RAG)
- ❌ **No persistent storage** - Need external storage for ChromaDB

**Cost Estimate for 4 Services:**
- Request Management: ~$1.25/month
- AI Processing: ~$1.25/month
- Decision & Simulation: ~$2/month (needs more resources)
- Execution: ~$0.50/month
- **Total: ~$5/month** (fits free tier!)

**Deployment:**
```yaml
# railway.json (per service)
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Best For:** Small to medium projects, easy setup, Docker support

---

### 2. Render ⭐ **GOOD ALTERNATIVE**

**Free Tier:**
- **750 hours** of instance time per month
- **512 MB RAM** per service
- **100 GB bandwidth** per month
- **Free SSL** certificates
- **Auto-deploy** from Git

**Pros:**
- ✅ **Free tier available** - No credit card required
- ✅ **Docker support** - Can deploy containers
- ✅ **PostgreSQL** - Free tier database (90 days, then $7/month)
- ✅ **Background workers** - Good for async processing
- ✅ **Custom domains** - Free SSL
- ✅ **Environment variables** - Easy config

**Cons:**
- ❌ **Services sleep after 15 min inactivity** - Cold starts
- ❌ **Limited RAM** - 512 MB may not be enough for RAG
- ❌ **No persistent storage** - Need external storage
- ❌ **Slower cold starts** - After sleep period

**Cost Estimate:**
- 4 services × 750 hours = 3000 hours needed
- **Free tier: 750 hours total** - Can only run 1-2 services free
- Need to upgrade for all 4 services

**Best For:** Development/testing, single service deployments

---

### 3. Fly.io ⚠️ **LIMITED FREE TIER**

**Free Tier:**
- **One-time $5 credit** for new users
- **3 shared-cpu VMs** (256 MB RAM each)
- **3 GB persistent storage**
- **160 GB outbound data transfer**

**Pros:**
- ✅ **Global edge network** - Low latency worldwide
- ✅ **Docker support** - Excellent container support
- ✅ **Persistent volumes** - Can store ChromaDB data
- ✅ **Fast cold starts** - Better than Render
- ✅ **Service mesh** - Built-in service discovery

**Cons:**
- ❌ **No ongoing free tier** - Only $5 credit
- ❌ **Paid after credit** - ~$1.94/month per VM minimum
- ❌ **Limited RAM** - 256 MB per VM (very tight)
- ❌ **Need credit card** - For persistent volumes

**Cost Estimate:**
- 4 services × $1.94 = **~$7.76/month minimum**
- Not truly free after initial credit

**Best For:** Production apps, global distribution, willing to pay small amount

---

### 4. Koyeb ⭐ **GOOD OPTION**

**Free Tier:**
- **2 nano services** (free forever)
- **256 MB RAM** per service
- **Auto-scaling** included
- **Global edge network**
- **Free SSL**

**Pros:**
- ✅ **Truly free** - 2 services forever
- ✅ **Docker support** - Full container support
- ✅ **No sleep** - Services stay awake
- ✅ **Git-based deployment** - Easy setup
- ✅ **Service discovery** - Internal networking
- ✅ **Global CDN** - Fast worldwide

**Cons:**
- ❌ **Only 2 free services** - Need 4 services
- ❌ **256 MB RAM** - Very limited
- ❌ **No persistent storage** - Need external storage
- ❌ **Limited to 2 services** - Can't deploy all 4 free

**Best For:** 2-service deployments, testing, small projects

---

### 5. Google Cloud Run ⭐ **BEST FOR SCALE**

**Free Tier:**
- **2 million requests** per month
- **360,000 GB-seconds** compute time
- **180,000 vCPU-seconds**
- **1 GB egress** per month

**Pros:**
- ✅ **Generous free tier** - Can handle 4 services
- ✅ **Serverless** - Pay only for usage
- ✅ **Auto-scaling** - Scales to zero when idle
- ✅ **Docker support** - Full container support
- ✅ **Global deployment** - Multi-region
- ✅ **Cloud Storage** - Can use for ChromaDB data
- ✅ **Service mesh** - Built-in service discovery

**Cons:**
- ❌ **Cold starts** - First request may be slow
- ❌ **Need Google Cloud account** - Credit card required
- ❌ **Complex setup** - More configuration needed
- ❌ **Billing complexity** - Need to monitor usage

**Cost Estimate:**
- **Free tier covers:** ~2M requests/month
- **After free tier:** ~$0.40 per million requests
- **Storage:** $0.020/GB/month (for ChromaDB)

**Best For:** Production, scalable apps, Google Cloud users

---

### 6. Vercel ⚠️ **NOT RECOMMENDED**

**Free Tier:**
- **100 GB bandwidth** per month
- **100 serverless function executions** per day
- **Unlimited static deployments**

**Pros:**
- ✅ **Excellent for frontend** - Best in class
- ✅ **Fast CDN** - Global edge network
- ✅ **Easy deployment** - Git-based

**Cons:**
- ❌ **Not designed for Python microservices** - Optimized for Node.js
- ❌ **Serverless functions only** - Not ideal for long-running services
- ❌ **Limited Python support** - Better for frontend/API routes
- ❌ **No Docker** - Can't deploy containers
- ❌ **Cold starts** - Functions spin down

**Best For:** Frontend deployment, not microservices

---

### 7. Heroku ⚠️ **LIMITED FREE TIER**

**Free Tier:**
- **No longer available** - Discontinued in 2022
- **Eco Dyno:** $5/month minimum

**Status:** Not recommended - Free tier removed

---

## Recommended Deployment Strategy

### Option 1: Railway.app (Best Balance) ⭐

**Why:**
- $5/month free credit covers all 4 services
- Excellent Docker support
- Easy deployment
- No sleep issues
- Good for development and small production

**Setup:**
1. Create Railway account (free)
2. Create 4 new projects (one per service)
3. Connect GitHub repository
4. Deploy each service from its directory
5. Set environment variables
6. Services communicate via Railway's internal network

**Limitations:**
- Need external storage for ChromaDB (use S3 or Railway's storage)
- 512 MB RAM may be tight for Decision & Simulation service

**Cost:** **FREE** (within $5/month credit)

---

### Option 2: Hybrid Approach (Railway + External Storage)

**Services on Railway:**
- Request Management
- AI Processing
- Execution

**Decision & Simulation on Google Cloud Run:**
- Needs more resources (RAG, ChromaDB)
- Use Cloud Storage for vector store
- Free tier covers usage

**Why:**
- Railway: Easy, free for 3 services
- Cloud Run: Better resources for RAG service
- Total cost: **FREE** (within free tiers)

---

### Option 3: All on Google Cloud Run

**Why:**
- Most generous free tier
- Can handle all 4 services
- Better for production
- Auto-scaling
- Persistent storage options

**Setup:**
1. Create Google Cloud account
2. Enable Cloud Run API
3. Build and push Docker images to Container Registry
4. Deploy each service
5. Configure service URLs for inter-service communication

**Cost:** **FREE** (within 2M requests/month)

---

## Detailed Railway.app Deployment Guide

### Step 1: Prepare Services

**Directory Structure:**
```
services/
├── request-management/
│   ├── Dockerfile
│   ├── railway.json
│   └── app/
├── ai-processing/
│   ├── Dockerfile
│   ├── railway.json
│   └── app/
├── decision-simulation/
│   ├── Dockerfile
│   ├── railway.json
│   └── app/
└── execution/
    ├── Dockerfile
    ├── railway.json
    └── app/
```

### Step 2: Create Railway Projects

1. **Go to Railway.app** → Sign up (free)
2. **Create 4 new projects:**
   - `request-management-service`
   - `ai-processing-service`
   - `decision-simulation-service`
   - `execution-service`

### Step 3: Configure Each Service

**Example: `services/request-management/railway.json`**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Example: `services/request-management/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE $PORT

# Run
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 4: Set Environment Variables

**Request Management Service:**
```env
PORT=8001
AWS_REGION=us-west-2
AWS_DYNAMODB_TABLE_NAME=aam_requests
AWS_SQS_QUEUE_URL=<sqs-url>
AI_PROCESSING_SERVICE_URL=https://ai-processing-service.up.railway.app
DECISION_SIMULATION_SERVICE_URL=https://decision-simulation-service.up.railway.app
EXECUTION_SERVICE_URL=https://execution-service.up.railway.app
```

**AI Processing Service:**
```env
PORT=8002
GEMINI_API_KEY=<your-key>
```

**Decision & Simulation Service:**
```env
PORT=8003
GEMINI_API_KEY=<your-key>
RAG_ENABLED=true
VECTOR_STORE_PATH=/app/vector_stores/chroma_db
# Use Railway's volume or external storage (S3) for ChromaDB
```

**Execution Service:**
```env
PORT=8004
AWS_REGION=us-west-2
AWS_SQS_QUEUE_URL=<sqs-url>
```

### Step 5: Deploy

1. **Connect GitHub** to each Railway project
2. **Select service directory** (e.g., `services/request-management`)
3. **Railway auto-detects** Dockerfile
4. **Deploy** - Railway builds and deploys automatically
5. **Get service URL** - Railway provides public URL

### Step 6: Service Communication

**Railway provides internal networking:**
- Services can communicate via Railway-generated URLs
- Or use Railway's private networking (if available)

**Example HTTP call:**
```python
import httpx

# In request-management service
async with httpx.AsyncClient() as client:
    response = await client.post(
        os.getenv("AI_PROCESSING_SERVICE_URL") + "/api/v1/classify",
        json={"message_text": message_text}
    )
```

---

## ChromaDB Storage Solution

### Problem:
ChromaDB needs persistent storage, but Railway free tier doesn't provide volumes.

### Solutions:

#### Option 1: Use S3 for ChromaDB (Recommended)
```python
# In decision-simulation service
# Store ChromaDB data in S3
# Load on startup, sync periodically
import boto3

s3 = boto3.client('s3')
# Download ChromaDB data from S3 on startup
# Upload changes periodically
```

#### Option 2: Use Railway Volume (Paid)
- Railway offers volumes for $0.25/GB/month
- Small ChromaDB: ~1-2 GB = $0.25-0.50/month
- Still within free tier if other services use <$4.50

#### Option 3: Use External Database
- Use PostgreSQL with pgvector extension
- Railway provides free PostgreSQL
- Convert ChromaDB to PostgreSQL

---

## Cost Comparison

| Platform | Free Tier | 4 Services Cost | Best For |
|----------|-----------|-----------------|----------|
| **Railway.app** | $5/month credit | **FREE** | Development, small production |
| **Render** | 750 hours | **$0-15/month** | Testing, 1-2 services |
| **Fly.io** | $5 one-time | **~$8/month** | Production, global |
| **Koyeb** | 2 services | **FREE (2 only)** | Testing, 2 services |
| **Google Cloud Run** | 2M requests | **FREE** | Production, scalable |
| **Vercel** | Limited | **N/A** | Frontend only |

---

## Final Recommendation

### For Development/Testing:
**Railway.app** - Easiest setup, $5 free credit covers all services

### For Production:
**Google Cloud Run** - Most generous free tier, better scalability

### Hybrid Approach:
- **3 services on Railway** (Request, AI, Execution)
- **1 service on Cloud Run** (Decision & Simulation - needs more resources)

---

## Quick Start: Railway.app

1. **Sign up:** https://railway.app (free)
2. **Install CLI:** `npm i -g @railway/cli`
3. **Login:** `railway login`
4. **Create projects:** `railway init` (4 times, one per service)
5. **Deploy:** `railway up` (from each service directory)

**Total time:** ~30 minutes for all 4 services

---

## Important Notes

1. **Free tiers have limits** - Monitor usage
2. **External services** - DynamoDB, SQS still need AWS (free tier available)
3. **Storage** - ChromaDB needs external storage (S3 free tier: 5 GB)
4. **Domain** - Railway provides free subdomain, custom domain free
5. **SSL** - All platforms provide free SSL certificates

---

## Next Steps

1. **Choose platform** based on your needs
2. **Prepare Dockerfiles** for each service
3. **Set up environment variables**
4. **Deploy services** one by one
5. **Test inter-service communication**
6. **Monitor usage** to stay within free tier

**Recommendation:** Start with **Railway.app** for easiest setup, then migrate to **Google Cloud Run** if you need more resources or scale.

