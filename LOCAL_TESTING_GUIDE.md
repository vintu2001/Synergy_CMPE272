# Local Testing Guide
## End-to-End Testing with Microservices

This guide walks you through testing all 4 microservices locally and performing end-to-end testing from the UI.

---

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Node.js** (for frontend)
3. **AWS Credentials** configured (for DynamoDB/SQS)
4. **Gemini API Key** (for AI services)
5. **ChromaDB initialized** (knowledge base ingested)

---

## Step 1: Initialize ChromaDB (First Time Only)

Before starting services, you need to initialize the ChromaDB vector store:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Ingest knowledge base documents
python kb/ingest_documents.py

# This creates vector_stores/chroma_db directory
# Copy it to decision-simulation service
cp -r vector_stores/chroma_db ../services/decision-simulation/vector_stores/
```

**Note:** If you already have ChromaDB initialized, skip this step.

---

## Step 2: Set Up Environment Variables

Create a `.env` file in `infrastructure/docker/`:

```bash
cd infrastructure/docker
nano .env
```

Add the following:

```env
# AWS Configuration
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DYNAMODB_TABLE_NAME=aam_requests
AWS_SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/123456789/request-queue

# Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Admin API Key
ADMIN_API_KEY=test-admin-key
```

**Save the file** (Ctrl+X, then Y, then Enter in nano)

---

## Step 3: Start All Microservices

```bash
# From infrastructure/docker directory
cd infrastructure/docker

# Start all services
docker-compose -f docker-compose.microservices.yml up -d

# Check if all services are running
docker-compose -f docker-compose.microservices.yml ps

# View logs (optional, to see what's happening)
docker-compose -f docker-compose.microservices.yml logs -f
```

**Expected Output:**
```
NAME                          STATUS
request-management-service   Up
ai-processing-service        Up
decision-simulation-service  Up
execution-service            Up
```

---

## Step 4: Verify Services Are Running

Test each service's health endpoint:

```bash
# Request Management Service
curl http://localhost:8001/health

# AI Processing Service
curl http://localhost:8002/health

# Decision & Simulation Service
curl http://localhost:8003/health

# Execution Service
curl http://localhost:8004/health
```

**Expected Response for each:**
```json
{
  "status": "healthy",
  "service": "Service Name"
}
```

---

## Step 5: Update Frontend Configuration

Update the frontend to point to the Request Management Service:

### Option 1: Environment Variable (Recommended)

Create/update `frontend/.env.local`:

```bash
cd frontend
nano .env.local
```

Add:
```env
VITE_API_BASE_URL=http://localhost:8001
```

### Option 2: Update api.js Directly

Edit `frontend/src/services/api.js`:

```javascript
// Change this line:
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";
```

**Note:** The frontend should now call `http://localhost:8001` which is the Request Management Service.

---

## Step 6: Start Frontend

```bash
# From frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

The frontend should start on `http://localhost:5173` (or another port if 5173 is taken).

---

## Step 7: End-to-End Testing from UI

### Test 1: Submit a Request

1. **Open the frontend** in your browser: `http://localhost:5173`

2. **Navigate to Resident Submission page**

3. **Enter a test request:**
   - **Resident ID:** `RES_Building123_1001`
   - **Message:** `My AC is broken and it's very hot outside. This is an emergency!`

4. **Click "Submit Request"**

5. **Expected Behavior:**
   - Button shows "Classifying issue..." while processing
   - After a few seconds, you should see:
     - Classification results (Category: Maintenance, Urgency: High)
     - Risk assessment
     - 3-4 resolution options with:
       - Action descriptions
       - Estimated cost and time
       - Reasoning
       - Source document IDs (RAG working)

6. **Check Browser Console** (F12) for any errors

7. **Check Service Logs:**
   ```bash
   # View logs from all services
   docker-compose -f docker-compose.microservices.yml logs -f
   
   # Or view specific service logs
   docker-compose -f docker-compose.microservices.yml logs -f request-management
   ```

### Test 2: Select an Option

1. **After options are displayed**, click on one of the options

2. **Expected Behavior:**
   - Option is selected
   - Execution is triggered
   - Success message is shown
   - Request status updates to "In Progress"

3. **Check logs** to verify execution service was called:
   ```bash
   docker-compose -f docker-compose.microservices.yml logs execution
   ```

### Test 3: View Request History

1. **Navigate to Request History page**

2. **Enter Resident ID:** `RES_Building123_1001`

3. **Click "Get Requests"**

4. **Expected Behavior:**
   - List of requests for that resident
   - Shows all submitted requests with their status

### Test 4: Test Different Scenarios

Try different message types:

**Maintenance (High Urgency):**
```
My AC is broken and it's 95°F outside. This is an emergency!
```

**Billing Question:**
```
How do I pay my rent online?
```

**Security Issue:**
```
I lost my apartment key. Can I get a replacement?
```

**Delivery Question:**
```
Where is my package? It was supposed to arrive yesterday.
```

**Amenities Question:**
```
What are the pool hours?
```

---

## Step 8: Monitor Service Communication

Watch the logs to see service-to-service communication:

```bash
# Watch all services
docker-compose -f docker-compose.microservices.yml logs -f

# Watch specific service
docker-compose -f docker-compose.microservices.yml logs -f request-management
```

**What to Look For:**
- Request Management → AI Processing (classification, risk prediction)
- Request Management → Decision & Simulation (simulation, decision)
- Request Management → Execution (when option is selected)
- No connection errors or timeouts

---

## Step 9: Test Error Scenarios

### Test LLM Failure Handling

1. **Temporarily break Gemini API:**
   ```bash
   # Stop AI Processing service
   docker-compose -f docker-compose.microservices.yml stop ai-processing
   ```

2. **Submit a request from UI**

3. **Expected Behavior:**
   - Error message displayed
   - "Escalate to Human Support" button appears
   - Request still created in database

4. **Restart service:**
   ```bash
   docker-compose -f docker-compose.microservices.yml start ai-processing
   ```

### Test Service Unavailability

1. **Stop Decision & Simulation service:**
   ```bash
   docker-compose -f docker-compose.microservices.yml stop decision-simulation
   ```

2. **Submit a request**

3. **Expected:** Error handling, graceful degradation

---

## Step 10: Verify Database

Check that requests are being stored in DynamoDB:

```bash
# Using AWS CLI (if installed)
aws dynamodb scan --table-name aam_requests --region us-west-2

# Or check from AWS Console
# Go to DynamoDB → Tables → aam_requests → Items
```

---

## Troubleshooting

### Issue: Services won't start

**Check:**
```bash
# Check Docker logs
docker-compose -f docker-compose.microservices.yml logs

# Check if ports are already in use
lsof -i :8001
lsof -i :8002
lsof -i :8003
lsof -i :8004
```

**Fix:**
- Stop any services using those ports
- Or change ports in docker-compose file

### Issue: ChromaDB not found

**Error:** `ChromaDB collection not found`

**Fix:**
```bash
# Make sure ChromaDB is initialized
cd backend
python kb/ingest_documents.py

# Copy to decision-simulation
cp -r vector_stores/chroma_db ../services/decision-simulation/vector_stores/
```

### Issue: Service-to-service communication failing

**Error:** `Connection refused` or `Service unavailable`

**Check:**
```bash
# Verify services are running
docker-compose -f docker-compose.microservices.yml ps

# Check service URLs in request-management
docker-compose -f docker-compose.microservices.yml exec request-management env | grep SERVICE_URL
```

**Fix:**
- Services use internal Docker network names
- URLs should be: `http://ai-processing:8002`, `http://decision-simulation:8003`, etc.
- Not `localhost` (that's only for external access)

### Issue: Frontend can't connect

**Error:** `CORS error` or `Network error`

**Fix:**
- Make sure frontend points to `http://localhost:8001`
- Check CORS is enabled in Request Management service (it should be)
- Check browser console for specific error

### Issue: Classification not working

**Error:** `GEMINI_API_KEY not found`

**Fix:**
- Check `.env` file has `GEMINI_API_KEY`
- Restart services after adding environment variable:
  ```bash
  docker-compose -f docker-compose.microservices.yml down
  docker-compose -f docker-compose.microservices.yml up -d
  ```

---

## Quick Commands Reference

```bash
# Start all services
cd infrastructure/docker
docker-compose -f docker-compose.microservices.yml up -d

# Stop all services
docker-compose -f docker-compose.microservices.yml down

# View logs
docker-compose -f docker-compose.microservices.yml logs -f

# Restart a specific service
docker-compose -f docker-compose.microservices.yml restart request-management

# Rebuild services (after code changes)
docker-compose -f docker-compose.microservices.yml up -d --build

# Check service status
docker-compose -f docker-compose.microservices.yml ps

# Test health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

---

## Testing Checklist

Use this checklist to verify everything works:

- [ ] All 4 services start successfully
- [ ] All health endpoints return "healthy"
- [ ] Frontend loads and connects to Request Management service
- [ ] Can submit a request from UI
- [ ] Classification works (category, urgency, intent)
- [ ] Risk prediction works
- [ ] Simulation generates 3-4 options
- [ ] Options have source_doc_ids (RAG working)
- [ ] Can select an option
- [ ] Execution is triggered
- [ ] Request history works
- [ ] Requests are stored in DynamoDB
- [ ] Service logs show proper communication
- [ ] Error handling works (test with service down)

---

## Next Steps

After local testing passes:

1. **Deploy to Railway/EC2** - Follow `DEPLOYMENT_GUIDE.md`
2. **Update frontend** to point to deployed services
3. **Test in production environment**

---

## Support

If you encounter issues:

1. Check service logs: `docker-compose logs -f <service-name>`
2. Verify environment variables are set
3. Check service health endpoints
4. Review this guide's troubleshooting section
5. Check browser console for frontend errors

