# Local Testing Setup - Complete! ✅

I've created everything you need to test the microservices locally with end-to-end UI testing.

---

## 📁 Files Created

### 1. Docker Compose Configuration
**File:** `infrastructure/docker/docker-compose.microservices.yml`
- Configures all 4 microservices to run locally
- Sets up internal networking between services
- Mounts ChromaDB volume for persistence
- Maps ports: 8001, 8002, 8003, 8004

### 2. Local Testing Guide
**File:** `LOCAL_TESTING_GUIDE.md`
- Complete step-by-step instructions
- Troubleshooting section
- Testing checklist
- Service monitoring commands

### 3. Quick Start Guide
**File:** `QUICK_START_LOCAL_TESTING.md`
- Fast reference for common commands
- Minimal setup steps

### 4. Setup Script
**File:** `scripts/setup_local_testing.sh`
- Automates ChromaDB initialization
- Creates environment file templates
- Configures frontend automatically

---

## 🚀 Quick Start (3 Steps)

### Step 1: Run Setup Script
```bash
./scripts/setup_local_testing.sh
```

This will:
- Initialize ChromaDB (if needed)
- Create `.env` file template
- Configure frontend

### Step 2: Edit Environment Variables
```bash
nano infrastructure/docker/.env
```

Add your:
- AWS credentials
- Gemini API key
- DynamoDB table name
- SQS queue URL

### Step 3: Start Services
```bash
# Terminal 1: Start microservices
cd infrastructure/docker
docker-compose -f docker-compose.microservices.yml up -d

# Terminal 2: Start frontend
cd frontend
npm run dev
```

**Open:** `http://localhost:5173` in your browser

---

## 🧪 Testing Flow

1. **Submit Request from UI**
   - Enter resident ID and message
   - Click "Submit Request"
   - Watch classification happen in real-time

2. **View Options**
   - See 3-4 resolution options
   - Each with cost, time, reasoning
   - Source document IDs (RAG working)

3. **Select Option**
   - Click on an option
   - Execution is triggered
   - Status updates to "In Progress"

4. **View History**
   - Check request history
   - See all submitted requests

---

## 📊 Service Architecture (Local)

```
┌─────────────────────────────────────────────────┐
│              Frontend (Port 5173)                │
│              http://localhost:5173               │
└──────────────────┬──────────────────────────────┘
                   │ HTTP
                   ▼
┌─────────────────────────────────────────────────┐
│   Request Management (Port 8001)                 │
│   http://localhost:8001                          │
└───┬──────────┬──────────────┬───────────────────┘
    │          │              │
    │ HTTP     │ HTTP         │ HTTP
    ▼          ▼              ▼
┌─────────┐ ┌──────────────┐ ┌──────────────┐
│ AI      │ │ Decision &   │ │ Execution    │
│ Process │ │ Simulation   │ │ Service      │
│ (8002)  │ │ (8003)       │ │ (8004)       │
└─────────┘ └──────────────┘ └──────────────┘
```

---

## 🔍 Monitoring

### View All Logs
```bash
cd infrastructure/docker
docker-compose -f docker-compose.microservices.yml logs -f
```

### View Specific Service
```bash
docker-compose -f docker-compose.microservices.yml logs -f request-management
```

### Check Service Health
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

---

## 🐛 Common Issues & Fixes

### Issue: "ChromaDB collection not found"
**Fix:**
```bash
cd backend
source venv/bin/activate
python kb/ingest_documents.py
cp -r vector_stores/chroma_db ../services/decision-simulation/vector_stores/
```

### Issue: "Connection refused" between services
**Fix:** Services use internal Docker network names:
- `http://ai-processing:8002` (not localhost)
- `http://decision-simulation:8003`
- `http://execution:8004`

### Issue: Frontend can't connect
**Fix:** Make sure `frontend/.env.local` has:
```
VITE_API_BASE_URL=http://localhost:8001
```

### Issue: Port already in use
**Fix:**
```bash
# Find what's using the port
lsof -i :8001

# Stop it or change port in docker-compose file
```

---

## ✅ Testing Checklist

- [ ] All 4 services start successfully
- [ ] All health endpoints return "healthy"
- [ ] Frontend loads at http://localhost:5173
- [ ] Can submit a request from UI
- [ ] Classification works (category, urgency shown)
- [ ] Risk prediction works
- [ ] Simulation generates 3-4 options
- [ ] Options have source_doc_ids (RAG working)
- [ ] Can select an option
- [ ] Execution is triggered
- [ ] Request history works
- [ ] Service logs show proper communication

---

## 📚 Documentation

- **Detailed Guide:** [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)
- **Quick Reference:** [QUICK_START_LOCAL_TESTING.md](QUICK_START_LOCAL_TESTING.md)
- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 🎯 Next Steps

After local testing passes:

1. **Fix any issues** found during testing
2. **Deploy to Railway/EC2** - Follow `DEPLOYMENT_GUIDE.md`
3. **Update frontend** to point to deployed services
4. **Test in production**

---

## 💡 Tips

1. **Keep logs open** in a separate terminal to see what's happening
2. **Test different scenarios** - maintenance, billing, security, etc.
3. **Check browser console** (F12) for frontend errors
4. **Verify DynamoDB** - Check that requests are being stored
5. **Test error cases** - Stop a service and see error handling

---

**You're all set! Start testing with: `./scripts/setup_local_testing.sh`**

