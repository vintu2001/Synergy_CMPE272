# Rebuild Docker Commands

## Quick Rebuild (After Fixes)

```bash
cd infrastructure/docker

# Stop all services
docker-compose -f docker-compose.microservices.yml down

# Rebuild all services (no cache to ensure fresh dependencies)
docker-compose -f docker-compose.microservices.yml build --no-cache

# Start services
docker-compose -f docker-compose.microservices.yml up -d

# Watch logs
docker-compose -f docker-compose.microservices.yml logs -f
```

## Verify Services

```bash
# Check all services are running
docker-compose -f docker-compose.microservices.yml ps

# Test health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

## Expected Status

All services should show:
- **Status:** `Up` (not "Restarting")
- **Health:** `healthy` (if healthcheck configured)

## If Services Still Fail

Check specific service logs:
```bash
docker-compose -f docker-compose.microservices.yml logs ai-processing
docker-compose -f docker-compose.microservices.yml logs decision-simulation
```

## Fixes Applied

1. ✅ Added `pandas` to AI Processing requirements
2. ✅ Removed database dependencies from Decision & Simulation
3. ✅ Added `simpy` and `boto3` to Decision & Simulation requirements
4. ✅ Copied `utils/` directory to Decision & Simulation

All import errors should be resolved!

