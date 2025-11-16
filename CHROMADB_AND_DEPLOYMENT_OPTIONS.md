# ChromaDB Alternatives & Multi-Platform Deployment Strategy

---

## Why ChromaDB? Can We Use S3 Instead?

### What ChromaDB Does

**ChromaDB is a Vector Database** - It's specifically designed for:
- **Semantic Search**: Finding documents by meaning, not just keywords
- **Similarity Search**: Finding documents similar to a query using embeddings
- **Fast Vector Operations**: Optimized for cosine similarity, dot product, etc.
- **Metadata Filtering**: Filter by building_id, category, doc_type, etc.

**Example:**
```python
# Query: "AC is broken"
# ChromaDB:
# 1. Converts query to embedding vector [0.1, 0.5, -0.3, ...]
# 2. Searches for similar vectors in database
# 3. Returns documents with highest similarity scores
# 4. Filters by metadata (building_id, category)
```

### Can S3 Replace ChromaDB?

**Short Answer: NO** ❌

**Why:**
- **S3 is object storage** - Stores files, not vectors
- **No vector search** - Can't do similarity search
- **No indexing** - Would need to download all embeddings and search in memory
- **Not optimized** - Vector search requires specialized algorithms (HNSW, IVF)

**What S3 CAN do:**
- ✅ Store ChromaDB data files (backup/persistence)
- ✅ Store embeddings as files (but still need vector DB for search)
- ✅ Store knowledge base documents (source files)

---

## ChromaDB Alternatives

### Option 1: PostgreSQL with pgvector ⭐ **RECOMMENDED**

**Why:**
- ✅ **Free** - PostgreSQL is free
- ✅ **Vector search** - pgvector extension provides vector similarity
- ✅ **Persistent** - Database, not file-based
- ✅ **Available on Railway** - Railway provides free PostgreSQL
- ✅ **Metadata filtering** - Native SQL WHERE clauses
- ✅ **Scalable** - Can handle large datasets

**How it works:**
```sql
-- Create table with vector column
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    doc_id TEXT,
    text TEXT,
    embedding vector(384),  -- 384 dimensions for all-MiniLM-L6-v2
    metadata JSONB
);

-- Vector similarity search
SELECT doc_id, text, 
       1 - (embedding <=> query_embedding) as similarity
FROM document_embeddings
WHERE metadata->>'building_id' = 'Building123'
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

**Migration from ChromaDB:**
- Export embeddings from ChromaDB
- Import into PostgreSQL with pgvector
- Update retriever code to use PostgreSQL instead of ChromaDB

**Cost:** **FREE** (Railway PostgreSQL free tier)

---

### Option 2: Keep ChromaDB with Different Storage

#### A. ChromaDB with S3 Backend (Hybrid)

**How:**
- Store ChromaDB data files in S3
- Download on service startup
- Use local ChromaDB for queries
- Sync back to S3 periodically

**Pros:**
- ✅ Keep existing ChromaDB code
- ✅ S3 for persistence (free tier: 5 GB)
- ✅ Works on Railway

**Cons:**
- ❌ Cold starts slower (download from S3)
- ❌ Need sync logic
- ❌ Not ideal for frequent updates

**Implementation:**
```python
import boto3
import os
import shutil

# On startup
s3 = boto3.client('s3')
s3.download_file('my-bucket', 'chroma_db.tar.gz', '/tmp/chroma_db.tar.gz')
shutil.unpack_archive('/tmp/chroma_db.tar.gz', '/app/vector_stores/')

# Use ChromaDB normally
chroma_client = chromadb.PersistentClient(path='/app/vector_stores/chroma_db')

# Periodically sync back to S3
def sync_to_s3():
    shutil.make_archive('/tmp/chroma_db', 'gztar', '/app/vector_stores/chroma_db')
    s3.upload_file('/tmp/chroma_db.tar.gz', 'my-bucket', 'chroma_db.tar.gz')
```

---

#### B. ChromaDB with Railway Volume (Paid)

**How:**
- Use Railway's volume feature
- Mount volume to service
- ChromaDB stores data on volume

**Cost:**
- $0.25/GB/month
- Small ChromaDB: ~1-2 GB = $0.25-0.50/month
- Still within Railway's $5 free credit

**Setup:**
```yaml
# railway.json
{
  "deploy": {
    "volumes": {
      "/app/vector_stores": "chroma-data"
    }
  }
}
```

---

### Option 3: Managed Vector Databases

#### A. Pinecone (Managed)
- **Free tier**: 1 index, 100K vectors
- **Cost**: $70/month after free tier
- **Pros**: Fully managed, fast, scalable
- **Cons**: Expensive, external dependency

#### B. Qdrant Cloud
- **Free tier**: 1 cluster, 1 GB
- **Cost**: $25/month after free tier
- **Pros**: Open source, self-hostable
- **Cons**: Still costs money

#### C. Weaviate Cloud
- **Free tier**: Limited
- **Cost**: $25/month
- **Pros**: GraphQL API, good features
- **Cons**: Costs money

**Recommendation:** Use **PostgreSQL with pgvector** - Free and works great!

---

## ChromaDB on Railway - Solutions

### Solution 1: PostgreSQL with pgvector (Best) ⭐

**Steps:**
1. **Create PostgreSQL on Railway:**
   - Add PostgreSQL service to Railway project
   - Railway provides free PostgreSQL (90 days, then $5/month)

2. **Enable pgvector extension:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Migrate from ChromaDB:**
   - Export embeddings from ChromaDB
   - Import into PostgreSQL
   - Update retriever code

4. **Update code:**
   ```python
   # Instead of ChromaDB
   import psycopg2
   from pgvector.psycopg2 import register_vector
   
   conn = psycopg2.connect(DATABASE_URL)
   register_vector(conn)
   
   # Vector search
   cur.execute("""
       SELECT doc_id, text, metadata,
              1 - (embedding <=> %s::vector) as similarity
       FROM document_embeddings
       WHERE metadata->>'category' = %s
       ORDER BY embedding <=> %s::vector
       LIMIT %s
   """, (query_embedding, category, query_embedding, top_k))
   ```

**Cost:** **FREE** (Railway PostgreSQL free tier)

---

### Solution 2: ChromaDB with S3 Sync

**Steps:**
1. **Store ChromaDB in S3:**
   - Create S3 bucket (free tier: 5 GB)
   - Upload ChromaDB data files

2. **Download on startup:**
   ```python
   # In Dockerfile or startup script
   aws s3 sync s3://my-bucket/chroma_db /app/vector_stores/chroma_db
   ```

3. **Use ChromaDB normally:**
   ```python
   chroma_client = chromadb.PersistentClient(
       path='/app/vector_stores/chroma_db'
   )
   ```

4. **Sync back periodically:**
   ```python
   # Background task
   aws s3 sync /app/vector_stores/chroma_db s3://my-bucket/chroma_db
   ```

**Cost:** **FREE** (S3 free tier: 5 GB storage, 20K GET requests)

---

### Solution 3: ChromaDB with Railway Volume

**Steps:**
1. **Add volume to Railway service:**
   ```json
   {
     "deploy": {
       "volumes": {
         "/app/vector_stores": "chroma-data"
       }
     }
   }
   ```

2. **Use ChromaDB normally:**
   ```python
   chroma_client = chromadb.PersistentClient(
       path='/app/vector_stores/chroma_db'
   )
   ```

**Cost:** $0.25-0.50/month (1-2 GB volume)

---

## EC2 Deployment - Full Guide

### Why EC2?

**Pros:**
- ✅ **Full control** - Complete server access
- ✅ **Persistent storage** - EBS volumes for ChromaDB
- ✅ **AWS Free Tier** - 750 hours/month of t2.micro (1 year)
- ✅ **All services on one instance** - Or separate instances
- ✅ **Familiar** - Same as current setup

**Cons:**
- ❌ **More setup** - Need to configure everything
- ❌ **Maintenance** - You manage the server
- ❌ **Scaling** - Manual scaling (or use Auto Scaling)

---

### EC2 Free Tier Details

**AWS Free Tier (12 months):**
- **t2.micro instance**: 750 hours/month
- **30 GB EBS storage**: Free
- **2 million I/O requests**: Free
- **15 GB data transfer out**: Free

**After 12 months:**
- t2.micro: ~$8.50/month
- EBS: $0.10/GB/month
- Data transfer: $0.09/GB after 15 GB

**Cost:** **FREE for 12 months**, then ~$10-15/month

---

### EC2 Deployment Strategy

#### Option A: Single EC2 Instance (All Services)

**Architecture:**
```
EC2 t2.micro (1 GB RAM, 1 vCPU)
├── Request Management (Port 8001)
├── AI Processing (Port 8002)
├── Decision & Simulation (Port 8003)
└── Execution (Port 8004)
```

**Setup:**
1. **Launch EC2 instance:**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t2.micro
   - Storage: 30 GB EBS (free tier)

2. **Install Docker:**
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Deploy services:**
   ```bash
   # Clone repository
   git clone <repo>
   cd Synergy_CMPE272
   
   # Build and run with docker-compose
   docker-compose up -d
   ```

4. **Configure security group:**
   - Open ports: 8001, 8002, 8003, 8004
   - Or use ALB (Application Load Balancer)

**Docker Compose:**
```yaml
version: '3.8'
services:
  request-management:
    build: ./services/request-management
    ports:
      - "8001:8001"
    environment:
      - PORT=8001
      - AI_PROCESSING_SERVICE_URL=http://ai-processing:8002
    networks:
      - app-network
  
  ai-processing:
    build: ./services/ai-processing
    ports:
      - "8002:8002"
    environment:
      - PORT=8002
    networks:
      - app-network
  
  decision-simulation:
    build: ./services/decision-simulation
    ports:
      - "8003:8003"
    volumes:
      - chroma-data:/app/vector_stores
    environment:
      - PORT=8003
    networks:
      - app-network
  
  execution:
    build: ./services/execution
    ports:
      - "8004:8004"
    environment:
      - PORT=8004
    networks:
      - app-network

volumes:
  chroma-data:

networks:
  app-network:
    driver: bridge
```

**Cost:** **FREE** (AWS free tier for 12 months)

---

#### Option B: Multiple EC2 Instances (One Per Service)

**Architecture:**
```
EC2 t2.micro #1 → Request Management
EC2 t2.micro #2 → AI Processing
EC2 t2.micro #3 → Decision & Simulation
EC2 t2.micro #4 → Execution
```

**Pros:**
- ✅ Better isolation
- ✅ Independent scaling
- ✅ Better resource allocation

**Cons:**
- ❌ Need 4 instances (only 1 free for 12 months)
- ❌ More complex setup
- ❌ Higher cost after free tier

**Cost:** **FREE for 1 instance**, then ~$8.50/month per additional instance

---

### EC2 Setup Steps

1. **Launch EC2 Instance:**
   ```bash
   # Via AWS Console or CLI
   aws ec2 run-instances \
     --image-id ami-0c55b159cbfafe1f0 \
     --instance-type t2.micro \
     --key-name my-key \
     --security-group-ids sg-xxx
   ```

2. **SSH into instance:**
   ```bash
   ssh -i my-key.pem ubuntu@<ec2-ip>
   ```

3. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose python3-pip git
   sudo usermod -aG docker ubuntu
   newgrp docker
   ```

4. **Clone and deploy:**
   ```bash
   git clone <your-repo>
   cd Synergy_CMPE272
   docker-compose up -d
   ```

5. **Configure environment:**
   ```bash
   # Create .env files for each service
   # Set AWS credentials, API keys, etc.
   ```

6. **Set up reverse proxy (optional):**
   ```bash
   sudo apt install nginx
   # Configure nginx to route to services
   ```

---

## Multi-Platform Deployment Strategy ⭐ **RECOMMENDED**

### Why Deploy on Different Platforms?

**Benefits:**
- ✅ **Optimize costs** - Use free tiers efficiently
- ✅ **Best tool for each service** - Match platform to service needs
- ✅ **Reduce risk** - If one platform has issues, others continue
- ✅ **Leverage free tiers** - Maximize free resources

---

### Recommended Multi-Platform Strategy

#### Strategy 1: Hybrid Railway + EC2

**Services on Railway (Free):**
- ✅ **Request Management** → Railway ($1.25/month)
- ✅ **AI Processing** → Railway ($1.25/month)
- ✅ **Execution** → Railway ($0.50/month)

**Services on EC2 (Free for 12 months):**
- ✅ **Decision & Simulation** → EC2 (needs more resources, ChromaDB)

**Why:**
- Railway: Easy deployment for 3 services
- EC2: Better for resource-intensive service (RAG, ChromaDB)
- **Total Cost: FREE** (Railway $5 credit + EC2 free tier)

---

#### Strategy 2: All on EC2

**All 4 services on single EC2 instance:**
- ✅ **Simple** - One place to manage
- ✅ **Free for 12 months** - AWS free tier
- ✅ **Full control** - Can customize everything
- ✅ **ChromaDB works** - EBS volume for persistence

**Cost:** **FREE** (AWS free tier)

---

#### Strategy 3: Railway + Google Cloud Run

**Services on Railway:**
- ✅ **Request Management** → Railway
- ✅ **AI Processing** → Railway
- ✅ **Execution** → Railway

**Services on Cloud Run:**
- ✅ **Decision & Simulation** → Cloud Run (better resources, PostgreSQL with pgvector)

**Why:**
- Railway: Easy, free for 3 services
- Cloud Run: Better for RAG service, can use Cloud SQL (PostgreSQL with pgvector)
- **Total Cost: FREE** (within free tiers)

---

#### Strategy 4: All Different Platforms

**Request Management** → **Railway** ($1.25/month)
- Simple service, fits Railway free tier

**AI Processing** → **Render** (Free)
- ML models, can use Render's free tier

**Decision & Simulation** → **EC2** (Free for 12 months)
- Needs most resources, ChromaDB, best on EC2

**Execution** → **Railway** ($0.50/month)
- Simple service, fits Railway free tier

**Total Cost: FREE** (within free tiers)

---

## Comparison Table

| Platform | Free Tier | Best For | ChromaDB Support |
|----------|-----------|----------|------------------|
| **Railway** | $5/month | All services | PostgreSQL with pgvector ⭐ |
| **EC2** | 750 hrs/month | Resource-intensive | Native (EBS volume) ⭐ |
| **Render** | 750 hrs/month | Simple services | Limited (no persistent storage) |
| **Google Cloud Run** | 2M requests | Scalable services | Cloud SQL (pgvector) ⭐ |
| **Fly.io** | $5 one-time | Global distribution | Volumes available |

---

## Final Recommendations

### For Development/Testing:
**All on EC2 (single instance)**
- ✅ Free for 12 months
- ✅ Full control
- ✅ ChromaDB works natively
- ✅ Easy setup with docker-compose

### For Production (Free):
**Hybrid: Railway + EC2**
- ✅ Railway: 3 services (Request, AI, Execution)
- ✅ EC2: Decision & Simulation (with ChromaDB)
- ✅ **Total: FREE**

### For Production (Best Performance):
**All on EC2 with Auto Scaling**
- ✅ Better performance
- ✅ Full control
- ✅ Cost: ~$10-15/month after free tier

### For ChromaDB Alternative:
**PostgreSQL with pgvector** ⭐
- ✅ Free on Railway
- ✅ Better than ChromaDB for production
- ✅ Persistent, scalable
- ✅ Easy migration

---

## Migration Path

### Step 1: Choose Deployment Strategy
- Development: All on EC2
- Production: Hybrid Railway + EC2

### Step 2: Choose Vector Database
- **Option A**: Keep ChromaDB (use S3 sync or Railway volume)
- **Option B**: Migrate to PostgreSQL with pgvector (recommended)

### Step 3: Deploy Services
- Set up infrastructure
- Deploy each service
- Configure inter-service communication
- Test end-to-end

### Step 4: Monitor and Optimize
- Monitor costs
- Optimize resource usage
- Scale as needed

---

## Quick Start: EC2 Deployment

```bash
# 1. Launch EC2 instance (t2.micro, Ubuntu 22.04)
# 2. SSH into instance
ssh -i key.pem ubuntu@<ec2-ip>

# 3. Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
newgrp docker

# 4. Clone repo
git clone <your-repo>
cd Synergy_CMPE272

# 5. Create docker-compose.yml (see above)
# 6. Set environment variables
export GEMINI_API_KEY=xxx
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx

# 7. Deploy
docker-compose up -d

# 8. Check services
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

**That's it! All services running on EC2 for FREE (12 months).**

---

## Summary

1. **ChromaDB vs S3**: Can't replace ChromaDB with S3 (different purposes)
2. **Best Alternative**: PostgreSQL with pgvector (free, better for production)
3. **ChromaDB on Railway**: Use PostgreSQL with pgvector, or S3 sync, or Railway volume
4. **EC2 Deployment**: Best option for free, full control, ChromaDB works natively
5. **Multi-Platform**: Recommended - Use different platforms for different services to maximize free tiers

**My Recommendation:**
- **Development**: All on EC2 (free, easy)
- **Production**: Hybrid Railway + EC2 (free, optimized)
- **Vector DB**: Migrate to PostgreSQL with pgvector (free, better)

