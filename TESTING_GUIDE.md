# Testing Guide
## How to Test Microservices Deployment

This guide provides step-by-step instructions to verify that all services are working correctly.

---

## Prerequisites

- All 4 services deployed (3 on Railway, 1 on EC2)
- Service URLs noted down
- curl or Postman installed
- Frontend configured (optional)

---

## Test 1: Health Checks

### Purpose
Verify all services are running and accessible.

### Steps

**1. Request Management Service (Railway):**
```bash
curl https://request-management-service.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Request Management Service"
}
```

**2. AI Processing Service (Railway):**
```bash
curl https://ai-processing-service.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "AI Processing Service"
}
```

**3. Decision & Simulation Service (EC2):**
```bash
curl http://<ec2-ip>:8003/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Decision & Simulation Service"
}
```

**4. Execution Service (Railway):**
```bash
curl https://execution-service.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Execution Service"
}
```

### ✅ Success Criteria
- All 4 services return `{"status": "healthy"}`

### ❌ Troubleshooting
- **Service not responding:** Check Railway dashboard / EC2 instance status
- **Connection refused:** Check security groups (EC2) or service status (Railway)
- **Timeout:** Check service URLs are correct

---

## Test 2: Direct Service Testing

### Purpose
Test each service independently to verify core functionality.

### 2.1 Test AI Processing - Classification

**Request:**
```bash
curl -X POST https://ai-processing-service.up.railway.app/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "RES_Building123_1001",
    "message_text": "My AC is broken and it'\''s very hot outside"
  }'
```

**Expected Response:**
```json
{
  "category": "Maintenance",
  "urgency": "High",
  "intent": "solve_problem",
  "confidence": 0.85
}
```

**✅ Success Criteria:**
- Returns category, urgency, intent, confidence
- Category is one of: Maintenance, Billing, Security, Deliveries, Amenities
- Urgency is one of: High, Medium, Low
- Confidence is between 0 and 1

### 2.2 Test AI Processing - Risk Prediction

**Request:**
```bash
curl -X POST https://ai-processing-service.up.railway.app/api/v1/predict-risk \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Maintenance",
    "urgency": "High",
    "intent": "solve_problem",
    "message_text": "AC is broken"
  }'
```

**Expected Response:**
```json
{
  "risk_forecast": 0.75,
  "risk_level": "High"
}
```

**✅ Success Criteria:**
- Returns risk_forecast (0-1)
- Returns risk_level (High/Medium/Low)

### 2.3 Test Decision & Simulation - Generate Options

**Request:**
```bash
curl -X POST http://<ec2-ip>:8003/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Maintenance",
    "urgency": "High",
    "message_text": "AC is broken and it'\''s very hot",
    "resident_id": "RES_Building123_1001",
    "risk_score": 0.75
  }'
```

**Expected Response:**
```json
{
  "options": [
    {
      "option_id": "opt_1",
      "action": "Dispatch emergency HVAC technician",
      "estimated_cost": 250.0,
      "estimated_time": 4.0,
      "reasoning": "...",
      "source_doc_ids": ["policy_maintenance_1.0", "sop_hvac_1.0"]
    },
    ...
  ],
  "issue_id": "agentic_Maintenance_High_RES_Building123_1001"
}
```

**✅ Success Criteria:**
- Returns 3-4 options
- Each option has: option_id, action, estimated_cost, estimated_time
- Options have source_doc_ids (RAG working)
- Options are relevant to the issue

### 2.4 Test Decision & Simulation - Make Decision

**Request:**
```bash
curl -X POST http://<ec2-ip>:8003/api/v1/decide \
  -H "Content-Type: application/json" \
  -d '{
    "classification": {
      "category": "Maintenance",
      "urgency": "High",
      "intent": "solve_problem",
      "confidence": 0.85
    },
    "simulation": {
      "options": [
        {
          "option_id": "opt_1",
          "action": "Dispatch emergency HVAC technician",
          "estimated_cost": 250.0,
          "estimated_time": 4.0
        }
      ]
    }
  }'
```

**Expected Response:**
```json
{
  "chosen_action": "Dispatch emergency HVAC technician",
  "chosen_option_id": "opt_1",
  "reasoning": "High urgency maintenance issue requires immediate response...",
  "alternatives_considered": ["opt_2", "opt_3"],
  "policy_scores": {"opt_1": 0.85, "opt_2": 0.72, "opt_3": 0.60}
}
```

**✅ Success Criteria:**
- Returns chosen_action and chosen_option_id
- Returns reasoning
- Returns alternatives_considered
- Returns policy_scores

---

## Test 3: End-to-End Request Flow

### Purpose
Test the complete flow from request submission to option generation.

### Steps

**1. Submit a Request:**
```bash
curl -X POST https://request-management-service.up.railway.app/api/v1/submit-request \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "RES_Building123_1001",
    "message_text": "My AC is broken and it'\''s 95°F outside. This is an emergency!"
  }'
```

**Expected Response:**
```json
{
  "status": "submitted",
  "message": "Request submitted successfully!",
  "request_id": "REQ_20241109123456_ABC123",
  "classification": {
    "category": "Maintenance",
    "urgency": "High",
    "intent": "solve_problem",
    "confidence": 0.88
  },
  "simulation": {
    "options": [
      {
        "option_id": "opt_1",
        "action": "Dispatch emergency HVAC technician",
        "estimated_cost": 250.0,
        "estimated_time": 4.0,
        "source_doc_ids": ["policy_maintenance_1.0"]
      },
      ...
    ],
    "recommended_option_id": "opt_1"
  }
}
```

**✅ Success Criteria:**
- Request is created successfully
- Classification is performed (category, urgency, intent)
- Risk prediction is performed
- Simulation generates 3-4 options
- Options have source_doc_ids (RAG working)
- Recommended option is provided

**2. Verify Request in Database:**
```bash
curl -X GET https://request-management-service.up.railway.app/api/v1/requests/REQ_20241109123456_ABC123 \
  -H "X-API-Key: <admin-api-key>"
```

**Expected Response:**
```json
{
  "request_id": "REQ_20241109123456_ABC123",
  "resident_id": "RES_Building123_1001",
  "message_text": "My AC is broken...",
  "category": "Maintenance",
  "urgency": "High",
  "status": "SUBMITTED",
  "created_at": "2024-11-09T12:34:56Z"
}
```

**✅ Success Criteria:**
- Request is stored in DynamoDB
- All fields are correct
- Status is SUBMITTED

**3. Select an Option:**
```bash
curl -X POST https://request-management-service.up.railway.app/api/v1/requests/REQ_20241109123456_ABC123/select-option \
  -H "Content-Type: application/json" \
  -d '{
    "selected_option_id": "opt_1"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Option selected and execution initiated",
  "request_id": "REQ_20241109123456_ABC123",
  "selected_option": {
    "option_id": "opt_1",
    "action": "Dispatch emergency HVAC technician"
  }
}
```

**✅ Success Criteria:**
- Option is selected successfully
- Request status updates to IN_PROGRESS
- Execution is triggered

---

## Test 4: Service-to-Service Communication

### Purpose
Verify services can communicate with each other correctly.

### Steps

**1. Check Request Management → AI Processing:**
- Submit a request
- Check Railway logs for Request Management service
- Should see HTTP calls to AI Processing service
- Should see successful responses

**2. Check Request Management → Decision & Simulation:**
- Submit a request
- Check Railway logs for Request Management service
- Should see HTTP calls to Decision & Simulation service (EC2)
- Should see successful responses

**3. Check Request Management → Execution:**
- Select an option
- Check Railway logs for Request Management service
- Should see HTTP calls to Execution service
- Should see successful responses

**✅ Success Criteria:**
- All inter-service calls succeed
- No connection errors
- No timeout errors
- Services respond within reasonable time (< 5 seconds)

---

## Test 5: Error Handling

### Purpose
Verify services handle errors gracefully.

### Steps

**1. Test Invalid Request:**
```bash
curl -X POST https://request-management-service.up.railway.app/api/v1/submit-request \
  -H "Content-Type: application/json" \
  -d '{
    "resident_id": "",
    "message_text": "short"
  }'
```

**Expected Response:**
```json
{
  "detail": "Validation error: message_text must be at least 10 characters"
}
```

**✅ Success Criteria:**
- Returns appropriate error message
- Status code 422 (Unprocessable Entity)

**2. Test Service Unavailable:**
- Temporarily stop Decision & Simulation service
- Submit a request
- Should handle gracefully (timeout or fallback)

**✅ Success Criteria:**
- Request Management handles service unavailability
- Returns appropriate error message
- Doesn't crash

---

## Test 6: Performance Testing

### Purpose
Verify services perform within acceptable limits.

### Steps

**1. Measure Response Times:**
```bash
# Time classification
time curl -X POST https://ai-processing-service.up.railway.app/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"resident_id": "RES_1001", "message_text": "AC is broken"}'

# Time simulation
time curl -X POST http://<ec2-ip>:8003/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"category": "Maintenance", "urgency": "High", "message_text": "AC broken", "resident_id": "RES_1001"}'
```

**✅ Success Criteria:**
- Classification: < 2 seconds
- Risk Prediction: < 1 second
- Simulation: < 5 seconds
- Decision: < 2 seconds
- End-to-end: < 10 seconds

**2. Load Testing (Optional):**
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test 100 requests
ab -n 100 -c 10 https://request-management-service.up.railway.app/health
```

**✅ Success Criteria:**
- All requests succeed
- Average response time < 500ms
- No errors

---

## Test 7: Frontend Integration

### Purpose
Verify frontend can communicate with deployed services.

### Steps

**1. Update Frontend API URL:**
```javascript
// frontend/src/services/api.js
const API_BASE_URL = 'https://request-management-service.up.railway.app';
```

**2. Test from Frontend:**
- Open frontend application
- Submit a request
- Verify it goes through all services
- Check options are displayed
- Select an option
- Verify execution

**✅ Success Criteria:**
- Frontend can submit requests
- Options are displayed correctly
- Selection works
- No CORS errors

---

## Test 8: Monitoring and Logs

### Purpose
Verify monitoring and logging are working.

### Steps

**1. Check Railway Logs:**
- Go to Railway dashboard
- Select each service
- View logs
- Check for errors

**2. Check EC2 Logs:**
```bash
ssh -i key.pem ubuntu@<ec2-ip>
cd infrastructure/ec2
docker-compose logs -f decision-simulation
```

**✅ Success Criteria:**
- Logs are accessible
- No critical errors
- Requests are logged
- Service-to-service calls are logged

---

## Test Checklist

Use this checklist to verify everything is working:

- [ ] All 4 services return healthy status
- [ ] AI Processing can classify messages
- [ ] AI Processing can predict risk
- [ ] Decision & Simulation can generate options
- [ ] Decision & Simulation can make decisions
- [ ] RAG retrieval is working (source_doc_ids present)
- [ ] End-to-end request flow works
- [ ] Requests are stored in DynamoDB
- [ ] Option selection works
- [ ] Service-to-service communication works
- [ ] Error handling works
- [ ] Performance is acceptable
- [ ] Frontend integration works
- [ ] Logs are accessible
- [ ] No critical errors

---

## Common Issues and Solutions

### Issue: Service returns 502 Bad Gateway

**Possible Causes:**
- Service is not running
- Service crashed
- Port mismatch

**Solutions:**
- Check Railway dashboard / EC2 status
- Check service logs
- Verify PORT environment variable

### Issue: Service-to-service communication fails

**Possible Causes:**
- Incorrect service URLs
- Network connectivity issues
- CORS issues

**Solutions:**
- Verify environment variables (service URLs)
- Test service URLs directly with curl
- Check security groups (EC2)
- Verify CORS configuration

### Issue: ChromaDB not working

**Possible Causes:**
- ChromaDB data not initialized
- Volume not mounted
- Permissions issue

**Solutions:**
- Initialize ChromaDB: `python kb/ingest_documents.py`
- Check volume mount: `docker volume ls`
- Check permissions: `docker exec -it decision-simulation-service ls -la /app/vector_stores`

### Issue: Slow response times

**Possible Causes:**
- Cold starts (Railway)
- Resource constraints
- Network latency

**Solutions:**
- Wait for services to warm up
- Check Railway metrics (CPU, memory)
- Consider upgrading EC2 instance type

---

## Next Steps

After all tests pass:

1. **Set up monitoring alerts**
2. **Configure custom domains** (optional)
3. **Set up CI/CD** (optional)
4. **Document service URLs** for team
5. **Set up backup strategy** for ChromaDB

---

## Support

If tests fail:
1. Check service logs
2. Verify environment variables
3. Test services individually
4. Review DEPLOYMENT_GUIDE.md
5. Check troubleshooting section

